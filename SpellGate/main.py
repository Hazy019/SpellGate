import os
import sys
import threading
from pathlib import Path
import json

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QGraphicsDropShadowEffect, QInputDialog, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QRect, QSequentialAnimationGroup, QPauseAnimation, QVariantAnimation, QAbstractAnimation
from PyQt6.QtGui import QFont, QFontDatabase, QShortcut, QKeySequence, QIcon, QColor

from modules.kiosk_manager import KioskManager
from modules.ui_scenes import MemorizationScene, RecallScene, ScrambledPhase, SummaryScene
from modules.loading_scene import LoadingScene
from modules.login_scene import LoginScene

from modules.config import TIME_BANK_FILE, USER_PROGRESS_FILE
from modules.game_logic import load_progress
from modules.startup_manager import install_to_startup
from modules.security import secure_save_time, secure_load_time, get_local_pin
from modules.firebase_sync import (
    init_firebase, fetch_parent_pin, start_force_unlock_listener,
    stop_force_unlock_listener
)

# ── Watchdog: internal daemon thread (no subprocess, no CMD window) ──
from watchdog import WatchdogThread


# ─────────────────────────────────────────────────────────────
#  GLASSY FLOATING TIMER (shown during playtime)
#
#  Security design:
#  - Frameless → no visible X button
#  - Alt+F4 blocked → kid can't keyboard-close it
#  - Right-click → PIN dialog (parent can close with PIN)
#  - Closing without PIN → re-locks the PC immediately
#  - Time runs out → PC re-locks (returns to spelling game)
#  - Saves time every second so no time is "lost" on crash
# ─────────────────────────────────────────────────────────────

