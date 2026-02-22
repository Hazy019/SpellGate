from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QEasingCurve
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGridLayout, 
                             QPushButton, QGraphicsDropShadowEffect, QLineEdit)

class MemorizationScene(QWidget):
    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.parent_window = parent_window

        self.words = [
            "BIRD", "FISH", "TREE", "STAR", "MOON", "FIRE", 
            "SNOW", "WIND", "RAIN", "DESK", "BOOK", "TIME"
        ]

        self.time_left = 300
        self.initUI()

    def initUI(self):
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #E0FFFF, stop:1 #B2EBF2);
            }
        """)

        main_layout =QVBoxLayout(self)
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(20)

        self.header = QLabel("Spelling Bee: Memorize the Words!", self)
        self.header.setFont(QFont("Arial", 36, QFont.Weight.Black))
        self.header.setStyleSheet("color: #00BCD4; background: transparent;")
        self.header.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.timer_label = QLabel("05:00", self)
        self.timer_label.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        self.timer_label.setStyleSheet("color: #FF6B9D; background: transparent;")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(self.header)
        main_layout.addWidget(self.timer_label)

        self.grid_widget = QWidget(self)
        self.grid_widget.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(20)

        self.cards = []
        row, col = 0, 0
        for i, word in enumerate(self.words):
            card = self.create_word_card(word)
            self.grid_layout.addWidget(card, row, col)
            self.cards.append(card)
            col += 1
            if col > 3:
                col = 0
                row +=1

        main_layout.addWidget(self.grid_widget)

        self.ready_btn = QPushButton("I'm Ready!", self)
        self.ready_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ready_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFD700;
                color: #333333;
                font-size: 24px;
                font-weight: bold;
                border-radius: 25px;
                padding: 15px 40px;
                border: 3px solid #FFF8DC;
            }
            QPushButton:hover {
                background-color: #FFC107;
                border-color: #FFECB3;
            }
        """)

        self.ready_btn.clicked.connect(self.finish_memorization)

        main_layout.addWidget(self.ready_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.start_timer()
        QTimer.singleShot(100, self.animate_cards_in)

    def create_word_card(self, word):
        btn = QPushButton(word)
        btn.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #2C3E50;
                border-radius: 15px;
                border: 3px solid #E0E0E0;
                padding: 20px;
            }
            QPushButton:hover {
                border: 3px solid #FF6B9D;
                background-color: #FFF0F5;
                color: #FF6B9D;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 188, 212, 80))
        shadow.setOffset(0, 5)
        btn.setGraphicsEffect(shadow)

        return btn
    
    def animation_cards_in(self):
        """Create a slick staggered animation pop-in animation for the cards."""
        self.animations = []
        delay = 0
        for card in self.cards:
            card.move(card.x(), card.y() + 100)
            card.setGraphicsEffect(None)

            anim = QPropertyAnimation(card, b"pos")
            anim.setDuration(600)
            anim.setStartValue(QPoint(card.x(), card.y() + 100))
            anim.setEasingCurve(QEasingCurve.Type.OutBack)
            
            QTimer.singleShot(delay, anim.start)
            self.animations.append(anim)
            delay += 150

    def start_timer(self):
            self.study_timer =QTimer(self)
            self.study_timer.timeout.connect(self.update_timer)
            self.study_timer.start(1000)

    def update_timer(self):
        if self.time_left > 0:
            self.time_left -= 1
            mins, secs = divmod(self.time_left, 60)
            self.timer_label.setText(f"{mins:02d}:{secs:02d}")

        else:
            self.study_timer.stop()
            self.finish_memorization()

    def finish_memorization(self):
        self.study_timer.stop()
        self.parent_window.start_recall_phase(self.words)

class RecallScene(QWidget):
    def __init__(self, parent_window, words):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.words = words
        self.inputs = []
        self.attempts = [0] * len(words)
        self.initUI()

    def initUI(self):
        self.setStyleSheet("""
            QWidget {
                background: qlineargradientx1:0, y1:0, x2:1, y2:1, stop:0 #E0FFFF, stop:1 #B2EBF2);
            }
        """)

        layout =QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)

        header = QLabel("Phase 2: Type the words in order!", self)
        header.setFont(QFont("Arial", 24))
        header.setStyleSheet("color: #00BCD4; background: transparent;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        grid_widget = QWidget(self)
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(20)

        row, col = 0, 0
        for i, word in enumerate(self.words):
            input_field = QLineEdit(self)
            input_field.setPlaceholderText("_ " * len(word))
            input_field.setFont(QFont("Arial", 18))
            input_field.setAlignment(Qt.AlignmentFlag.AlignCenter)
            input_field.setStyleSheet("""
                QLineEdit {
                    background-color: white;
                    border: 3px solid #E0E0E0;
                    border-radius: 15px;
                    padding: 15px;
                    color: #2C3E50;
                }
                QLineEdit:focus {
                    border: 3px solid #00BCD4;
                }
            """)
            
            input_field.returnPressed.connect(lambda idx=i: self.check_answer(idx))

            grid_layout.addWidget(input_field, row, col)
            self.inputs.append(input_field)

            col += 1
            if col > 3:
                col = 0
                row += 1

        layout.addWidget(grid_widget)

        self.study_again_btn = QPushButton("I Need to Study Again...", self)
        self.study_again_btn.setVisible(False)
        self.study_again_btn.setStyleSheet("background-color: #FF6B9D; color: whit; padding: 10px; border-radius: 10px;")
        self.study_again_btn.clicked.connect(self.parent_window.show_memorization_phase)
        layout.addWidget(self.study_again_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def check_answer(self, index):
        user_text = self.inputs[index].text().strip().upper()  
        correct_word = self.words[index].upper()

        if user_text == correct_word:
            self.inputs[index].setEnabled(False)
            self.inputs[index].setStyleSheet("background-color: #C8E6C9; border: 3px solid #4CAF50; border-radius: 15px; color: #2E7D32;")
            self.check_overall_completion()
        else:
            self.wobble_animation(self.inputs[index])
            self.attempts[index] += 1

            if sum(self.attempts) >= 3:
                self.study_again_btn.setVisible(True)

    def wobble_animation(self, widget):
        """Create the 'No' shake effect."""
        anim = QPropertyAnimation(widget, b"pos")
        anim.setDuration(50)
        curr = widget.pos()

        anim.setKeyValueAt(0, curr)
        anim.setKeyValueAt(0.25, curr + QPoint(-10, 0))
        anim.setKeyValueAt(0.75, curr + QPoint(10, 0))
        anim.setKeyValueAt(1, curr)
        anim.setLoopCount(3)
        anim.start()

    def check_overall_completion(self):
        """Check if all words are filled correctly."""
        if all(not inp.isEnabled() for inp in self.inputs):
            print("Phase 2 Complete! Starting Phase 3 (Scrambled Spelling)...")

            