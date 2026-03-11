import json
import random
from modules.audio import play_audio

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, 
                             QPushButton, QGraphicsDropShadowEffect, QLineEdit)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QEasingCurve, QVariantAnimation
from PyQt6.QtGui import QFont, QColor, QFontDatabase, QPainter, QPen
from PyQt6.QtWidgets import QFrame, QSizePolicy
from modules.game_logic import generate_scrambled, update_mastery, get_next_words, save_progress

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

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        grid_pen = QPen(QColor(255, 255, 255, 5)) 
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        
        for x in range(0, self.width(), 32):
            painter.drawLine(x, 0, x, self.height())
            
        for y in range(0, self.height(), 32):
            painter.drawLine(0, y, self.width(), y)
        
    def apply_current_theme(self):
        self.setStyleSheet(DARK_THEME if self.is_dark else LIGHT_THEME)

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
        self.scanline = QLabel(self)
        self.scanline.setStyleSheet("background-color: rgba(34, 211, 238, 20); border-bottom: 2px solid rgba(34, 211, 238, 80);")
        self.scanline.setFixedHeight(12)
        self.scanline.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.scanline.show()
        self.scanline.raise_()

        self.scan_anim = QPropertyAnimation(self.scanline, b"pos", self)
        self.scan_anim.setDuration(3000)
        self.scan_anim.setStartValue(QPoint(0, -20))
        self.scan_anim.setEndValue(QPoint(0, 1080))
        self.scan_anim.setLoopCount(-1)
        self.scan_anim.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'scanline'):
            self.scanline.setFixedWidth(self.width())
            if self.height() > 0:
                self.scan_anim.setEndValue(QPoint(0, self.height() + 20))

