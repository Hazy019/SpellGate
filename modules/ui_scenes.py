from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QEasingCurve, QRect
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QPushButton, QGraphicsDropShadowEffect

class MemorizationScene(QWidget):
    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.parent_window = parent_window

        self.words = [
            "BIRD", "FISH", "TREE", "STAR",
            "MOON", "FIRE", "SNOW", "WIND",
            "RAIN", "DESK", "BOOK", "TIME"
        ]

        self.time_left = 300
        self.initUI()

    def initUI(self):
        self.setStyleSheet("""
            QWidget {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #E0FFF, stop:1 #B2EBF2);
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
        self.animate_cards_in()

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
        shadow.setBlueRadius(15)
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
            print("Moving to Phase 2: Sequential Recall!")