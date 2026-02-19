import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtGui import QKeySequence, QShortcut, QFont
from PyQt6.QtCore import Qt, QTimer
from modules.kiosk_manager import KioskManager
from modules.ui_scenes import MemorizationScene

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spelling Bee")
        self.resize(1024, 768)

        self.current_scene = MemorizationScene(self)
        self.setCentraWidget(self.current_scene)

        # try:
        #     with open("data/time_bank.txt", "r") as f:
        #         self.time_remaining = int(f.read())

        # except:
        #     self.time_remaining = 15

        # self.setWindowTitle("Spelling Bee")
        # self.central_widget = QWidget()
        # self.setCentralWidget(self.central_widget)
        # self.layout = QVBoxLayout(self.central_widget)

        # self.label = QLabel(f"Time Remaining: {self.time_remaining}s", self)
        # self.label.setFont(QFont("Arial", 40, QFont.Weight.Bold))
        # self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.layout.addWidget(self.label)

        self.kiosk = KioskManager(self)
        self.kiosk.enable_kiosk_mode()

        self.exit_shortcut = QShortcut(QKeySequence("Ctrl+Shift+P"), self)
        self.exit_shortcut.activated.connect(self.kiosk.disable_kiosk_mode)
        
    #     self.timer = QTimer(self)
    #     self.timer.timeout.connect(self.countdown)
    #     self.timer.start(1000)

    # def countdown(self):
    #     if self.time_remaining > 0:
    #         self.time_remaining -=1
    #         self.label.setText(f"Time Remaining: {self.time_remaining}s")

    #     else:
    #         self.timer.stop()
    #         self.label.setText("SHUTDOWN INITIATED")
    #         self.label.setStyleSheet("color:red;")

    #         print("If this was real the PC would shutdown now.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())