class MemorizationScene(BaseScene): 
    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.time_left = 300
        self.load_data()
        self.initUI()
        self.apply_current_theme()
        self.setup_scanline()

    def load_data(self):
        try:
            with open("data/user_progress.json", "r") as f:
                self.progress_data = json.load(f)
        except:
            self.progress_data = {"mastered_words": [], "learning_pool": {}, "current_level": "Grade_4"}
        
        self.words = get_next_words(self.progress_data, "assets/words.csv", count=12)

    def initUI(self):
        layout = QVBoxLayout(self)
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

        hud_layout.addWidget(lives_lbl)
        hud_layout.addStretch()
        hud_layout.addWidget(score_lbl)
        layout.addLayout(hud_layout)
        
        header_container = QWidget(self)
        header_container.setStyleSheet("border: 2px solid #ff00ff; background: transparent; padding: 4px;")
        hc_layout = QVBoxLayout(header_container)
        hc_layout.setContentsMargins(0, 0, 0, 0)

        header = QLabel("SPELL BLASTER", self)
        header.setObjectName("Header")
        header.setFont(QFont(self.arcade_family, 32))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hc_layout.addWidget(header)
        
        layout.addWidget(header_container)
        
        subtitle = QLabel("INSERT COIN TO CONTINUE", self)
        subtitle.setFont(QFont(self.arcade_family, 9))
        subtitle.setStyleSheet("color: #334155; background: transparent; letter-spacing: 3px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
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

        self.progress_blocks_widget = QWidget(self.timer_container)
        self.progress_blocks_widget.setStyleSheet("border: none;")
        pb_layout = QHBoxLayout(self.progress_blocks_widget)
        pb_layout.setSpacing(5)
        self.progress_blocks = []
        for i in range(10):
            block = QWidget()
            block.setFixedSize(20, 20)
            block.setStyleSheet("background-color: #4ade80;") # Green
            pb_layout.addWidget(block)
            self.progress_blocks.append(block)
        tc_layout.addWidget(self.progress_blocks_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.timer_container, alignment=Qt.AlignmentFlag.AlignCenter)

        grid_widget = QWidget(self)
        grid_layout = QGridLayout(grid_widget)
        
        import math
        self.cards = []
        row, col = 0, 0
        for i, word in enumerate(self.words):
            card = self.create_word_card(word, i)
            # Center the row dynamically
            if i >= len(self.words) - (len(self.words) % 4) and len(self.words) % 4 != 0:
                offset_col = col + math.floor((4 - (len(self.words) % 4)) / 2)
                grid_layout.addWidget(card, row, offset_col)
            else:
                grid_layout.addWidget(card, row, col)
            
            self.cards.append(card)
            col += 1
            if col > 3:
                col = 0
                row += 1
        
        layout.addWidget(grid_widget)

        self.ready_btn = QPushButton("RECALL MODE", self)
        self.ready_btn.setObjectName("ActionBtn")
        self.ready_btn.setFont(QFont(self.arcade_family, 16))
        
        # ActionBtn 3D DropShadow
        ab_glow = QGraphicsDropShadowEffect(self.ready_btn)
        ab_glow.setBlurRadius(0)
        ab_glow.setColor(QColor("#facc15"))
        ab_glow.setOffset(4, 4)
        self.ready_btn.setGraphicsEffect(ab_glow)

        self.ready_btn.clicked.connect(self.finish_memorization)
        
        self.press_enter_lbl = QLabel("▶▶ PRESS ENTER ◀◀", self)
        self.press_enter_lbl.setFont(QFont(self.arcade_family, 8))
        self.press_enter_lbl.setStyleSheet("color: #facc15; background: transparent;")
        self.press_enter_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.press_enter_lbl.setFixedHeight(30)
        layout.addWidget(self.press_enter_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self._pe_visible = True
        def blink_pe():
            self._pe_visible = not self._pe_visible
            opacity = "1.0" if self._pe_visible else "0.0"
            self.press_enter_lbl.setStyleSheet(
                f"color: #facc15; background: transparent; opacity: {opacity};"
            )

        self.press_enter_timer = QTimer(self)
        self.press_enter_timer.timeout.connect(blink_pe)
        self.press_enter_timer.start(500)

        layout.addWidget(self.ready_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.study_timer = QTimer(self)
        self.study_timer.timeout.connect(self.update_timer)
        self.study_timer.start(1000)
        
        QTimer.singleShot(100, self.animate_cards_in)

    def create_word_card(self, word, index):
        btn = QPushButton(f"👾\n{word}")
        btn.setObjectName("WordCard") 
        btn.setMinimumHeight(80)
        btn.setSizePolicy(QPushButton.sizePolicy(btn).horizontalPolicy().Expanding,
                          QPushButton.sizePolicy(btn).verticalPolicy().Fixed)
        color = NEON_COLORS[index % 4]
        default_style = f"QPushButton#WordCard {{ border: 3px solid {color}; background-color: #000000; color: #FFFFFF; padding: 15px; border-radius: 4px; }}"
        flash_style = f"QPushButton#WordCard {{ border: 3px solid {color}; background-color: #ffffff18; color: #FFFFFF; padding: 15px; border-radius: 4px; }}"
        btn.setStyleSheet(default_style)
        btn.setFont(QFont(self.arcade_family, 12))
        
        def on_click():
            play_audio(word)
            btn.setStyleSheet(flash_style)
            QTimer.singleShot(150, lambda: btn.setStyleSheet(default_style))
            
        btn.clicked.connect(on_click)
        glow = QGraphicsDropShadowEffect(btn)
        glow.setBlurRadius(15)
        glow.setColor(QColor(color))
        glow.setOffset(0, 0)
        btn.setGraphicsEffect(glow)
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
            blocks_to_show = int(self.time_left / 30)
            for i in range(10):
                self.progress_blocks[i].setVisible(i < blocks_to_show)
        else:
            self.finish_memorization()

    def finish_memorization(self):
        self.study_timer.stop()
        self.parent_window.start_recall_phase(self.words)

# --- PHASE 2 ---
class RecallScene(BaseScene):
    def __init__(self, parent_window, words):
        super().__init__(parent_window)
        self.words = words
        self.inputs = []
        self.attempts = [0] * len(words)
        self.earned_seconds = 0 
        self.initUI()
        self.apply_current_theme()
        self.setup_scanline()

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

        hud_layout.addWidget(self.lives_label)
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
        for i, word in enumerate(self.words):
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
            cell_layout.addWidget(input_field)

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

    def check_answer(self, index):
        user_text = self.inputs[index].text().strip().upper()
        if user_text == self.words[index].upper():
            self.earned_seconds += 120 # +2 mins
            self.inputs[index].setEnabled(False)
            self.inputs[index].setStyleSheet("background-color: #113311; border: 3px solid #4ade80; color: #4ade80;")
            
            self.inputs[index].glow.setColor(QColor("#4ade80"))
            self.inputs[index].glow.setBlurRadius(15)

            play_audio("Correct")
            
            self.score += 100
            self.score_label.setText(f"SCORE: {self.score:05d}")
            
            correct_so_far = sum(1 for inp in self.inputs if not inp.isEnabled())
            self.correct_count_lbl.setText(f"{correct_so_far} / {len(self.words)} CORRECT")
            
            tick = self.findChild(QWidget, f"tick_{index}")
            if tick:
                tick.setStyleSheet("background-color: #4ade80; border: none;")
                t_glow = QGraphicsDropShadowEffect(tick)
                t_glow.setBlurRadius(8); t_glow.setColor(QColor("#4ade80")); t_glow.setOffset(0,0)
                tick.setGraphicsEffect(t_glow)
            
            popup = QLabel("+100", self)
            popup.setFont(QFont(self.arcade_family, 12))
            popup.setStyleSheet("color: #4ade80; background: transparent;")
            popup.move(self.inputs[index].pos())
            popup.show()
            
            anim = QPropertyAnimation(popup, b"pos", self)
            anim.setDuration(600)
            anim.setStartValue(popup.pos())
            anim.setEndValue(popup.pos() - QPoint(0, 80))
            anim.finished.connect(popup.deleteLater)
            anim.start()
            
            if not hasattr(self, '_anims'): self._anims = []
            self._anims.append(anim)
            
            if all(not inp.isEnabled() for inp in self.inputs):
                self.deposit_time(self.earned_seconds)
                self.parent_window.start_scrambled_phase(self.words)
            else:
                for i in range(len(self.inputs)):
                    if self.inputs[i].isEnabled():
                        self.inputs[i].setFocus()
                        break
        else:
            self.earned_seconds = max(0, self.earned_seconds - 60) # -1 min
            
            widget = self.inputs[index]
            original_style = widget.styleSheet()
            widget.setStyleSheet("border: 3px solid #ef4444; background-color: #2d0a0a; color: #ef4444;")
            QTimer.singleShot(400, lambda w=widget, s=original_style: w.setStyleSheet(s))
            
            self.wobble_animation(widget)
            play_audio("Try again")

    def wobble_animation(self, widget):
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

    def deposit_time(self, seconds):
        try:
            with open("data/time_bank.txt", "r") as f:
                current = int(f.read().strip())
            with open("data/time_bank.txt", "w") as f:
                f.write(str(current + seconds))
        except:
            pass

# --- PHASE 3 ---
class ScrambledPhase(BaseScene):
    def __init__(self, parent_window, words):
        super().__init__(parent_window)
        self.words = words.copy()
        random.shuffle(self.words)
        self.current_index = 0
        self.hints_used = 0
        
        try:
            with open("data/user_progress.json", "r") as f:
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

        self.hint_btn = QPushButton("[H] HINT  -1 MIN", self)
        self.hint_btn.setObjectName("ActionBtn")
        self.hint_btn.setFont(QFont(self.arcade_family, 8))
        
        hb_glow = QGraphicsDropShadowEffect(self.hint_btn)
        hb_glow.setBlurRadius(0)
        hb_glow.setColor(QColor("#facc15"))
        hb_glow.setOffset(4, 4)
        self.hint_btn.setGraphicsEffect(hb_glow)

        self.hint_btn.clicked.connect(self.use_hint)
        self.layout.addWidget(self.hint_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addStretch(1)   # push content up from bottom

        self.load_word()

    def load_word(self):
        self.input_field.clear()
        self.input_field.setFocus()
        self.hints_used = 0
        if hasattr(self, 'hint_tokens'):
            self.hint_tokens.setText("HINTS: ●●●")
        self.scrambled_word = generate_scrambled(self.words[self.current_index])
        self.scrambled_display.setText(self.scrambled_word)
        self.progress_label.setText(f"WORD {self.current_index + 1} OF {len(self.words)}")

        play_audio(f"Spell {self.words[self.current_index]}")

    def submit_answer(self):
        answer = self.input_field.text().strip().upper()
        correct_word = self.words[self.current_index].upper()

        if answer == correct_word:
            reward = 300 - (self.hints_used * 60) 
            self.deposit_time(reward)
            update_mastery(correct_word, True, self.hints_used > 0, self.progress_data)
            play_audio("Correct")
            self.next_word()
        else:
            self.deposit_time(-180) 
            update_mastery(correct_word, False, False, self.progress_data)
            
            # Flash scrambled display
            self.scrambled_display.setStyleSheet("color: #ef4444; letter-spacing: 15px; background: transparent;")
            QTimer.singleShot(300, lambda: self.scrambled_display.setStyleSheet("color: #facc15; letter-spacing: 15px; background: transparent;"))
            
            self.wobble_input()
            play_audio("Try again")

    def use_hint(self):
        self.hints_used += 1
        correct = self.words[self.current_index]
        self.scrambled_display.setText(correct[:2] + self.scrambled_word[2:])
        dots = "●" * max(0, 3 - self.hints_used)
        self.hint_tokens.setText(f"HINTS: {dots}")

    def deposit_time(self, seconds):
        try:
            with open("data/time_bank.txt", "r") as f:
                current = int(f.read().strip())
            with open("data/time_bank.txt", "w") as f:
                f.write(str(max(0, current + seconds)))
        except:
            pass

    def wobble_input(self):
        anim = QPropertyAnimation(self.input_field, b"pos", self)
        anim.setDuration(50)
        curr = self.input_field.pos()
        anim.setKeyValueAt(0, curr)
        anim.setKeyValueAt(0.25, curr + QPoint(-15, 0))
        anim.setKeyValueAt(0.75, curr + QPoint(15, 0))
        anim.setKeyValueAt(1, curr)
        anim.setLoopCount(3)
        anim.start()
        self._wobble_anim = anim

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
            with open("data/time_bank.txt", "r") as f:
                return int(f.read().strip())
        except:
            return 0

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(40, 16, 40, 24)
        
        self.create_theme_toggle(layout)

        # ── star burst ──────────────────────────────────────
        import random as _r
        def spawn_stars():
            for _ in range(22):
                star = QLabel(_r.choice(["*","+","✦","★"]), self)
                star.setFont(QFont(self.arcade_family, _r.randint(10,20)))
                star.setStyleSheet(f"color:{_r.choice(NEON_COLORS)};background:transparent;")
                star.move(_r.randint(0,self.width()), _r.randint(0,self.height()))
                star.show()
                anim = QPropertyAnimation(star, b"pos", self)
                anim.setDuration(_r.randint(900,2000))
                anim.setStartValue(star.pos())
                anim.setEndValue(star.pos() - QPoint(0, 130))
                anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                anim.finished.connect(star.deleteLater)
                if not hasattr(self,'_star_anims'): self._star_anims=[]
                self._star_anims.append(anim)
                QTimer.singleShot(_r.randint(0,1000), anim.start)
        QTimer.singleShot(250, spawn_stars)

        # ── MISSION COMPLETE title ───────────────────────────
        self.title = QLabel("MISSION\nCOMPLETE!", self)
        self.title.setFont(QFont(self.arcade_family, 38))
        self.title.setStyleSheet("color: #ff00ff; background: transparent;")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_glow = QGraphicsDropShadowEffect(self.title)
        title_glow.setBlurRadius(20); title_glow.setColor(QColor("#ff00ff")); title_glow.setOffset(0,0)
        self.title.setGraphicsEffect(title_glow)
        layout.addWidget(self.title)

        # ── Typewriter "NEW HIGH SCORE!" ─────────────────────
        self._hs_full = "NEW HIGH SCORE!"
        self._hs_idx  = 0
        self.hs_label = QLabel("", self)
        self.hs_label.setFont(QFont(self.arcade_family, 10))
        self.hs_label.setStyleSheet("color: #4ade80; background: transparent;")
        self.hs_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.hs_label)
        self.hs_timer = QTimer(self)
        self.hs_timer.timeout.connect(self._type_hs)
        self.hs_timer.start(80)

        # ── TIMER PANEL ──────────────────────────────────────
        timer_panel = QWidget(self)
        timer_panel.setStyleSheet("""
            QWidget { background-color: #000000; border: 3px solid #22d3ee; }
        """)
        tp_glow = QGraphicsDropShadowEffect(timer_panel)
        tp_glow.setBlurRadius(25); tp_glow.setColor(QColor("#22d3ee")); tp_glow.setOffset(0,0)
        timer_panel.setGraphicsEffect(tp_glow)

        tp_outer = QVBoxLayout(timer_panel)
        tp_outer.setContentsMargins(20,16,20,16)
        tp_outer.setSpacing(14)

        panel_title = QLabel("⏱  TOTAL PLAYTIME EARNED", self)
        panel_title.setFont(QFont(self.arcade_family, 9))
        panel_title.setStyleSheet("color: #22d3ee; background: transparent; border: none; letter-spacing: 4px;")
        panel_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tp_outer.addWidget(panel_title)

        # horizontal row: big time display + stats
        row_widget = QWidget(self)
        row_widget.setStyleSheet("background: transparent; border: none;")
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0,0,0,0)
        row_layout.setSpacing(40)

        # BIG earned time display
        time_box = QWidget(self)
        time_box.setStyleSheet("background: transparent; border: 2px solid #4ade80;")
        tb_layout = QVBoxLayout(time_box)
        tb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tb_layout.setContentsMargins(20,16,20,16)

        earned_lbl = QLabel("EARNED", self)
        earned_lbl.setFont(QFont(self.arcade_family, 7))
        earned_lbl.setStyleSheet("color: #4ade80; background: transparent; border: none; letter-spacing: 3px;")
        earned_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tb_layout.addWidget(earned_lbl)

        mins_val, secs_val = divmod(self.earned_time, 60)
        self.time_big = QLabel(f"{mins_val:02d}:{secs_val:02d}", self)
        self.time_big.setFont(QFont(self.arcade_family, 56))
        self.time_big.setStyleSheet("color: #4ade80; background: transparent; border: none;")
        self.time_big.setAlignment(Qt.AlignmentFlag.AlignCenter)
        big_glow = QGraphicsDropShadowEffect(self.time_big)
        big_glow.setBlurRadius(20); big_glow.setColor(QColor("#4ade80")); big_glow.setOffset(0,0)
        self.time_big.setGraphicsEffect(big_glow)
        tb_layout.addWidget(self.time_big)

        mm_ss = QLabel("MM  :  SS", self)
        mm_ss.setFont(QFont(self.arcade_family, 7))
        mm_ss.setStyleSheet("color: #22d3ee; background: transparent; border: none; letter-spacing: 2px;")
        mm_ss.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tb_layout.addWidget(mm_ss)

        row_layout.addWidget(time_box)

        # Stats column
        stats_widget = QWidget(self)
        stats_widget.setStyleSheet("background: transparent; border: none;")
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.setSpacing(8)
        stats_layout.setContentsMargins(0,0,0,0)

        stats = [
            ("PHASE 1 BONUS",  f"+{mins_val*60}s",     "#22d3ee"),
            ("PHASE 2 BONUS",  "+240s",                 "#22d3ee"),
            ("PHASE 3 TOTAL",  f"+{secs_val}s",         "#fb923c"),
            ("TOTAL TIME",     f"{mins_val}m {secs_val}s", "#4ade80"),
        ]
        
        for label, val, color in stats:
            row = QHBoxLayout()
            lbl = QLabel(label, self)
            lbl.setFont(QFont(self.arcade_family, 7))
            lbl.setStyleSheet("color: #334155; background: transparent; border: none;")
            val_lbl = QLabel(val, self)
            val_lbl.setFont(QFont(self.arcade_family, 9))
            val_lbl.setStyleSheet(f"color: {color}; background: transparent; border: none;")
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(val_lbl)
            stats_layout.addLayout(row)

            # divider before TOTAL TIME
            if label == "PHASE 3 TOTAL":
                line = QFrame(self)
                line.setFrameShape(QFrame.Shape.HLine)
                line.setStyleSheet("color: #1e293b; background: #1e293b; border: none;")
                line.setFixedHeight(1)
                stats_layout.addWidget(line)

        row_layout.addWidget(stats_widget)
        row_layout.setStretch(0, 1)   # time_box gets 1 part
        row_layout.setStretch(1, 2)   # stats_widget gets 2 parts
        tp_outer.addWidget(row_widget)
        layout.addWidget(timer_panel)

        # ── Hearts ───────────────────────────────────────────
        self.hearts_widget = QWidget(self)
        h_layout = QHBoxLayout(self.hearts_widget)
        h_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hearts = []
        for _ in range(5):
            heart = QLabel("❤️", self)
            heart.setFont(QFont("Arial", 32))
            heart.setStyleSheet("background: transparent;")
            h_layout.addWidget(heart)
            self.hearts.append(heart)
        layout.addWidget(self.hearts_widget)
        self.heart_state = 0
        self.heart_timer = QTimer(self)
        self.heart_timer.timeout.connect(self.animate_hearts)
        self.heart_timer.start(300)

        # ── Blink countdown ──────────────────────────────────
        self.countdown_label = QLabel(f"UNLOCK IN... {self.unlock_countdown}", self)
        self.countdown_label.setFont(QFont(self.arcade_family, 20))
        self.countdown_label.setStyleSheet("color: #facc15; background: transparent;")
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.countdown_label)

        self.blink_timer = QTimer(self)
        self._bl_vis = True
        def blink_cd():
            self._bl_vis = not self._bl_vis
            self.countdown_label.setStyleSheet(
                f"color: #facc15; background: transparent; opacity: {'1.0' if self._bl_vis else '0.0'};"
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
            self.countdown_label.setText(f"UNLOCK IN... {self.unlock_countdown}")
        else:
            self.blink_timer.stop()
            self.countdown_label.setVisible(True)
            self.timer.stop()
            self.parent_window.trigger_playtime()