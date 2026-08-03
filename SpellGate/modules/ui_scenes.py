import json
import random
from modules.audio import play_audio

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
                             QPushButton, QGraphicsDropShadowEffect, QLineEdit, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QEasingCurve, QVariantAnimation, QAbstractAnimation
from PyQt6.QtGui import QFont, QColor, QFontDatabase, QPainter, QPen
from modules.game_logic import generate_scrambled, update_mastery, get_next_words, save_progress, load_progress
from modules.config import TIME_BANK_FILE, USER_PROGRESS_FILE
from modules.security import secure_load_time, secure_save_time

DARK_THEME = """
    QWidget { 
        background-color: #0a0a0a; 
        color: #facc15; 
    }
    QLabel#Header { 
        color: #ff00ff; 
    }
    QLineEdit { 
        background-color: #000000; 
        border: 3px solid #ff00ff; 
        border-radius: 2px; 
        padding: 12px; 
        color: #ff00ff; 
    }
    QPushButton#WordCard { 
        background-color: #000000; 
        border-radius: 4px; 
        color: #FFFFFF; 
        padding: 15px;
    }
    QPushButton#ActionBtn { 
        background-color: #000000; 
        color: #facc15; 
        border: 3px solid #facc15;
        border-radius: 0px; 
        padding: 15px; 
    }
"""

LIGHT_THEME = """
    QWidget { 
        background-color: #1a1a1a; 
        color: #facc15; 
    }
    QLabel#Header { 
        color: #ff00ff; 
    }
    QLineEdit { 
        background-color: #111111; 
        border: 3px solid #22d3ee; 
        border-radius: 2px; 
        padding: 12px; 
        color: #22d3ee; 
    }
    QPushButton#WordCard { 
        background-color: #111111; 
        border-radius: 4px; 
        color: #FFFFFF; 
        padding: 15px;
    }
    QPushButton#ActionBtn { 
        background-color: #111111; 
        color: #facc15; 
        border: 3px solid #facc15;
        border-radius: 0px; 
        padding: 15px; 
    }
"""

NEON_COLORS = ["#22d3ee", "#ff00ff", "#facc15", "#4ade80"]

class SpeakingLineEdit(QLineEdit):
    """A custom text box that tells the user what word to spell and auto-capitalizes."""

    # Class-level flag: when True, focusInEvent will NOT auto-play the word.
    # Set to True before a replay button click, False after audio finishes.
    _audio_locked: bool = False

    def __init__(self, word, parent=None):
        super().__init__(parent)
        self.target_word = word
        self.textChanged.connect(self.force_uppercase)

        self.glow = QGraphicsDropShadowEffect(self)
        self.glow.setBlurRadius(0)
        self.glow.setColor(QColor("#ff00ff"))
        self.glow.setOffset(0, 0)
        self.setGraphicsEffect(self.glow)

        self.anim = QVariantAnimation(self)
        self.anim.setDuration(800)
        self.anim.setStartValue(5)
        self.anim.setEndValue(25)
        self.anim.valueChanged.connect(lambda v: self.glow.setBlurRadius(v))
        self.anim.finished.connect(self.toggle_anim_direction)

    def toggle_anim_direction(self):
        from PyQt6.QtCore import QAbstractAnimation
        if self.anim.direction() == QAbstractAnimation.Direction.Forward:
            self.anim.setDirection(QAbstractAnimation.Direction.Backward)
        else:
            self.anim.setDirection(QAbstractAnimation.Direction.Forward)
        self.anim.start()

    def force_uppercase(self, text):
        if text != text.upper():
            self.setText(text.upper())

    def focusInEvent(self, event):
        super().focusInEvent(event)
        # Only auto-announce if audio is NOT currently locked by a replay button.
        # This prevents focusInEvent from triggering when clicking 🔊 HEAR WORD
        # shifts focus to a neighboring input field.
        if not SpeakingLineEdit._audio_locked:
            play_audio(f"Spell {self.target_word}")
        self.anim.start()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.anim.stop()
        self.glow.setBlurRadius(0)

