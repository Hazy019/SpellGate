import json
import random
from modules.audio import play_audio

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGridLayout, 
                             QPushButton, QGraphicsDropShadowEffect, QLineEdit)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QEasingCurve, QVariantAnimation
from PyQt6.QtGui import QFont, QColor, QFontDatabase
from modules.game_logic import generate_scrambled, update_mastery, get_next_words, save_progress

DARK_THEME = """
    QWidget { background-color: #0F172A; color: #F8FAFC; font-family: 'Segoe UI'; }
    QLabel#Header { color: #38BDF8; font-weight: bold; }
    QLineEdit { 
        background-color: #1E293B; border: 2px solid #334155; 
        border-radius: 15px; padding: 12px; color: #38BDF8; font-size: 18px;
    }
    QPushButton#WordCard { 
        background-color: #1E293B; border: 2px solid #334155; 
        border-radius: 12px; color: #F8FAFC; padding: 15px;
    }
    QPushButton#ActionBtn { 
        background-color: #38BDF8; color: #0F172A; border-radius: 20px; padding: 15px; font-weight: bold;
    }
"""

LIGHT_THEME = """
    QWidget { background-color: #F1F5F9; color: #1E293B; font-family: 'Segoe UI'; }
    QLabel#Header { color: #0EA5E9; font-weight: bold; }
    QLineEdit { 
        background-color: #FFFFFF; border: 2px solid #E2E8F0; 
        border-radius: 15px; padding: 12px; color: #0EA5E9; font-size: 18px;
    }
    QPushButton#WordCard { 
        background-color: #FFFFFF; border: 2px solid #E2E8F0; 
        border-radius: 12px; color: #1E293B; padding: 15px;
    }
    QPushButton#ActionBtn { 
        background-color: #0EA5E9; color: #FFFFFF; border-radius: 20px; padding: 15px; font-weight: bold;
    }
"""

class SpeakingLineEdit(QLineEdit):
    """A custom text box that tells the user what word to spell and auto-capitalizes."""
    def __init__(self, word, parent=None):
        super().__init__(parent)
        self.target_word = word
        self.textChanged.connect(self.force_uppercase)

        self.glow = QGraphicsDropShadowEffect()
        self.glow.setBlurRadius(10)
        self.glow.setColor(QColor(56, 189, 248, 0)) # Fixed QColor wrapper
        self.setGraphicsEffect(self.glow)

    def force_uppercase(self, text):
        if text != text.upper():
            self.setText(text.upper())

    def focusInEvent(self, event):
        super().focusInEvent(event)
        play_audio(f"Spell {self.target_word}")
        self.start_glow()

    def start_glow(self):
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(1000)
        self.anim.setStartValue(10)
        self.anim.setEndValue(25)
        self.anim.setDirection(QVariantAnimation.Direction.Forward)
        self.anim.valueChanged.connect(lambda v: self.glow.setBlurRadius(v))
        self.anim.valueChanged.connect(lambda v: self.glow.setColor(QColor(56, 189, 248, int(v*10))))
        self.anim.setLoopCount(-1)
        self.anim.start()