class GlassyTimer(QWidget):

    def __init__(self, parent_pin: str | None = None, on_relock=None):
        """
        parent_pin  — the PIN needed to close the timer early.
        on_relock   — callback that re-shows the kiosk (called when time
                      runs out or parent closes the timer with PIN).
        """
        super().__init__()
        self._parent_pin = parent_pin
        self._on_relock  = on_relock   # callable: re-shows main kiosk window
        self._closing    = False       # prevents re-entrant close logic

        font_id = QFontDatabase.addApplicationFont("assets/PressStart2P-Regular.ttf")
        font_family = (
            QFontDatabase.applicationFontFamilies(font_id)[0]
            if font_id != -1 else "Arial"
        )

        # ── Window flags ──────────────────────────────────────
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint       # no X button
            | Qt.WindowType.WindowStaysOnTopHint    # always on top
            | Qt.WindowType.Tool                    # hides from taskbar
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(0.92)

        # ── Layout ───────────────────────────────────────────
        self.container = QWidget(self)
        self.container.setObjectName("TimerContainer")
        self.container.setStyleSheet("""
            QWidget#TimerContainer {
                background-color: rgba(10, 15, 35, 220);
                border-radius: 20px;
                border: 2px solid #38BDF8;
            }
        """)

        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(24)
        self.shadow.setColor(QColor(56, 189, 248, 160))
        self.container.setGraphicsEffect(self.shadow)

        inner = QVBoxLayout(self.container)
        inner.setContentsMargins(12, 8, 12, 8)

        self.label = QLabel("00:00:00", self)
        self.label.setFont(QFont(font_family, 22))
        self.label.setStyleSheet("color: #38BDF8; padding: 6px;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Hint text — tells parent how to close
        self.hint = QLabel("Right-click to close", self)
        self.hint.setFont(QFont("Arial", 7))
        self.hint.setStyleSheet("color: rgba(56,189,248,100); padding: 0 6px 4px 6px;")
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        inner.addWidget(self.label)
        inner.addWidget(self.hint)

        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.container)
        self.setLayout(outer)
        self.setGeometry(100, 100, 230, 110)

        # ── Timer logic ───────────────────────────────────────
        self.time_left = self._load_time()
        self._tick_timer = QTimer(self)
        self._tick_timer.timeout.connect(self._update_time)
        self._tick_timer.start(1000)

    # ── Drag to move ──────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def contextMenuEvent(self, event):
        """Right-click → ask for parent PIN to close the timer."""
        self._ask_pin_to_close()
        event.accept()

    # ── Block all close attempts ──────────────────────────────

    def closeEvent(self, event):
        """
        Any close attempt (Alt+F4, system, etc.) that wasn't explicitly
        authorised goes through PIN verification first.
        If no PIN is set, we still block the close — re-lock instead.
        """
        if self._closing:
            # Authorised close — let Qt finish
            event.accept()
            return
        # Block and ask for PIN
        event.ignore()
        self._ask_pin_to_close()

    def keyPressEvent(self, event):
        """Block Alt+F4 and other close-related keys."""
        blocked = {
            Qt.Key.Key_F4,      # Alt+F4
            Qt.Key.Key_F,       # just in case
            Qt.Key.Key_Escape,
        }
        if event.key() in blocked:
            event.ignore()
            return
        super().keyPressEvent(event)

    # ── PIN verification ──────────────────────────────────────

    def _ask_pin_to_close(self):
        """Show PIN dialog. If correct → close and re-lock."""
        from modules.security import get_local_pin
        active_pin = self._parent_pin or get_local_pin()

        if not active_pin:
            # No PIN configured — show info message, don't close
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self, "SpellGate",
                "No PIN is configured yet.\n\n"
                "Set a PIN in the Parent Dashboard at spellgate.web.app\n"
                "to be able to close this timer early."
            )
            return

        pin, ok = QInputDialog.getText(
            self, "Close Timer", "Enter parent PIN:",
            QLineEdit.EchoMode.Password
        )
        if ok and pin == active_pin:
            self._authorised_close()
        elif ok:
            # Wrong PIN — flash red briefly
            self.label.setStyleSheet("color: #ff4444; padding: 6px;")
            QTimer.singleShot(
                800,
                lambda: self.label.setStyleSheet("color: #38BDF8; padding: 6px;")
            )

    def _authorised_close(self):
        """Close the timer and re-lock the PC."""
        self._closing = True
        self._tick_timer.stop()
        # Save whatever time is left so it's not lost
        secure_save_time(self.time_left, TIME_BANK_FILE)
        self.close()
        # Re-activate kiosk so the kid goes back to the spelling game
        if self._on_relock:
            QTimer.singleShot(300, self._on_relock)

    # ── Countdown logic ───────────────────────────────────────

    def _load_time(self):
        return secure_load_time(TIME_BANK_FILE)

    def _update_time(self):
        if self.time_left > 0:
            self.time_left -= 1
            hrs, remainder = divmod(self.time_left, 3600)
            mins, secs = divmod(remainder, 60)
            self.label.setText(f"{hrs:02d}:{mins:02d}:{secs:02d}")

            # Change colour when under 5 minutes
            if self.time_left <= 300:
                self.label.setStyleSheet("color: #ffc857; padding: 6px;")
            # Change colour when under 1 minute
            if self.time_left <= 60:
                self.label.setStyleSheet("color: #ff6b6b; padding: 6px;")

            # Save every second (no time lost on crash)
            secure_save_time(self.time_left, TIME_BANK_FILE)
        else:
            # Time's up — re-lock immediately
            self._tick_timer.stop()
            secure_save_time(0, TIME_BANK_FILE)
            self.label.setText("TIME UP!")
            self.label.setStyleSheet("color: #ff4444; padding: 6px;")
            self.hint.setText("Locking PC...")
            # Re-lock after a 2-second "TIME UP" display
            QTimer.singleShot(2000, self._authorised_close)