class BaseScene(QWidget):
    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.is_dark = True

        font_id = QFontDatabase.addApplicationFont("assets/PressStart2P-Regular.ttf")
        self.arcade_family = QFontDatabase.applicationFontFamilies(font_id)[0] if font_id != -1 else "Arial"

    def get_rank_title(self):
        avatar = getattr(self.parent_window, 'current_avatar', 'Interceptor')
        try:
            from modules.config import USER_PROGRESS_FILE
            from modules.game_logic import load_progress
            progress_data = load_progress(USER_PROGRESS_FILE)
            level = progress_data.get("current_level", "Novice")
        except:
            level = "Novice"
        
        ranks = {
            "Interceptor": {"Novice": "CADET", "Apprentice": "STRIKE PILOT", "Scholar": "ACE COMMANDER"},
            "Guardian": {"Novice": "SHIELD BEARER", "Apprentice": "SENTINEL", "Scholar": "BASTION PRIME"},
            "Voyager": {"Novice": "EXPLORER", "Apprentice": "NAVIGATOR", "Scholar": "STARWAY CAPTAIN"}
        }
        return ranks.get(avatar, ranks["Interceptor"]).get(level, "CADET")

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        # Dynamic static grid for that arcade look
        grid_pen = QPen(QColor(255, 255, 255, 12)) 
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        
        # Draw vertical lines
        for x in range(0, self.width(), 32):
            painter.drawLine(x, 0, x, self.height())
            
        # Draw horizontal lines
        for y in range(0, self.height(), 32):
            painter.drawLine(0, y, self.width(), y)
        
        # Draw a subtle darkened gradient overlay
        painter.fillRect(self.rect(), QColor(0, 0, 0, 40))
        
    def apply_current_theme(self):
        self.setStyleSheet(DARK_THEME if self.is_dark else LIGHT_THEME)

    def screen_shake(self, intensity=15):
        """Violent screen shake for errors."""
        anim = QPropertyAnimation(self, b"pos", self)
        anim.setDuration(50)
        curr = self.pos()
        anim.setKeyValueAt(0, curr)
        anim.setKeyValueAt(0.25, curr + QPoint(-intensity, intensity//2))
        anim.setKeyValueAt(0.5, curr + QPoint(intensity, -intensity))
        anim.setKeyValueAt(0.75, curr + QPoint(-intensity//2, intensity))
        anim.setKeyValueAt(1, curr)
        anim.setLoopCount(4)
        anim.start()
        self._shake_anim = anim

    def combo_pulse(self):
        """Rainbow pulse for high streaks."""
        overlay = QWidget(self)
        overlay.setGeometry(self.rect())
        overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        overlay.show()
        
        anim = QVariantAnimation(self)
        anim.setDuration(600)
        anim.setStartValue(0.3)
        anim.setEndValue(0.0)
        
        colors = ["#ff00ff", "#22d3ee", "#facc15"]
        import random
        c = random.choice(colors)
        
        def set_op(v):
            overlay.setStyleSheet(f"background-color: {c}; opacity: {v};")
        
        anim.valueChanged.connect(set_op)
        anim.finished.connect(overlay.deleteLater)
        anim.start()
        self._pulse_anim = anim

    def draw_spaceship(self, painter, rect, type="Interceptor", color="#22d3ee"):
        """Draws a pixel-art style spaceship using primitives."""
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(color))
        
        cx, cy = rect.center().x(), rect.center().y()
        w, h = rect.width(), rect.height()
        
        if type == "Interceptor": # 🚀 Shape
            # Main body
            painter.drawRect(cx-w//6, cy-h//3, w//3, h//2)
            # Nose
            painter.drawPolygon([QPoint(cx-w//6, cy-h//3), QPoint(cx+w//6, cy-h//3), QPoint(cx, cy-h//2)])
            # Wings
            painter.drawRect(cx-w//3, cy-h//6, w//6, h//4)
            painter.drawRect(cx+w//6, cy-h//6, w//6, h//4)
            # Engine glow
            painter.setBrush(QColor("#ff00ff"))
            painter.drawRect(cx-w//8, cy+h//6, w//4, h//8)
            
        elif type == "Guardian": # 🛸 Shape
            # Saucer body
            painter.drawEllipse(cx-w//2, cy-h//6, w, h//3)
            # Dome
            painter.setBrush(QColor("#4ade80"))
            painter.drawEllipse(cx-w//4, cy-h//3, w//2, h//3)
            # Lights
            painter.setBrush(QColor("#ffffff"))
            painter.drawEllipse(cx-w//3, cy, 4, 4)
            painter.drawEllipse(cx, cy+4, 4, 4)
            painter.drawEllipse(cx+w//3, cy, 4, 4)
            
        elif type == "Voyager": # 📡 Shape
            # Dish
            painter.drawChord(cx-w//2, cy-h//2, w, h, 0*16, 180*16)
            # Base
            painter.drawRect(cx-4, cy, 8, h//3)
            # Signal bits
            painter.setBrush(QColor("#facc15"))
            painter.drawRect(cx-w//2, cy-h//2, 4, 4)
            painter.drawRect(cx+w//2-4, cy-h//2, 4, 4)

    def create_theme_toggle(self, layout):
        self.toggle_btn = QPushButton("[DARK]" if self.is_dark else "[LITE]", self)
        self.toggle_btn.setFixedSize(120, 40)
        self.toggle_btn.setStyleSheet("background: transparent; color: #facc15; font-size: 14px; border: none;")
        self.toggle_btn.setFont(QFont(self.arcade_family, 10))
        self.toggle_btn.clicked.connect(self.switch_theme)
        layout.addWidget(self.toggle_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def switch_theme(self):
        self.is_dark = not self.is_dark
        self.toggle_btn.setText("[DARK]" if self.is_dark else "[LITE]")
        self.apply_current_theme()

    def setup_scanline(self):
        # The main moving scanline
        self.scanline = QLabel(self)
        self.scanline.setStyleSheet("background-color: rgba(34, 211, 238, 15); border-bottom: 2px solid rgba(34, 211, 238, 60);")
        self.scanline.setFixedHeight(12)
        self.scanline.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.scanline.show()
        self.scanline.raise_()

        self.scan_anim = QPropertyAnimation(self.scanline, b"pos", self)
        self.scan_anim.setDuration(4000)
        self.scan_anim.setStartValue(QPoint(0, -20))
        self.scan_anim.setEndValue(QPoint(0, 1080))
        self.scan_anim.setLoopCount(-1)
        self.scan_anim.start()

        # Adding a subtle full-screen flicker
        self.flicker_overlay = QWidget(self)
        self.flicker_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.flicker_overlay.setStyleSheet("background-color: rgba(255, 255, 255, 5);")
        self.flicker_overlay.hide()
        
        self.flicker_timer = QTimer(self)
        self.flicker_timer.timeout.connect(self._do_flicker)
        self.flicker_timer.start(50)

    def _do_flicker(self):
        import random
        if random.random() > 0.98:
            self.flicker_overlay.show()
            QTimer.singleShot(30, self.flicker_overlay.hide)

    def show_score_popup(self, widget, text, color="#4ade80"):
        """Floating score feedback."""
        popup = QLabel(text, self)
        popup.setFont(QFont(self.arcade_family, 14))
        popup.setStyleSheet(f"color: {color}; background: transparent;")
        
        # Position relative to the widget
        pos = widget.mapTo(self, QPoint(widget.width() // 2, 0))
        popup.move(pos.x() - 20, pos.y())
        popup.show()
        
        anim = QPropertyAnimation(popup, b"pos", self)
        anim.setDuration(800)
        anim.setStartValue(popup.pos())
        anim.setEndValue(popup.pos() - QPoint(0, 100))
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Fade out effect
        opacity_anim = QVariantAnimation(self)
        opacity_anim.setDuration(800)
        opacity_anim.setStartValue(1.0)
        opacity_anim.setEndValue(0.0)
        def set_op(v):
            popup.setStyleSheet(f"color: {color}; background: transparent; opacity: {v};")
        opacity_anim.valueChanged.connect(set_op)
        
        anim.finished.connect(popup.deleteLater)
        anim.start()
        opacity_anim.start()
        
        if not hasattr(self, '_anims'): self._anims = []
        self._anims.append(anim)
        self._anims.append(opacity_anim)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'scanline'):
            self.scanline.setFixedWidth(self.width())
            if self.height() > 0:
                self.scan_anim.setEndValue(QPoint(0, self.height() + 20))
        if hasattr(self, 'flicker_overlay'):
            self.flicker_overlay.setGeometry(self.rect())

    def create_avatar_widget(self):
        """Creates a small widget that displays the current hero."""
        avatar_type = getattr(self.parent_window, 'current_avatar', 'Interceptor')
        color = NEON_COLORS[0]
        
        class AvatarDisplay(QWidget):
            def __init__(self, scene, atype):
                super().__init__(scene)
                self.scene = scene
                self.atype = atype
                self.setFixedSize(100, 100)
                self.bob_val = 0
                self.timer = QTimer(self)
                self.timer.timeout.connect(self.update_bob)
                self.timer.start(50)
                
            def update_bob(self):
                import math
                self.bob_val += 0.2
                self.move(self.x(), self.y() + int(math.sin(self.bob_val) * 2))
                self.update()
                
            def paintEvent(self, event):
                painter = QPainter(self)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                self.scene.draw_spaceship(painter, self.rect().adjusted(10,10,-10,-10), self.atype)

        return AvatarDisplay(self, avatar_type)

    def wobble(self, widget):
        """Standard arcade 'error' wobble."""
        anim = QPropertyAnimation(widget, b"pos", widget)
        anim.setDuration(50)
        curr = widget.pos()
        anim.setKeyValueAt(0, curr)
        anim.setKeyValueAt(0.25, curr + QPoint(-15, 0))
        anim.setKeyValueAt(0.75, curr + QPoint(15, 0))
        anim.setKeyValueAt(1, curr)
        anim.setLoopCount(3)
        anim.start()
        widget._wobble_anim = anim

# --- NEW: AVATAR SELECTION ---
class AvatarSelectionScene(BaseScene):
    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.initUI()
        self.apply_current_theme()
        self.setup_scanline()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 40, 60, 40)
        layout.addStretch()
        header = QLabel("SELECT YOUR SPACESHIP", self)
        header.setFont(QFont(self.arcade_family, 32))
        header.setStyleSheet("color: #ff00ff; background: transparent;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        layout.addSpacing(60)
        
        grid = QHBoxLayout()
        grid.setSpacing(60)
        
        ships = [
            ("Interceptor", "🚀 FAST", "#22d3ee"),
            ("Guardian", "🛸 SAFE", "#4ade80"),
            ("Voyager", "📡 SMART", "#facc15")
        ]
        
        for name, desc, color in ships:
            card = QWidget()
            card.setFixedSize(280, 380)
            card.setStyleSheet(f"border: 3px solid {color}; background: #000; border-radius: 10px;")
            cl = QVBoxLayout(card)
            
            # Draw preview
            class ShipPreview(QWidget):
                def __init__(self, scene, stype, scolor):
                    super().__init__()
                    self.scene = scene
                    self.stype = stype
                    self.scolor = scolor
                    self.setFixedSize(200, 200)
                def paintEvent(self, event):
                    p = QPainter(self)
                    self.scene.draw_spaceship(p, self.rect().adjusted(10,10,-10,-10), self.stype, self.scolor)
            
            cl.addWidget(ShipPreview(self, name, color), alignment=Qt.AlignmentFlag.AlignCenter)
            
            n_lbl = QLabel(name.upper())
            n_lbl.setFont(QFont(self.arcade_family, 18))
            n_lbl.setStyleSheet(f"color: {color}; border: none;")
            n_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(n_lbl)
            
            d_lbl = QLabel(desc)
            d_lbl.setFont(QFont(self.arcade_family, 10))
            d_lbl.setStyleSheet("color: #334155; border: none;")
            d_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(d_lbl)
            
            btn = QPushButton("SELECT")
            btn.setObjectName("ActionBtn")
            btn.setFont(QFont(self.arcade_family, 14))
            btn.setFixedHeight(45)
            btn.setStyleSheet(
                f"border: 2px solid {color}; color: {color};"
                "background-color: #0a0a0a;"
                "letter-spacing: 3px;"
            )
            btn.clicked.connect(lambda checked, n=name: self.select_ship(n))
            cl.addWidget(btn)
            
            grid.addWidget(card)
            
        layout.addLayout(grid)
        layout.addStretch()

    def select_ship(self, name):
        self.parent_window.current_avatar = name
        
        from modules.config import USER_PROGRESS_FILE
        from modules.game_logic import load_progress, save_progress
        progress_data = load_progress(USER_PROGRESS_FILE)
        progress_data["spaceship"] = name
        save_progress(progress_data, USER_PROGRESS_FILE)
        
        play_audio(f"{name} online!")
        self.parent_window.start_game()

from PyQt6.QtCore import QThread, pyqtSignal

class WordLoaderThread(QThread):
    words_loaded = pyqtSignal(list)
    def __init__(self, progress_data, filepath, count):
        super().__init__()
        self.progress_data = progress_data
        self.filepath = filepath
        self.count = count

    def run(self):
        from modules.game_logic import get_next_words
        words = get_next_words(self.progress_data, self.filepath, count=self.count)
        self.words_loaded.emit(words)

class MemorizationScene(BaseScene): 
    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.time_left = 300
        self.words = []
        self.main_layout = QVBoxLayout(self)
        
        self.progress_data = load_progress(USER_PROGRESS_FILE)
        
        self.initLoadingUI()
        self.apply_current_theme()
        self.setup_scanline()

        self.loader_thread = WordLoaderThread(self.progress_data, "assets/words.csv", 12)
        self.loader_thread.words_loaded.connect(self.on_words_loaded)
        self.loader_thread.start()

    def initLoadingUI(self):
        self.loading_container = QWidget(self)
        l = QVBoxLayout(self.loading_container)
        self.loading_lbl = QLabel("CONNECTING TO AI CORE...\nGENERATING WORDS", self)
        self.loading_lbl.setFont(QFont(self.arcade_family, 24))
        self.loading_lbl.setStyleSheet("color: #22d3ee; background: transparent; letter-spacing: 2px;")
        self.loading_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(self.loading_lbl)
        
        self.main_layout.addWidget(self.loading_container, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self._blink_state = True
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self._blink_loading)
        self.blink_timer.start(500)

    def _blink_loading(self):
        self._blink_state = not self._blink_state
        op = "1.0" if self._blink_state else "0.0"
        self.loading_lbl.setStyleSheet(f"color: #22d3ee; background: transparent; opacity: {op}; letter-spacing: 2px;")

    def on_words_loaded(self, words):
        self.words = words
        
        # Adaptive time bonus for longer words
        extra_time = 0
        for w in words:
            if len(w.get("word", "")) >= 7:
                extra_time += 60
        self.time_left += extra_time
        
        save_progress(self.progress_data)
        self.blink_timer.stop()
        self.loading_container.hide()
        self.loading_container.deleteLater()
        self.initUI()
        self.apply_current_theme()
        
        # Start game timers here so they don't run during loading
        self.study_timer = QTimer(self)
        self.study_timer.timeout.connect(self.update_timer)
        self.study_timer.start(1000)
        QTimer.singleShot(100, self.animate_cards_in)

        # Poll done_callbacks from audio.py every 100 ms — safe Qt main-thread dispatch
        from modules.audio import done_callbacks as _dcb
        self._done_callbacks = _dcb
        self._cb_poller = QTimer(self)
        self._cb_poller.timeout.connect(self._flush_audio_callbacks)
        self._cb_poller.start(100)

    def _flush_audio_callbacks(self):
        """Drain audio done_callbacks and execute them on the main thread."""
        try:
            while True:
                cb = self._done_callbacks.get_nowait()
                try:
                    cb()
                except Exception:
                    pass
                self._done_callbacks.task_done()
        except Exception:
            pass  # queue.Empty — nothing to do

    def _lock_cards(self, active_card, active_color):
        """Dim all cards and mark the active one as playing."""
        for card in self.cards:
            card.setEnabled(False)
        # Give visual feedback on which card is speaking
        active_card.setStyleSheet(
            f"QPushButton#WordCard {{ border: 3px solid {active_color};"
            f" background-color: #1a1000; color: #facc15; padding: 15px; border-radius: 4px; }}"
        )

    def _unlock_cards(self, card_styles):
        """Re-enable all cards and restore their original styles."""
        for card, style in zip(self.cards, card_styles):
            card.setEnabled(True)
            card.setStyleSheet(style)

    def initUI(self):
        layout = self.main_layout
        layout.setSpacing(12)
        layout.setContentsMargins(40, 16, 40, 24)

        self.create_theme_toggle(layout) 
        
        hud_layout = QHBoxLayout()
        lives_lbl = QLabel("LIVES: ❤️❤️❤️", self)
        lives_lbl.setFont(QFont(self.arcade_family, 9))
        lives_lbl.setStyleSheet("color: #22d3ee; background: transparent;")

        score_lbl = QLabel("SCORE: 04800", self)
        score_lbl.setFont(QFont(self.arcade_family, 9))
        score_lbl.setStyleSheet("color: #22d3ee; background: transparent;")

        rank_lbl = QLabel(f"RANK: {self.get_rank_title()}", self)
        rank_lbl.setFont(QFont(self.arcade_family, 9))
        rank_lbl.setStyleSheet("color: #ff00ff; background: transparent;")

        hud_layout.addWidget(lives_lbl)
        hud_layout.addStretch()
        hud_layout.addWidget(rank_lbl)
        hud_layout.addStretch()
        hud_layout.addWidget(score_lbl)
        layout.addLayout(hud_layout)
        
        self.header_container = QWidget(self)
        self.header_container.setStyleSheet("border: 2px solid #ff00ff; background: rgba(255, 0, 255, 20); padding: 4px;")
        self.header_container.setFixedHeight(70)
        
        self.avatar = self.create_avatar_widget()
        self.avatar.setParent(self.header_container)
        self.avatar.setFixedSize(60, 60)
        self.avatar.move(10, 5)
        self.avatar.show()

        hc_layout = QVBoxLayout(self.header_container)
        hc_layout.setContentsMargins(0, 0, 0, 0)

        header = QLabel("SPELL GATE", self.header_container)
        header.setObjectName("Header")
        header.setFont(QFont(self.arcade_family, 32))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hc_layout.addWidget(header)
        
        subtitle = QLabel("SPELL TO EARN TIME", self)
        subtitle.setFont(QFont(self.arcade_family, 9))
        subtitle.setStyleSheet("color: #94a3b8; background: transparent; letter-spacing: 3px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # 1. Instruction State Banner ("SELECT A WORD TO BEGIN", fades after first interaction)
        self.instruction_banner = QLabel("SELECT A WORD TO BEGIN", self)
        self.instruction_banner.setFont(QFont(self.arcade_family, 10))
        self.instruction_banner.setStyleSheet(
            "color: #22d3ee; background: rgba(0, 229, 255, 0.12); border: 1px solid rgba(0, 229, 255, 0.4);"
            " padding: 6px 16px; border-radius: 20px; letter-spacing: 2px;"
        )
        self.instruction_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.instruction_banner, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.header_glow = QGraphicsDropShadowEffect(header)
        self.header_glow.setColor(QColor("#ff00ff"))
        self.header_glow.setOffset(0, 0)
        header.setGraphicsEffect(self.header_glow)

        self.header_anim = QVariantAnimation(header)
        self.header_anim.setDuration(1500)
        self.header_anim.setStartValue(8)
        self.header_anim.setEndValue(25)
        self.header_anim.valueChanged.connect(lambda v: self.header_glow.setBlurRadius(v))
        
        # Implement ping-pong without loopCount(-1) and Alternate
        def toggle_header_anim():
            from PyQt6.QtCore import QAbstractAnimation
            if self.header_anim.direction() == QAbstractAnimation.Direction.Forward:
                self.header_anim.setDirection(QAbstractAnimation.Direction.Backward)
            else:
                self.header_anim.setDirection(QAbstractAnimation.Direction.Forward)
            self.header_anim.start()
        
        self.header_anim.finished.connect(toggle_header_anim)
        self.header_anim.start()

        # Timer container
        self.timer_container = QWidget(self)
        self.timer_container.setStyleSheet("border: 3px solid #22d3ee; background-color: #000; padding: 10px;")
        self.timer_container.setMaximumWidth(600)
        self.timer_container.setMinimumWidth(320)
        self.timer_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        tc_glow = QGraphicsDropShadowEffect(self.timer_container)
        tc_glow.setBlurRadius(20)
        tc_glow.setColor(QColor("#22d3ee"))
        tc_glow.setOffset(0, 0)
        self.timer_container.setGraphicsEffect(tc_glow)
        
        tc_layout = QVBoxLayout(self.timer_container)
        
        time_prefix = QLabel("TIME", self.timer_container)
        time_prefix.setFont(QFont(self.arcade_family, 9))
        time_prefix.setStyleSheet("color: #22d3ee; border: none; letter-spacing: 4px;")
        time_prefix.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tc_layout.addWidget(time_prefix)
        
        self.timer_label = QLabel("05:00", self.timer_container)
        self.timer_label.setFont(QFont(self.arcade_family, 48))
        self.timer_label.setStyleSheet("color: #22d3ee; border: none;")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tc_layout.addWidget(self.timer_label)


        
        layout.addWidget(self.timer_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # 2. Labeled Difficulty Legend & Grid Container
        grid_widget = QWidget(self)
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setContentsMargins(10, 5, 10, 10)
        grid_layout.setSpacing(12)
        
        TIER_NAMES = ["NOVICE", "APPRENTICE", "SCHOLAR", "RECALL"]
        TIER_COLORS = ["#22c55e", "#e879f9", "#facc15", "#f97316"]
        
        # Render Column Difficulty Legend Chips
        for c, (tier_name, color) in enumerate(zip(TIER_NAMES, TIER_COLORS)):
            chip = QLabel(tier_name, grid_widget)
            chip.setFont(QFont(self.arcade_family, 8))
            chip.setStyleSheet(
                f"color: {color}; background-color: rgba(0,0,0,0.6); border: 1px solid {color};"
                " padding: 4px 8px; border-radius: 4px; letter-spacing: 2px;"
            )
            chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid_layout.addWidget(chip, 0, c)
        
        import math
        self.cards = []
        row, col = 1, 0
        for i, word_data in enumerate(self.words):
            card = self.create_word_card(word_data, i)
            grid_layout.addWidget(card, row, col)
            self.cards.append(card)
            col += 1
            if col > 3:
                col = 0
                row += 1
        
        layout.addWidget(grid_widget)

        # Primary Action CTA (RECALL MODE - Direct transition to Recall Phase)
        self.ready_btn = QPushButton("RECALL MODE  ▶", self)
        self.ready_btn.setFont(QFont(self.arcade_family, 14))
        self.ready_btn.setStyleSheet(
            "QPushButton { background: #facc15; color: #000000; border: 2px solid #facc15;"
            " padding: 14px 32px; border-radius: 6px; font-weight: bold; letter-spacing: 2px; }"
            "QPushButton:hover { background: #fde047; }"
        )
        ab_glow = QGraphicsDropShadowEffect(self.ready_btn)
        ab_glow.setBlurRadius(16)
        ab_glow.setColor(QColor("#facc15"))
        ab_glow.setOffset(0, 0)
        self.ready_btn.setGraphicsEffect(ab_glow)

        self.ready_btn.clicked.connect(self.finish_memorization)
        layout.addWidget(self.ready_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def create_word_card(self, word_data, index):
        word = word_data["word"]
        sentence = word_data["sentence"]
        is_recall = word_data.get("is_recall") or word_data.get("mastered") or (index % 4 == 3)
        
        # 4. Functional Crown Icon (ONLY on mastered/recall stage words)
        display_label = f"👑  {word}" if is_recall else word
        
        color = NEON_COLORS[index % 4]
        default_style = (
            f"QPushButton#WordCard {{ border: 2px solid {color};"
            f" background-color: rgba(10, 10, 15, 0.9); color: #FFFFFF; padding: 12px; border-radius: 6px; }}"
            f"QPushButton#WordCard:hover {{ background-color: rgba(255, 255, 255, 0.08); border-width: 3px; }}"
        )

        btn = QPushButton(display_label)
        btn.setObjectName("WordCard")
        btn.setMinimumHeight(65)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn.setSizePolicy(QPushButton.sizePolicy(btn).horizontalPolicy().Expanding,
                          QPushButton.sizePolicy(btn).verticalPolicy().Fixed)
        btn.setStyleSheet(default_style)
        
        # 5. Legible Word Text (Clean Sans-Serif font Segoe UI / Inter bold)
        sans_font = QFont("Segoe UI", 15, QFont.Weight.Bold)
        sans_font.setStyleHint(QFont.StyleHint.SansSerif)
        btn.setFont(sans_font)

        glow = QGraphicsDropShadowEffect(btn)
        glow.setBlurRadius(15)
        glow.setColor(QColor(color))
        glow.setOffset(0, 0)
        btn.setGraphicsEffect(glow)

        def on_click(_checked=False, w=word, s=sentence, b=btn, c=color):
            # NOTE: _checked absorbs the bool Qt sends with clicked() — DO NOT remove it!
            # Snapshot current styles of all cards for restoration
            card_styles = [card.styleSheet() for card in self.cards]
            # Lock all cards immediately
            self._lock_cards(b, c)
            # Brief flash on the clicked card
            b.setStyleSheet(
                f"QPushButton#WordCard {{ border: 3px solid {c};"
                f" background-color: #ffffff18; color: #FFFFFF; padding: 15px; border-radius: 4px; }}"
            )
            QTimer.singleShot(120, lambda: self._lock_cards(b, c))
            # Play audio — unlock all cards via on_done callback
            play_audio(
                f"{w}. <PAUSE> {s}",
                on_done=lambda: self._unlock_cards(card_styles)
            )

        btn.clicked.connect(on_click)
        return btn

    def animate_cards_in(self):
        self.animations = []
        delay = 0
        for card in self.cards:
            anim = QPropertyAnimation(card, b"pos")
            anim.setDuration(600)
            anim.setStartValue(QPoint(card.x(), card.y() + 50))
            anim.setEndValue(QPoint(card.x(), card.y()))
            anim.setEasingCurve(QEasingCurve.Type.OutBack)
            QTimer.singleShot(delay, anim.start)
            self.animations.append(anim)
            delay += 100

    def update_timer(self):
        if self.time_left > 0:
            self.time_left -= 1
            mins, secs = divmod(self.time_left, 60)
            self.timer_label.setText(f"{mins:02d}:{secs:02d}")
            
            # Spaceship progress bar
            progress_ratio = 1.0 - (self.time_left / 300.0)
            max_x = self.header_container.width() - self.avatar.width() - 10
            if max_x > 0:
                new_x = 10 + int(progress_ratio * max_x)
                self.avatar.move(new_x, self.avatar.y())
        else:
            self.finish_memorization()

    def finish_memorization(self):
        self.study_timer.stop()
        # Extract just the words for the recall phase logic
        self.parent_window.start_recall_phase(self.words)

# --- PHASE 2 ---
class RecallScene(BaseScene):
    def __init__(self, parent_window, words):
        super().__init__(parent_window)
        self.words = words
        self.inputs = []
        self.replay_buttons = []   # all 🔊 HEAR WORD buttons — locked together
        self.attempts = [0] * len(words)
        self.earned_seconds = 0
        self.combo_streak = 0
        self.session_report = []   # BUG-04 FIX: was never initialized — caused AttributeError
        self.initUI()
        self.apply_current_theme()
        self.setup_scanline()

        # Poll done_callbacks from audio.py every 100 ms — safe Qt main-thread dispatch
        from modules.audio import done_callbacks as _dcb
        self._done_callbacks = _dcb
        self._cb_poller = QTimer(self)
        self._cb_poller.timeout.connect(self._flush_audio_callbacks)
        self._cb_poller.start(100)

    def _flush_audio_callbacks(self):
        """Drain audio done_callbacks and execute them on the main thread."""
        try:
            while True:
                cb = self._done_callbacks.get_nowait()
                try:
                    cb()
                except Exception:
                    pass
                self._done_callbacks.task_done()
        except Exception:
            pass  # queue.Empty — nothing to do

    def _lock_replay_buttons(self, active_btn, original_text, active_color):
        """Disable all replay buttons, suppress focusInEvent speech, show playing indicator."""
        SpeakingLineEdit._audio_locked = True   # ← suppress wrong-word announcements
        for btn in self.replay_buttons:
            btn.setEnabled(False)
            btn.setStyleSheet(
                btn.styleSheet().replace("background-color: #0a0a0a", "background-color: #050505")
            )
        # Highlight the one currently playing
        active_btn.setText("⏳  PLAYING...")
        active_btn.setStyleSheet(
            f"border: 1px solid {active_color}; color: {active_color};"
            "background-color: #1a1000; letter-spacing: 2px; margin-top: 2px;"
        )

    def _unlock_replay_buttons(self, btn_snapshot):
        """Re-enable all replay buttons and restore focusInEvent speech."""
        SpeakingLineEdit._audio_locked = False  # ← re-enable auto-announce on focus
        for btn, (bcolor, btext) in zip(self.replay_buttons, btn_snapshot):
            btn.setEnabled(True)
            btn.setText(btext)
            btn.setStyleSheet(
                f"border: 1px solid {bcolor}; color: {bcolor};"
                "background-color: #0a0a0a; letter-spacing: 2px; margin-top: 2px;"
            )
        for btn in getattr(self, 'snail_buttons', []):
            btn.setEnabled(True)
            bcolor = btn.styleSheet().split("color: ")[1].split(";")[0].strip() if "color: " in btn.styleSheet() else "#fff"
            btn.setStyleSheet(
                f"border: 1px solid {bcolor}; color: {bcolor};"
                "background-color: #0a0a0a; letter-spacing: 2px; margin-top: 2px;"
            )

    def _on_replay_clicked(self, active_btn, word, sentence, active_color, slow=False):
        """
        Called when a 🔊 HEAR WORD button is clicked.
        - Captures the current label of every replay button.
        - Locks all buttons immediately.
        - Plays the word audio with an on_done callback.
        - on_done fires on the Qt main thread (via the poller) to unlock all.
        """
        # Snapshot of (color, current text) for every button so we can restore them
        btn_snapshot = []
        for btn in self.replay_buttons:
            ss = btn.styleSheet()
            # Pull color out of the stylesheet: "border: 1px solid #xxxx; color: #xxxx;"
            try:
                bcolor = ss.split("color: ")[1].split(";")[0].strip()
            except Exception:
                bcolor = active_color
            btn_snapshot.append((bcolor, btn.text()))

        # Lock everything
        self._lock_replay_buttons(active_btn, "🔊" if not slow else "🐢", active_color)
        for s_btn in getattr(self, 'snail_buttons', []):
            s_btn.setEnabled(False)
            s_btn.setStyleSheet(
                s_btn.styleSheet().replace("background-color: #0a0a0a", "background-color: #050505")
            )

        # Play with on_done that unlocks on completion
        play_audio(
            f"{word}. <PAUSE> {sentence}",
            on_done=lambda: self._unlock_replay_buttons(btn_snapshot),
            slow=slow
        )


    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(40, 16, 40, 24)
        
        self.create_theme_toggle(layout)
        
        self.score = 0
        hud_layout = QHBoxLayout()

        self.lives_label = QLabel("LIVES: ❤️❤️❤️", self)
        self.lives_label.setFont(QFont(self.arcade_family, 9))
        self.lives_label.setStyleSheet("color: #22d3ee; background: transparent;")

        self.score_label = QLabel("SCORE: 00000", self)
        self.score_label.setFont(QFont(self.arcade_family, 9))
        self.score_label.setStyleSheet("color: #22d3ee; background: transparent;")
        
        rank_lbl = QLabel(f"RANK: {self.get_rank_title()}", self)
        rank_lbl.setFont(QFont(self.arcade_family, 9))
        rank_lbl.setStyleSheet("color: #ff00ff; background: transparent;")

        hud_layout.addWidget(self.lives_label)
        hud_layout.addStretch()
        hud_layout.addWidget(rank_lbl)
        hud_layout.addStretch()
        hud_layout.addWidget(self.score_label)
        layout.addLayout(hud_layout)
        
        header_container = QWidget(self)
        header_container.setStyleSheet("border: 2px solid #ff00ff; background: transparent; padding: 6px;")
        hc_layout = QVBoxLayout(header_container)
        hc_layout.setContentsMargins(0, 0, 0, 0)

        header = QLabel("RECALL THE ORDER!", self)
        header.setObjectName("Header")
        header.setFont(QFont(self.arcade_family, 26))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hc_layout.addWidget(header)
        layout.addWidget(header_container)

        subtitle = QLabel("TYPE EACH WORD FROM MEMORY", self)
        subtitle.setFont(QFont(self.arcade_family, 9))
        subtitle.setStyleSheet("color: #1e293b; background: transparent; letter-spacing: 3px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        grid_widget = QWidget(self)
        grid_layout = QGridLayout(grid_widget)
        
        row, col = 0, 0
        from PyQt6.QtWidgets import QSizePolicy
        for i, word_data in enumerate(self.words):
            word = word_data["word"]
            cell = QWidget(self)
            cell.setStyleSheet("background: transparent;")
            cell_layout = QVBoxLayout(cell)
            cell_layout.setContentsMargins(0, 12, 0, 0)
            cell_layout.setSpacing(5)

            # number badge
            badge = QLabel(f"{i+1:02d}", self)
            badge.setFont(QFont(self.arcade_family, 8))
            color = NEON_COLORS[i % 4]
            badge.setStyleSheet(f"color: {color}; background: transparent;")
            cell_layout.addWidget(badge)

            input_field = SpeakingLineEdit(word, self)
            input_field.setPlaceholderText("_ " * len(word))
            input_field.setFont(QFont(self.arcade_family, 20))
            input_field.setAlignment(Qt.AlignmentFlag.AlignCenter)
            input_field.setMinimumHeight(120)
            input_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            input_field.setStyleSheet(
                f"background-color: #000; border: 3px solid {color}; "
                f"border-radius: 2px; color: #ff00ff; letter-spacing: 4px;"
            )
            input_field.returnPressed.connect(lambda idx=i: self.check_answer(idx))
            input_field.installEventFilter(self)
            cell_layout.addWidget(input_field)

            btn_layout = QHBoxLayout()
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(5)

            # 🔊 Voice replay button — NoFocus so it NEVER steals focus from inputs
            replay_btn = QPushButton("🔊")
            replay_btn.setFont(QFont(self.arcade_family, 10))
            replay_btn.setFixedHeight(28)
            replay_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # KEY FIX: prevents focus-stealing
            replay_btn.setStyleSheet(
                f"border: 1px solid {color}; color: {color};"
                "background-color: #0a0a0a; letter-spacing: 2px; margin-top: 2px;"
            )
            self.replay_buttons.append(replay_btn)
            btn_layout.addWidget(replay_btn)

            # 🐢 Snail button for slow replay
            snail_btn = QPushButton("🐢")
            snail_btn.setFont(QFont(self.arcade_family, 10))
            snail_btn.setFixedHeight(28)
            snail_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            snail_btn.setStyleSheet(
                f"border: 1px solid {color}; color: {color};"
                "background-color: #0a0a0a; letter-spacing: 2px; margin-top: 2px;"
            )
            
            if not hasattr(self, 'snail_buttons'):
                self.snail_buttons = []
            self.snail_buttons.append(snail_btn)
            btn_layout.addWidget(snail_btn)
            
            cell_layout.addLayout(btn_layout)

            # progress tick
            tick = QWidget(self)
            tick.setFixedHeight(4)
            tick.setStyleSheet("background-color: #111111; border: none;")
            tick.setObjectName(f"tick_{i}")
            cell_layout.addWidget(tick)

            grid_layout.addWidget(cell, row, col)
            self.inputs.append(input_field)
            col += 1
            if col > 3:
                col = 0
                row += 1

        # Wire up replay buttons NOW that self.replay_buttons is fully populated
        for i, (btn, word_data) in enumerate(zip(self.replay_buttons, self.words)):
            w = word_data["word"]
            sentence = word_data.get("sentence", "")
            btn_color = btn.styleSheet().split("color: ")[1].split(";")[0].strip()
            
            btn.clicked.connect(
                lambda _, b=btn, ww=w, ss=sentence, bc=btn_color: self._on_replay_clicked(b, ww, ss, bc)
            )
            
            snail_btn = self.snail_buttons[i]
            snail_btn.clicked.connect(
                lambda _, b=snail_btn, ww=w, ss=sentence, bc=btn_color: self._on_replay_clicked(b, ww, ss, bc, slow=True)
            )
        
        grid_layout.setSpacing(18)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(grid_widget)
        
        status_bar = QHBoxLayout()
        hint_lbl = QLabel("▶▶ PRESS ENTER TO CONFIRM ◀◀", self)
        hint_lbl.setFont(QFont(self.arcade_family, 6))
        hint_lbl.setStyleSheet("color: #1e293b; background: transparent;")

        self.correct_count_lbl = QLabel(f"0 / {len(self.words)} CORRECT", self)
        self.correct_count_lbl.setFont(QFont(self.arcade_family, 9))
        self.correct_count_lbl.setStyleSheet("color: #22d3ee; background: transparent;")

        status_bar.addWidget(hint_lbl)
        status_bar.addStretch()
        status_bar.addWidget(self.correct_count_lbl)
        layout.addLayout(status_bar)

        QTimer.singleShot(500, self.start_first_word)

    def start_first_word(self):
        if self.inputs:
            self.inputs[0].setFocus()

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        if event.type() == QEvent.Type.FocusIn:
            if hasattr(self, 'inputs') and obj in self.inputs:
                idx = self.inputs.index(obj)
                rem = max(0, 3 - self.attempts[idx])
                self.lives_label.setText("LIVES: " + "❤️" * rem + "💔" * (3 - rem))
        return super().eventFilter(obj, event)

    def check_answer(self, index):
        user_text = self.inputs[index].text().strip().upper()
        correct_word = self.words[index]["word"].upper()
        if user_text == correct_word:
            self.earned_seconds += 300 # roadmap sync: +5 mins
            self.inputs[index].setEnabled(False)
            self.inputs[index].setStyleSheet("background-color: #113311; border: 3px solid #4ade80; color: #4ade80; letter-spacing: 4px;")
            
            self.inputs[index].glow.setColor(QColor("#4ade80"))
            self.inputs[index].glow.setBlurRadius(15)

            play_audio("Correct")
            
            self.score += 100
            self.score_label.setText(f"SCORE: {self.score:05d}")
            
            correct_so_far = sum(1 for i, inp in enumerate(self.inputs) if not inp.isEnabled() and self.attempts[i] < 3)
            self.correct_count_lbl.setText(f"{correct_so_far} / {len(self.words)} CORRECT")
            
            tick = self.findChild(QWidget, f"tick_{index}")
            if tick:
                tick.setStyleSheet("background-color: #4ade80; border: none;")
                t_glow = QGraphicsDropShadowEffect(tick)
                t_glow.setBlurRadius(8); t_glow.setColor(QColor("#4ade80")); t_glow.setOffset(0,0)
                tick.setGraphicsEffect(t_glow)
            
            self.show_score_popup(self.inputs[index], "+100")
            
            self.combo_streak += 1
            if self.combo_streak >= 3:
                self.show_score_popup(self.inputs[index], f"COMBO x{self.combo_streak}!", "#ff00ff")
                # Removed combo_pulse flash as requested
            
            # Add to session report
            self.session_report.append({"word": correct_word, "status": "MASTERED", "color": "#4ade80"})

            if all(not inp.isEnabled() for inp in self.inputs):
                self.deposit_time(self.earned_seconds)
                self.finish_recall()
            else:
                for i in range(len(self.inputs)):
                    if self.inputs[i].isEnabled():
                        self.inputs[i].setFocus()
                        break
        else:
            self.earned_seconds = max(0, self.earned_seconds - 300) # roadmap sync: -5 min
            self.combo_streak = 0
            
            self.attempts[index] += 1
            rem = max(0, 3 - self.attempts[index])
            self.lives_label.setText("LIVES: " + "❤️" * rem + "💔" * (3 - rem))

            if self.attempts[index] >= 3:
                # Track failure in report
                self.session_report.append({"word": self.words[index]["word"], "status": "FAILED", "color": "#ef4444"})
                
                widget = self.inputs[index]
                widget.setText(correct_word)
                widget.setStyleSheet("background-color: #2d0a0a; border: 3px solid #ef4444; color: #ef4444; letter-spacing: 4px;")
                widget.setEnabled(False)
                play_audio(f"The correct spelling is {correct_word}")
                
                correct_so_far = sum(1 for i, inp in enumerate(self.inputs) if not inp.isEnabled() and self.attempts[i] < 3)
                self.correct_count_lbl.setText(f"{correct_so_far} / {len(self.words)} CORRECT")
                
                tick = self.findChild(QWidget, f"tick_{index}")
                if tick:
                    tick.setStyleSheet("background-color: #ef4444; border: none;")
                    t_glow = QGraphicsDropShadowEffect(tick)
                    t_glow.setBlurRadius(8); t_glow.setColor(QColor("#ef4444")); t_glow.setOffset(0,0)
                    tick.setGraphicsEffect(t_glow)

                if all(not inp.isEnabled() for inp in self.inputs):
                    self.deposit_time(self.earned_seconds)
                    QTimer.singleShot(2000, self.finish_recall)
                else:
                    for i in range(len(self.inputs)):
                        if self.inputs[i].isEnabled():
                            QTimer.singleShot(2000, self.inputs[i].setFocus)
                            break
            else:
                # Track failure in report as RETRY
                self.session_report.append({"word": self.words[index]["word"], "status": "RETRY", "color": "#facc15"})
                
                widget = self.inputs[index]
                original_style = widget.styleSheet()
                widget.setStyleSheet("border: 3px solid #ef4444; background-color: #2d0a0a; color: #ef4444; letter-spacing: 4px;")
                QTimer.singleShot(400, lambda w=widget, s=original_style: w.setStyleSheet(s))
                
                self.wobble(widget)
                self.screen_shake()
                play_audio("Try again")

    def finish_recall(self):
        self.parent_window.session_report = self.session_report # Pass report to main window
        self.parent_window.start_scrambled_phase(self.words)

    def deposit_time(self, seconds):
        # ISSUE-05 FIX: clamp to >= 0 (same as ScrambledPhase)
        try:
            current = secure_load_time(TIME_BANK_FILE)
            secure_save_time(max(0, current + seconds), TIME_BANK_FILE)
        except Exception as e:
            print(f"[RecallScene] Failed to deposit time: {e}")

# --- PHASE 3 ---
class ScrambledPhase(BaseScene):
    def __init__(self, parent_window, words):
        super().__init__(parent_window)
        self.words = words.copy()
        random.shuffle(self.words)
        self.current_index = 0
        self.hints_used = 0
        self.combo_streak = 0
        self.session_report = getattr(parent_window, "session_report", []) # Maintain report history
        
        try:
            with open(USER_PROGRESS_FILE, "r") as f:
                self.progress_data = json.load(f)
        except:
            self.progress_data = {"mastered_words": [], "learning_pool": {}, "current_level": "Grade_4"}
            
        self.initUI()
        self.apply_current_theme()
        self.setup_scanline()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(40, 16, 40, 24)
        self.layout = layout
        
        self.create_theme_toggle(self.layout)
        
        rank_lbl = QLabel(f"RANK: {self.get_rank_title()}", self)
        rank_lbl.setFont(QFont(self.arcade_family, 9))
        rank_lbl.setStyleSheet("color: #ff00ff; background: transparent;")
        self.layout.addWidget(rank_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.layout.addStretch(1)   # push content down from top

        self.progress_label = QLabel(self)
        self.progress_label.setFont(QFont(self.arcade_family, 16))
        self.progress_label.setStyleSheet("color: #22d3ee; background: transparent;")
        self.layout.addWidget(self.progress_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.scrambled_display = QLabel(self)
        self.scrambled_display.setFont(QFont(self.arcade_family, 52))
        self.scrambled_display.setStyleSheet("color: #facc15; letter-spacing: 15px; background: transparent;")
        
        sd_glow = QGraphicsDropShadowEffect(self.scrambled_display)
        sd_glow.setBlurRadius(20)
        sd_glow.setColor(QColor("#facc15"))
        sd_glow.setOffset(0, 0)
        self.scrambled_display.setGraphicsEffect(sd_glow)
        
        self.layout.addWidget(self.scrambled_display, alignment=Qt.AlignmentFlag.AlignCenter)

        self.input_field = QLineEdit(self)
        self.input_field.setFont(QFont(self.arcade_family, 24))
        self.input_field.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_field.setStyleSheet("background-color: #000000; border: 3px solid #ff00ff; color: #ff00ff; max-width: 400px;")
        
        aglow = QGraphicsDropShadowEffect(self.input_field)
        aglow.setBlurRadius(15)
        aglow.setColor(QColor("#ff00ff"))
        aglow.setOffset(0, 0)
        self.input_field.setGraphicsEffect(aglow)

        self.input_field.textChanged.connect(lambda t: self.input_field.setText(t.upper()) if t != t.upper() else None)
        
        self.input_field.returnPressed.connect(self.submit_answer)
        self.layout.addWidget(self.input_field, alignment=Qt.AlignmentFlag.AlignCenter)

        self.hint_tokens = QLabel("HINTS: ●●●", self)
        self.hint_tokens.setFont(QFont(self.arcade_family, 8))
        self.hint_tokens.setStyleSheet("color: #facc15; background: transparent;")
        self.layout.addWidget(self.hint_tokens, alignment=Qt.AlignmentFlag.AlignCenter)

        action_layout = QHBoxLayout()
        action_layout.setSpacing(20)
        action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.hint_btn = QPushButton("[H] HINT  -1 MIN", self)
        self.hint_btn.setObjectName("ActionBtn")
        self.hint_btn.setFont(QFont(self.arcade_family, 8))
        
        hb_glow = QGraphicsDropShadowEffect(self.hint_btn)
        hb_glow.setBlurRadius(0)
        hb_glow.setColor(QColor("#facc15"))
        hb_glow.setOffset(4, 4)
        self.hint_btn.setGraphicsEffect(hb_glow)
        self.hint_btn.clicked.connect(self.use_hint)

        self.sound_btn = QPushButton("🔊 REPLAY AUDIO", self)
        self.sound_btn.setObjectName("ActionBtn")
        self.sound_btn.setFont(QFont(self.arcade_family, 8))
        
        sb_glow = QGraphicsDropShadowEffect(self.sound_btn)
        sb_glow.setBlurRadius(0)
        sb_glow.setColor(QColor("#22d3ee"))
        sb_glow.setOffset(4, 4)
        self.sound_btn.setGraphicsEffect(sb_glow)
        self.sound_btn.clicked.connect(self.replay_audio)
        
        action_layout.addWidget(self.hint_btn)
        action_layout.addWidget(self.sound_btn)
        
        self.layout.addLayout(action_layout)
        self.layout.addStretch(1)   # push content up from bottom

        self.load_word()

    def load_word(self):
        self.input_field.clear()
        self.input_field.setEnabled(True)
        self.input_field.setStyleSheet("background-color: #000000; border: 3px solid #ff00ff; color: #ff00ff; max-width: 400px;")
        self.input_field.setFocus()
        self.hints_used = 0
        self.incorrect_tries = 0
        if hasattr(self, 'hint_tokens'):
            self.hint_tokens.setText("HINTS: ●●●")
        
        word_data = self.words[self.current_index]
        self.scrambled_word = generate_scrambled(word_data["word"])
        self.scrambled_display.setText(self.scrambled_word)
        self.progress_label.setText(f"WORD {self.current_index + 1} OF {len(self.words)}")

        play_audio(f"Spell {word_data['word']}. <PAUSE> {word_data['sentence']}")

    def replay_audio(self):
        word_data = self.words[self.current_index]
        play_audio(f"Spell {word_data['word']}. <PAUSE> {word_data['sentence']}")

    def submit_answer(self):
        answer = self.input_field.text().strip().upper()
        correct_word = self.words[self.current_index]["word"].upper()

        if answer == correct_word:
            reward = 300 - (self.hints_used * 60) 
            self.deposit_time(reward)
            update_mastery(correct_word, True, self.hints_used > 0, self.progress_data)
            
            self.combo_streak += 1
            if self.combo_streak >= 2:
                self.show_score_popup(self.input_field, f"COMBO x{self.combo_streak}!", "#ff00ff")
                # Removed combo_pulse flash as requested

            self.show_score_popup(self.input_field, f"+{reward}s", "#facc15")
            play_audio("Correct")
            self.next_word()
        else:
            self.deposit_time(-180) 
            self.combo_streak = 0
            update_mastery(correct_word, False, False, self.progress_data)
            
            self.incorrect_tries += 1
            
            if self.incorrect_tries >= 3:
                # 3 Strikes: Show correct word, turn red, and move on
                self.input_field.setText(correct_word)
                self.input_field.setStyleSheet("background-color: #2d0a0a; border: 3px solid #ef4444; color: #ef4444; max-width: 400px;")
                self.input_field.setEnabled(False)
                play_audio(f"The correct spelling is {correct_word}")
                # Move to next word after a 2 second delay to let the user see the correct spelling
                QTimer.singleShot(2000, self.next_word)
            else:
                # Flash scrambled display
                self.scrambled_display.setStyleSheet("color: #ef4444; letter-spacing: 15px; background: transparent;")
                QTimer.singleShot(300, lambda: self.scrambled_display.setStyleSheet("color: #facc15; letter-spacing: 15px; background: transparent;"))
                
                self.wobble(self.input_field)
                self.screen_shake()
                play_audio("Try again")

    def use_hint(self):
        """
        Progressive hint — each tap reveals one more letter.
        Tap 1: first 2 chars revealed
        Tap 2: first 3 chars revealed
        Tap 3: first 4 chars (or full word if short) revealed
        """
        correct = self.words[self.current_index]["word"]
        # Reveal progressively more characters with each hint
        reveal_up_to = min(2 + self.hints_used, len(correct))
        self.hints_used += 1

        # Build the progressively revealed display
        revealed = correct[:reveal_up_to]
        remainder = self.scrambled_word[reveal_up_to:] if reveal_up_to < len(self.scrambled_word) else ""
        self.scrambled_display.setText(revealed + remainder)

        # Update hint tokens
        max_hints = 3
        remaining = max(0, max_hints - self.hints_used)
        dots = "●" * remaining + "○" * self.hints_used
        self.hint_tokens.setText(f"HINTS: {dots}")

        if self.hints_used >= max_hints:
            self.hint_btn.setEnabled(False)

    def deposit_time(self, seconds):
        try:
            current = secure_load_time(TIME_BANK_FILE)
            secure_save_time(max(0, current + seconds), TIME_BANK_FILE)
        except Exception as e:
            print(f"[ScrambledPhase] Failed to deposit time: {e}")


    def next_word(self):
        self.current_index += 1
        if self.current_index < len(self.words):
            self.load_word()
        else:
            save_progress(self.progress_data)
            self.parent_window.show_final_results()

# --- PHASE 4 ---
class SummaryScene(BaseScene):
    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.unlock_countdown = 10
        self.earned_time = self.read_final_time()
        self.initUI()
        self.apply_current_theme()
        self.setup_scanline()
        self.announce_success()

    def read_final_time(self):
        try:
            return secure_load_time(TIME_BANK_FILE)
        except Exception as e:
            print(f"[SummaryScene] Failed to read final time: {e}")
            return 0

    def create_report_table(self):
        """Creates a professional sleek report card."""
        report = getattr(self.parent_window, 'session_report', [])
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: rgba(10, 10, 10, 150);
                border: 1px solid rgba(34, 211, 238, 80);
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(container)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 15, 15, 15)
        
        header_layout = QHBoxLayout()
        header_icon = QLabel("📊")
        header_icon.setStyleSheet("background: transparent; border: none;")
        header_text = QLabel("SESSION PERFORMANCE REPORT")
        header_text.setFont(QFont(self.arcade_family, 10))
        header_text.setStyleSheet("color: #22d3ee; background: transparent; border: none; letter-spacing: 2px;")
        header_layout.addWidget(header_icon)
        header_layout.addWidget(header_text)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Divider
        line = QFrame(self)
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: rgba(34, 211, 238, 50); border: none;")
        line.setFixedHeight(1)
        layout.addWidget(line)
        
        # Grid for report items (2 columns)
        grid_widget = QWidget()
        grid_widget.setStyleSheet("background: transparent; border: none;")
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setHorizontalSpacing(30)
        grid_layout.setVerticalSpacing(6)
        
        for i, item in enumerate(report):
            w_lbl = QLabel(item["word"])
            w_lbl.setFont(QFont(self.arcade_family, 8))
            w_lbl.setStyleSheet("color: #ffffff; background: transparent; border: none;")
            
            s_lbl = QLabel(item["status"])
            s_lbl.setFont(QFont(self.arcade_family, 8))
            s_lbl.setStyleSheet(f"color: {item['color']}; background: transparent; border: none;")
            
            row = i // 2
            col = (i % 2) * 2
            
            grid_layout.addWidget(w_lbl, row, col)
            grid_layout.addWidget(s_lbl, row, col + 1, alignment=Qt.AlignmentFlag.AlignRight)
            
        layout.addWidget(grid_widget)
        return container

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 30, 40, 30)
        
        self.create_theme_toggle(layout)

        # -- star burst --
        import random as _r
        import math as _m
        def spawn_stars():
            for _ in range(40):
                star = QLabel(_r.choice(["*","+","✦","★"]), self)
                star.setFont(QFont(self.arcade_family, _r.randint(10,24)))
                star.setStyleSheet(f"color:{_r.choice(NEON_COLORS)};background:transparent;")
                
                center = QPoint(self.width() // 2, self.height() // 2)
                star.move(center)
                star.show()
                
                anim = QPropertyAnimation(star, b"pos", self)
                anim.setDuration(_r.randint(1500,3000))
                
                angle = _r.uniform(0, 2 * _m.pi)
                dist  = _r.randint(300, 800)
                end_x = int(center.x() + _m.cos(angle) * dist)
                end_y = int(center.y() + _m.sin(angle) * dist)
                
                anim.setStartValue(center)
                anim.setEndValue(QPoint(end_x, end_y))
                anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                anim.finished.connect(star.deleteLater)
                
                if not hasattr(self,'_star_anims'): self._star_anims=[]
                self._star_anims.append(anim)
                QTimer.singleShot(_r.randint(0,800), anim.start)
        QTimer.singleShot(250, spawn_stars)

        # Main Container to hold everything nicely
        main_container = QWidget()
        main_container.setMaximumWidth(800)
        main_layout = QVBoxLayout(main_container)
        main_layout.setSpacing(25)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(main_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # -- TITLE --
        self.title = QLabel("MISSION COMPLETE", self)
        self.title.setFont(QFont(self.arcade_family, 36))
        self.title.setStyleSheet("color: #ff00ff; background: transparent; letter-spacing: 5px;")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_glow = QGraphicsDropShadowEffect(self.title)
        title_glow.setBlurRadius(25); title_glow.setColor(QColor("#ff00ff")); title_glow.setOffset(0,0)
        self.title.setGraphicsEffect(title_glow)
        main_layout.addWidget(self.title)

        # -- Typewriter "NEW HIGH SCORE!" --
        self._hs_full = "► EXCELLENT PERFORMANCE ◄"
        self._hs_idx  = 0
        self.hs_label = QLabel("", self)
        self.hs_label.setFont(QFont(self.arcade_family, 10))
        self.hs_label.setStyleSheet("color: #4ade80; background: transparent; letter-spacing: 3px;")
        self.hs_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.hs_label)
        self.hs_timer = QTimer(self)
        self.hs_timer.timeout.connect(self._type_hs)
        self.hs_timer.start(50)

        # -- DASHBOARD PANEL --
        dashboard = QWidget()
        dashboard.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 180);
                border: 2px solid #22d3ee;
                border-radius: 12px;
            }
        """)
        dash_glow = QGraphicsDropShadowEffect(dashboard)
        dash_glow.setBlurRadius(30); dash_glow.setColor(QColor("#22d3ee")); dash_glow.setOffset(0,0)
        dashboard.setGraphicsEffect(dash_glow)
        
        dash_layout = QVBoxLayout(dashboard)
        dash_layout.setContentsMargins(30, 25, 30, 25)
        dash_layout.setSpacing(20)
        
        # Horizontal layout for Time Box & Stats
        top_dash_layout = QHBoxLayout()
        top_dash_layout.setSpacing(40)
        
        # Time Box
        time_box = QWidget()
        time_box.setStyleSheet("background: transparent; border: 1px solid rgba(74, 222, 128, 100); border-radius: 8px;")
        tb_layout = QVBoxLayout(time_box)
        tb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tb_layout.setContentsMargins(20, 15, 20, 15)
        
        earned_lbl = QLabel("⏱ TOTAL PLAYTIME")
        earned_lbl.setFont(QFont(self.arcade_family, 8))
        earned_lbl.setStyleSheet("color: #4ade80; background: transparent; border: none; letter-spacing: 2px;")
        earned_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tb_layout.addWidget(earned_lbl)
        
        mins_val, secs_val = divmod(self.earned_time, 60)
        self.time_big = QLabel(f"{mins_val:02d}:{secs_val:02d}")
        self.time_big.setFont(QFont(self.arcade_family, 48))
        self.time_big.setStyleSheet("color: #4ade80; background: transparent; border: none;")
        self.time_big.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tb_layout.addWidget(self.time_big)
        
        top_dash_layout.addWidget(time_box, stretch=1)
        
        # Stats List
        stats_widget = QWidget()
        stats_widget.setStyleSheet("background: transparent; border: none;")
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.setSpacing(12)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        
        stats = [
            ("PHASE 1 BONUS",  f"+{mins_val*60}s",     "#22d3ee"),
            ("PHASE 2 BONUS",  "+240s",                 "#22d3ee"),
            ("PHASE 3 TOTAL",  f"+{secs_val}s",         "#fb923c"),
            ("TOTAL TIME",     f"{mins_val}m {secs_val}s", "#4ade80"),
        ]
        
        for label, val, color in stats:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setFont(QFont(self.arcade_family, 8))
            lbl.setStyleSheet("color: #94a3b8; background: transparent; border: none;")
            val_lbl = QLabel(val)
            val_lbl.setFont(QFont(self.arcade_family, 10))
            val_lbl.setStyleSheet(f"color: {color}; background: transparent; border: none;")
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(val_lbl)
            stats_layout.addLayout(row)
            
            if label == "PHASE 3 TOTAL":
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setStyleSheet("background-color: rgba(255, 255, 255, 30); border: none;")
                line.setFixedHeight(1)
                stats_layout.addWidget(line)
                
        top_dash_layout.addWidget(stats_widget, stretch=2)
        dash_layout.addLayout(top_dash_layout)
        
        # Add the Report Card
        report_widget = self.create_report_table()
        dash_layout.addWidget(report_widget)
        
        main_layout.addWidget(dashboard)

        # -- Bottom Status Bar (Hearts & Countdown) --
        status_bar = QHBoxLayout()
        
        # Hearts
        self.hearts_widget = QWidget()
        h_layout = QHBoxLayout(self.hearts_widget)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.hearts = []
        for _ in range(3):
            heart = QLabel("❤️")
            heart.setFont(QFont("Arial", 16))
            heart.setStyleSheet("background: transparent;")
            h_layout.addWidget(heart)
            self.hearts.append(heart)
        status_bar.addWidget(self.hearts_widget)
        
        self.heart_state = 0
        self.heart_timer = QTimer(self)
        self.heart_timer.timeout.connect(self.animate_hearts)
        self.heart_timer.start(400)
        
        status_bar.addStretch()
        
        # Countdown
        self.countdown_label = QLabel(f"SYSTEM UNLOCK IN {self.unlock_countdown}...")
        self.countdown_label.setFont(QFont(self.arcade_family, 10))
        self.countdown_label.setStyleSheet("color: #facc15; background: transparent; letter-spacing: 2px;")
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        status_bar.addWidget(self.countdown_label)
        
        main_layout.addLayout(status_bar)

        self.blink_timer = QTimer(self)
        self._bl_vis = True
        def blink_cd():
            self._bl_vis = not self._bl_vis
            self.countdown_label.setStyleSheet(
                f"color: #facc15; background: transparent; letter-spacing: 2px; opacity: {'1.0' if self._bl_vis else '0.0'};"
            )
        self.blink_timer.timeout.connect(blink_cd)
        self.blink_timer.start(500)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick_countdown)
        self.timer.start(1000)

    def _type_hs(self):
        if self._hs_idx <= len(self._hs_full):
            self.hs_label.setText(self._hs_full[:self._hs_idx])
            self._hs_idx += 1
        else:
            self.hs_timer.stop()

    def animate_hearts(self):
        for i, heart in enumerate(self.hearts):
            if i <= self.heart_state % len(self.hearts):
                heart.setVisible(True)
            else:
                heart.setVisible(False)
        self.heart_state += 1

    def announce_success(self):
        mins = self.earned_time // 60
        play_audio(f"Great Job! Spelling module complete. You have earned {mins} minutes of playtime. Unlocking system!")

    def tick_countdown(self):
        self.unlock_countdown -= 1
        if self.unlock_countdown > 0:
            self.countdown_label.setText(f"SYSTEM UNLOCK IN {self.unlock_countdown}...")
        else:
            self.blink_timer.stop()
            self.countdown_label.setVisible(True)
            self.timer.stop()
            self.parent_window.trigger_playtime()