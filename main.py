import os
import sys
from pathlib import Path
import json

from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QRect, QSequentialAnimationGroup, QPauseAnimation, QVariantAnimation, QAbstractAnimation
from PyQt6.QtGui import QFont, QFontDatabase, QShortcut, QKeySequence, QIcon, QColor

from modules.kiosk_manager import KioskManager
from modules.ui_scenes import MemorizationScene, RecallScene, ScrambledPhase, SummaryScene
from modules.loading_scene import LoadingScene

from modules.config import TIME_BANK_FILE, USER_PROGRESS_FILE


class GlassyTimer(QWidget):
    def __init__(self):
        super().__init__()
        font_id = QFontDatabase.addApplicationFont("assets/PressStart2P-Regular.ttf")
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0] if font_id != -1 else "Arial"

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(0.9)

        self.container = QWidget(self)
        self.container.setObjectName("TimerContainer")
        self.container.setStyleSheet("""
            QWidget#TimerContainer {
                background-color: rgba(15, 23, 42, 200);
                border-radius: 20px;
                border: 2px solid #38BDF8;
            }
        """)

        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(20)
        self.shadow.setColor(QColor(56, 189, 248, 150))
        self.container.setGraphicsEffect(self.shadow)

        layout = QVBoxLayout(self.container)
        self.label = QLabel("00:00:00", self)
        self.label.setFont(QFont(font_family, 24))
        self.label.setStyleSheet("color: #38BDF8; padding: 10px;")
        layout.addWidget(self.label)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.container)
        self.setGeometry(100, 100, 220, 100)

        # Timer Logic
        self.time_left = self.load_time()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        # FIX: was Qt.MouseButton.leftButton (invalid) — now LeftButton
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()


    def load_time(self):
        try:
            with open(TIME_BANK_FILE, "r") as f:
                return int(f.read().strip())
        except:
            return 0 

    def update_time(self):
        if self.time_left > 0:
            self.time_left -= 1
            hrs, remainder = divmod(self.time_left, 3600)
            mins, secs = divmod(remainder, 60)
            self.label.setText(f"{hrs:02d}:{mins:02d}:{secs:02d}")

            if self.time_left % 10 == 0:
                with open("data/time_bank.txt", "w") as f:
                    f.write(str(self.time_left))

        else:
            self.timer.stop()
            self.label.setText("TIME UP")
            self.label.setStyleSheet("color: red;")
            # Real shutdown trigger (Phase 2 hardening)
            import os
            os.system("shutdown /s /t 60")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SpellGate Lock")
        self.setStyleSheet("QMainWindow { background-color: #0a0a0a; }")

        # Ensure the data directory + time_bank exist — but NEVER reset earned time
        os.makedirs(os.path.dirname(TIME_BANK_FILE), exist_ok=True)
        if not os.path.exists(TIME_BANK_FILE):
            with open(TIME_BANK_FILE, "w") as f:
                f.write("0")
        
        self.current_avatar = "Interceptor" # Default
        self.kiosk = KioskManager(self)
        self.kiosk.enable_kiosk_mode()

        self.exit_shortcut = QShortcut(QKeySequence("Ctrl+Shift+P"), self)
        self.exit_shortcut.activated.connect(self.emergency_exit)

        self.showFullScreen()          # forces true fullscreen
        self.setContentsMargins(0,0,0,0)
        self.setWindowIcon(QIcon("assets/icons/logo.png"))

        self.show_loading_screen()

    def show_loading_screen(self):
        self.setCentralWidget(LoadingScene(self))

    def show_avatar_selection(self):
        from modules.ui_scenes import AvatarSelectionScene
        self.setCentralWidget(AvatarSelectionScene(self))

    def start_game(self):
        # Check if we have an avatar, if not, select one
        if not hasattr(self, 'current_avatar_selected'):
            self.current_avatar_selected = True
            self.show_avatar_selection()
        else:
            self.show_memorization_phase()

    def show_memorization_phase(self):
        self.setCentralWidget(MemorizationScene(self))
        

    def start_recall_phase(self, words):
        # This switches the screen to the Recall Phase
        self.setCentralWidget(RecallScene(self, words))

    def start_scrambled_phase(self, words):
        self.setCentralWidget(ScrambledPhase(self, words))

    def show_final_results(self):
        self.setCentralWidget(SummaryScene(self))

    def trigger_playtime(self):
        """Closes time game, unlocks the PC, and launches the floating timer."""
        self.kiosk.disable_kiosk_mode()
        self.hide()

        self.floating_tracker = GlassyTimer()
        self.floating_tracker.show()

    def emergency_exit(self):
        self.kiosk.disable_kiosk_mode()
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())