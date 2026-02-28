import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtGui import QKeySequence, QShortcut, QFont
from PyQt6.QtCore import Qt, QTimer, QPoint

from modules.kiosk_manager import KioskManager
from modules.ui_scenes import MemorizationScene, RecallScene, ScrambledPhase, SummaryScene
class FloatingTimer(QWidget):
    """The small widget that stays on screen during playtime."""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(0,0,0,150); border-radius; 10px")

        layout = QVBoxLayout(self)
        self.label = QLabel("00:00", self)
        self.label.setFont(QFont("Arial", 18 , QFont.Weight.Bold))
        self.label.setStyleSheet("color: white;")
        layout.addWidget(self.label)
        self.setGeometry(50, 50, 120, 50)

        self.drag_position = QPoint()

        self.time_left = self.load_time()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.leftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def load_time(self):
        try:
            with open("data/time_bank.txt", "r") as f:
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
            print("Executing Shutdown")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SpellGate Lock")

        try:
            with open("data/time_bank.txt", "w") as f:
                f.write("0")
        except Exception as e:
            print(f"Could not reset time bank: {e}")
        
        self.kiosk = KioskManager(self)
        self.kiosk.enable_kiosk_mode()

        self.exit_shortcut = QShortcut(QKeySequence("Ctrl+Shift+P"), self)
        self.exit_shortcut.activated.connect(self.emergency_exit)

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

        self.floating_tracker = FloatingTimer()
        self.floating_tracker.show()

    def emergency_exit(self):
        self.kiosk.disable_kiosk_mode()
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())