# ─────────────────────────────────────────────────────────────
#  MAIN WINDOW
# ─────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SpellGate Lock")
        self.setStyleSheet("QMainWindow { background-color: #0a0a0a; }")

        # ── Background music ─────────────────────────────────
        try:
            import winsound
            bgm_path = os.path.abspath(r"assets\bgm.wav")
            if os.path.exists(bgm_path):
                winsound.PlaySound(
                    bgm_path,
                    winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP
                )
        except Exception as e:
            print("Could not start background music:", e)

        # ── Persistence (startup on boot) ────────────────────
        install_to_startup()

        # ── Internal watchdog thread ──────────────────────────
        # Replaces the old subprocess.Popen(watchdog.py) approach.
        # No separate process, no CMD window, nothing the kid can kill.
        self._watchdog = WatchdogThread()
        self._watchdog.start()

        # Heartbeat timer — pings the watchdog every second so it
        # knows the UI is still responsive.
        self._heartbeat_timer = QTimer(self)
        self._heartbeat_timer.timeout.connect(self._watchdog.tick)
        self._heartbeat_timer.start(1000)

        # ── Firebase init & PIN loading ──────────────────────
        # Runs on background thread so it never blocks the UI.
        self._parent_pin: str | None = None
        threading.Thread(target=self._init_firebase_and_pin, daemon=True).start()

        # ── Data directories ─────────────────────────────────
        os.makedirs(os.path.dirname(TIME_BANK_FILE), exist_ok=True)
        if not os.path.exists(TIME_BANK_FILE):
            secure_save_time(0, TIME_BANK_FILE)

        progress_data = load_progress(USER_PROGRESS_FILE)
        self.current_avatar = progress_data.get("spaceship", None)
        if self.current_avatar:
            self.current_avatar_selected = True
        else:
            self.current_avatar = "Interceptor"

        # ── Kiosk mode ───────────────────────────────────────
        self.kiosk = KioskManager(self)
        self.kiosk.enable_kiosk_mode()

        # ── Parent override & ESC shortcuts ───────────────────
        self.exit_shortcut = QShortcut(QKeySequence("Ctrl+Shift+P"), self)
        self.exit_shortcut.activated.connect(self.emergency_exit)

        self.esc_shortcut = QShortcut(QKeySequence("Esc"), self)
        self.esc_shortcut.activated.connect(self.handle_esc_pressed)

        self.showFullScreen()
        self.setContentsMargins(0, 0, 0, 0)
        self.setWindowIcon(QIcon("assets/icons/logo.png"))

        # Start with Loading screen while we check Firebase
        self.show_loading_screen()

    # ── Firebase + PIN init (background) ─────────────────────

    def _init_firebase_and_pin(self):
        """
        Runs on a background thread.
        1. Initialises Firebase (checks refresh token).
        2. If no valid token, shows Login Screen.
        3. If valid, fetches parent PIN from Firestore and caches it.
        4. Starts the real-time force-unlock listener.
        """
        try:
            connected = init_firebase()
            if not connected:
                # Need to login - switch to main thread for UI
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(0, self.show_login_screen)
                return

            # Fetch PIN (Firestore → also caches in Credential Manager)
            cloud_pin = fetch_parent_pin()
            if cloud_pin:
                self._parent_pin = cloud_pin
                print(f"[Main] Parent PIN loaded from Firebase.")
            else:
                # Fall back to locally cached PIN
                local_pin = get_local_pin()
                if local_pin:
                    self._parent_pin = local_pin
                    print("[Main] Parent PIN loaded from local cache (offline).")
                else:
                    print("[Main] ⚠ No parent PIN found — Ctrl+Shift+P override disabled until paired.")

            # Start real-time force-unlock listener
            start_force_unlock_listener(self._on_force_unlock)

        except Exception as e:
            print(f"[Main] Firebase init error: {e}")

    def _on_force_unlock(self):
        """Called from Firestore listener thread when parent presses Force Unlock."""
        # Use QTimer.singleShot to safely execute on the Qt main thread
        QTimer.singleShot(0, self.trigger_playtime)

    # ── Scene navigation ──────────────────────────────────────

    def show_login_screen(self):
        login = LoginScene(self)
        login.login_successful.connect(self._on_login_successful)
        self.setCentralWidget(login)
        
    def _on_login_successful(self):
        self.show_loading_screen()
        import threading
        threading.Thread(target=self._init_firebase_and_pin, daemon=True).start()

    def show_loading_screen(self):
        self.setCentralWidget(LoadingScene(self))

    def show_avatar_selection(self):
        from modules.ui_scenes import AvatarSelectionScene
        self.setCentralWidget(AvatarSelectionScene(self))

    def start_game(self):
        # If the user has remaining playtime (e.g. after a reboot/crash), skip lock screen
        remaining_time = secure_load_time(TIME_BANK_FILE)
        if remaining_time > 0:
            print(f"[Main] Remaining playtime detected: {remaining_time}s. Restoring playtime.")
            self.trigger_playtime()
            return

        if not hasattr(self, 'current_avatar_selected'):
            self.current_avatar_selected = True
            self.show_avatar_selection()
        else:
            self.show_memorization_phase()

    def show_memorization_phase(self):
        self.setCentralWidget(MemorizationScene(self))

    def start_recall_phase(self, words):
        self.setCentralWidget(RecallScene(self, words))

    def start_scrambled_phase(self, words):
        self.setCentralWidget(ScrambledPhase(self, words))

    def show_final_results(self):
        self.setCentralWidget(SummaryScene(self))

    # ── Playtime (kiosk unlock) ───────────────────────────────

    def trigger_playtime(self):
        """Unlock the PC and show the floating countdown timer."""
        stop_force_unlock_listener()
        self.kiosk.disable_kiosk_mode()
        self.hide()

        self.floating_tracker = GlassyTimer(
            parent_pin=self._parent_pin,
            on_relock=self._relock_after_playtime,
        )
        self.floating_tracker.show()

    def _relock_after_playtime(self):
        """
        Called when the timer closes (time up OR parent used PIN to close early).
        Re-activates kiosk so the child goes back to the spelling game.
        """
        # Restart force-unlock listener in case parent wants to unlock again
        start_force_unlock_listener(self._on_force_unlock)
        self.kiosk.enable_kiosk_mode()
        self.showFullScreen()
        self.show_loading_screen()

    # ── ESC key & Emergency Exit logic ────────────────────────

    def is_paired(self) -> bool:
        from modules.firebase_sync import is_connected
        return is_connected()

    def handle_esc_pressed(self):
        """
        Handles ESC key press based on pairing status:
        - If unpaired (e.g. LoginScene): minimizes game to taskbar so user can check web dashboard.
        - If paired (e.g. active game): triggers emergency_exit (PIN required).
        """
        if isinstance(self.centralWidget(), LoginScene) or not self.is_paired():
            print("[Main] ESC pressed while unpaired — minimizing window to taskbar.")
            self.showMinimized()
        else:
            self.emergency_exit()

    def emergency_exit(self):
        """Ctrl+Shift+P / ESC in-game — asks for parent PIN, then unlocks and closes."""
        active_pin = self._parent_pin or get_local_pin()

        if not active_pin and (isinstance(self.centralWidget(), LoginScene) or not self.is_paired()):
            print("[Main] Unpaired device emergency exit triggered — closing.")
            self._watchdog.authorize_exit()
            self._heartbeat_timer.stop()
            stop_force_unlock_listener()
            self.kiosk.disable_kiosk_mode()
            self.close()
            return

        if not active_pin:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, "SpellGate Lock",
                "Emergency exit is disabled because no override PIN has been configured.\n\n"
                "Please configure a PIN in the Parent Dashboard or complete the setup."
            )
            return

        pin, ok = QInputDialog.getText(
            self, "Parent Override", "Enter your PIN:",
            QLineEdit.EchoMode.Password
        )

        if ok and pin == active_pin:
            # Authorise exit so the watchdog doesn't fight us
            self._watchdog.authorize_exit()
            self._heartbeat_timer.stop()
            stop_force_unlock_listener()

            self.kiosk.disable_kiosk_mode()
            self.close()

        elif ok:
            # Wrong PIN — show subtle feedback
            print("[Main] Incorrect PIN attempt.")


import ctypes

_SINGLE_INSTANCE_MUTEX = None

def _ensure_single_instance(mutex_name="Global\\SpellGateSingleInstanceMutex") -> bool:
    """Returns True if this is the only running instance of SpellGate."""
    global _SINGLE_INSTANCE_MUTEX
    try:
        kernel32 = ctypes.windll.kernel32
        _SINGLE_INSTANCE_MUTEX = kernel32.CreateMutexW(None, False, mutex_name)
        last_error = kernel32.GetLastError()
        ERROR_ALREADY_EXISTS = 183
        if last_error == ERROR_ALREADY_EXISTS:
            return False
        return True
    except Exception:
        return True


# ─────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not _ensure_single_instance():
        print("[Main] SpellGate is already running. Terminating duplicate instance.")
        sys.exit(0)

    # ── Normal launch ─────────────────────────────────────────────
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())