class BaseScene(QWidget):
    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.is_dark = True

        font_id = QFontDatabase.addApplicationFont("assets/Orbitron-Bold.ttf")
        self.orbitron_family = QFontDatabase.applicationFontFamilies(font_id)[0] if font_id != -1 else "Arial"

    def apply_current_theme(self):
        self.setStyleSheet(DARK_THEME if self.is_dark else LIGHT_THEME)

    def create_theme_toggle(self, layout):
        self.toggle_btn = QPushButton("🌙" if self.is_dark else "☀️")
        self.toggle_btn.setFixedSize(60, 40)
        self.toggle_btn.setStyleSheet("background: transparent; font-size: 20px; border: none;")
        self.toggle_btn.clicked.connect(self.switch_theme)
        layout.addWidget(self.toggle_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def switch_theme(self):
        self.is_dark = not self.is_dark
        self.toggle_btn.setText("🌙" if self.is_dark else "☀️")
        self.apply_current_theme()

class MemorizationScene(BaseScene): 
    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.time_left = 300
        self.load_data()
        self.initUI()
        self.apply_current_theme()

    def load_data(self):
        try:
            with open("data/user_progress.json", "r") as f:
                self.progress_data = json.load(f)
        except:
            self.progress_data = {"mastered_words": [], "learning_pool": {}, "current_level": "Grade_4"}
        
        self.words = get_next_words(self.progress_data, "assists/words.csv", count=12)

    def initUI(self):
        layout = QVBoxLayout(self)
        self.create_theme_toggle(layout) 
        
        header = QLabel("AI MEMORY MODULE", self)
        header.setObjectName("Header")
        header.setFont(QFont(self.orbitron_family, 32))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        self.timer_label = QLabel("05:00", self)
        self.timer_label.setFont(QFont(self.orbitron_family, 24))
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.timer_label)

        grid_widget = QWidget(self)
        grid_layout = QGridLayout(grid_widget)
        
        self.cards = []
        row, col = 0, 0
        for word in self.words:
            card = self.create_word_card(word)
            grid_layout.addWidget(card, row, col)
            self.cards.append(card)
            col += 1
            if col > 3:
                col = 0
                row += 1
        layout.addWidget(grid_widget)

        self.ready_btn = QPushButton("INITIATE RECALL", self)
        self.ready_btn.setObjectName("ActionBtn")
        self.ready_btn.clicked.connect(self.finish_memorization)
        layout.addWidget(self.ready_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.study_timer = QTimer(self)
        self.study_timer.timeout.connect(self.update_timer)
        self.study_timer.start(1000)
        
        QTimer.singleShot(100, self.animate_cards_in)

    def create_word_card(self, word):
        btn = QPushButton(word)
        btn.setObjectName("WordCard") 
        btn.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        btn.clicked.connect(lambda: play_audio(word))
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
        else:
            self.finish_memorization()

    def finish_memorization(self):
        self.study_timer.stop()
        self.parent_window.start_recall_phase(self.words)

# --- PHASE 2 ---
class RecallScene(QWidget):
    def __init__(self, parent_window, words):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.words = words
        self.inputs = []
        self.attempts = [0] * len(words)
        self.earned_seconds = 0 
        self.initUI()

    def initUI(self):
        self.setStyleSheet("QWidget { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #E0FFFF, stop:1 #B2EBF2); }")
        layout = QVBoxLayout(self)
        
        header = QLabel("Recall the Order!", self)
        header.setFont(QFont("Arial", 32, QFont.Weight.Black))
        header.setStyleSheet("color: #00BCD4; background: transparent;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        grid_widget = QWidget(self)
        grid_layout = QGridLayout(grid_widget)
        
        row, col = 0, 0
        for i, word in enumerate(self.words):
            input_field = SpeakingLineEdit(word, self)
            input_field.setPlaceholderText("_ " * len(word))
            input_field.setFont(QFont("Arial", 18))
            input_field.setAlignment(Qt.AlignmentFlag.AlignCenter)
            input_field.setStyleSheet("background-color: white; border: 3px solid #E0E0E0; border-radius: 15px; padding: 15px;")
            input_field.returnPressed.connect(lambda idx=i: self.check_answer(idx))
            grid_layout.addWidget(input_field, row, col)
            self.inputs.append(input_field)
            col += 1
            if col > 3:
                col = 0
                row += 1
        layout.addWidget(grid_widget)

        # FEATURE 2: Auto-focus the first box and speak right when the scene loads!
        QTimer.singleShot(500, self.start_first_word)

    def start_first_word(self):
        if self.inputs:
            self.inputs[0].setFocus()
            play_audio(f"Spell {self.words[0]}")

    def check_answer(self, index):
        user_text = self.inputs[index].text().strip().upper()
        if user_text == self.words[index].upper():
            self.earned_seconds += 120 # +2 mins
            self.inputs[index].setEnabled(False)
            self.inputs[index].setStyleSheet("background-color: #C8E6C9; border: 3px solid #4CAF50; border-radius: 15px; color: #2E7D32;")
            play_audio("Correct")
            
            # FEATURE 3: Check if done. If not, AUTO-ADVANCE to the next box!
            if all(not inp.isEnabled() for inp in self.inputs):
                self.deposit_time(self.earned_seconds)
                self.parent_window.start_scrambled_phase(self.words)
            else:
                # Find the next box that hasn't been answered yet
                for i in range(len(self.inputs)):
                    if self.inputs[i].isEnabled():
                        self.inputs[i].setFocus()
                        play_audio(f"Spell {self.words[i]}")
                        break
        else:
            self.earned_seconds = max(0, self.earned_seconds - 60) # -1 min
            self.wobble_animation(self.inputs[index])
            play_audio("Try again")

    def wobble_animation(self, widget):
        anim = QPropertyAnimation(widget, b"pos")
        anim.setDuration(50)
        curr = widget.pos()
        anim.setKeyValueAt(0, curr)
        anim.setKeyValueAt(0.25, curr + QPoint(-10, 0))
        anim.setKeyValueAt(0.75, curr + QPoint(10, 0))
        anim.setKeyValueAt(1, curr)
        anim.setLoopCount(3)
        anim.start()

    def deposit_time(self, seconds):
        try:
            with open("data/time_bank.txt", "r") as f:
                current = int(f.read().strip())
            with open("data/time_bank.txt", "w") as f:
                f.write(str(current + seconds))
        except:
            pass


# --- PHASE 3 ---
class ScrambledPhase(QWidget):
    def __init__(self, parent_window, words):
        super().__init__(parent_window)
        self.parent_window = parent_window
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

    def initUI(self):
        self.setStyleSheet("QWidget { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #E0FFFF, stop:1 #B2EBF2); }")
        self.layout = QVBoxLayout(self)

        self.progress_label = QLabel(self)
        self.progress_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.progress_label.setStyleSheet("color: #00BCD4; background: transparent;")
        self.layout.addWidget(self.progress_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.scrambled_display = QLabel(self)
        self.scrambled_display.setFont(QFont("Arial", 60, QFont.Weight.Black))
        self.scrambled_display.setStyleSheet("color: #2C3E50; letter-spacing: 15px; background: transparent;")
        self.layout.addWidget(self.scrambled_display, alignment=Qt.AlignmentFlag.AlignCenter)

        self.input_field = QLineEdit(self)
        self.input_field.setFont(QFont("Arial", 28))
        self.input_field.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_field.setStyleSheet("background-color: white; border: 4px solid #FF6B9D; border-radius: 20px; padding: 10px; max-width: 400px;")
        
        # FEATURE 1: Force Uppercase in Phase 3 as well!
        self.input_field.textChanged.connect(lambda t: self.input_field.setText(t.upper()) if t != t.upper() else None)
        
        self.input_field.returnPressed.connect(self.submit_answer)
        self.layout.addWidget(self.input_field, alignment=Qt.AlignmentFlag.AlignCenter)

        self.hint_btn = QPushButton("NEED A HINT? (-1 min)", self)
        self.hint_btn.setStyleSheet("background-color: #FFD700; font-size: 16px; padding: 10px; border-radius: 10px;")
        self.hint_btn.clicked.connect(self.use_hint)
        self.layout.addWidget(self.hint_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.load_word()

    def load_word(self):
        self.input_field.clear()
        self.input_field.setFocus()
        self.hints_used = 0
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
            self.wobble_input()
            play_audio("Try again")

    def use_hint(self):
        self.hints_used += 1
        correct = self.words[self.current_index]
        self.scrambled_display.setText(correct[:2] + self.scrambled_word[2:])

    def deposit_time(self, seconds):
        try:
            with open("data/time_bank.txt", "r") as f:
                current = int(f.read().strip())
            with open("data/time_bank.txt", "w") as f:
                f.write(str(max(0, current + seconds)))
        except:
            pass

    def wobble_input(self):
        anim = QPropertyAnimation(self.input_field, b"pos")
        anim.setDuration(50)
        curr = self.input_field.pos()
        anim.setKeyValueAt(0, curr)
        anim.setKeyValueAt(0.25, curr + QPoint(-15, 0))
        anim.setKeyValueAt(0.75, curr + QPoint(15, 0))
        anim.setKeyValueAt(1, curr)
        anim.setLoopCount(3)
        anim.start()

    def next_word(self):
        self.current_index += 1
        if self.current_index < len(self.words):
            self.load_word()
        else:
            save_progress(self.progress_data)
            self.parent_window.show_final_results()


# --- PHASE 4 ---
class SummaryScene(QWidget):
    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.unlock_countdown = 10
        self.earned_time = self.read_final_time()
        self.initUI()
        self.announce_success()

    def read_final_time(self):
        try:
            with open("data/time_bank.txt", "r") as f:
                return int(f.read().strip())
        except:
            return 0

    def initUI(self):
        self.setStyleSheet("QWidget { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #E0FFFF, stop:1 #B2EBF2); }")
        layout = QVBoxLayout(self)
        
        title = QLabel("MISSION COMPLETE!", self)
        title.setFont(QFont("Arial", 48, QFont.Weight.Black))
        title.setStyleSheet("color: #FF6B9D; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        mins, secs = divmod(self.earned_time, 60)
        time_label = QLabel(f"Total Playtime Earned:\n{mins} Minutes and {secs} Seconds", self)
        time_label.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        time_label.setStyleSheet("color: #00BCD4; background: transparent;")
        time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(time_label)

        self.countdown_label = QLabel(f"Unlocking system in... {self.unlock_countdown}", self)
        self.countdown_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.countdown_label.setStyleSheet("color: #FFD700; background: transparent;")
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.countdown_label)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick_countdown)
        self.timer.start(1000)

    def announce_success(self):
        mins = self.earned_time // 60
        play_audio(f"Great Job! Spelling module complete. You have earned {mins} minutes of playtime. Unlocking system!")

    def tick_countdown(self):
        self.unlock_countdown -= 1
        if self.unlock_countdown > 0:
            self.countdown_label.setText(f"Unlocking system in... {self.unlock_countdown}")
        else:
            self.timer.stop()
            self.parent_window.trigger_playtime()