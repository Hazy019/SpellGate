import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtGui import QKeySequence, QShortcut
from modules.kiosk_manager import KioskManager
from modules.ui_scenes import MemorizationScene, RecallScene

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spelling Star")
        
        # Start with Phase 1
        self.show_memorization_phase()

        self.kiosk = KioskManager(self)
        self.kiosk.enable_kiosk_mode()

        self.exit_shortcut = QShortcut(QKeySequence("Ctrl+Shift+P"), self)
        self.exit_shortcut.activated.connect(self.kiosk.disable_kiosk_mode)

    def show_memorization_phase(self):
        self.current_scene = MemorizationScene(self)
        self.setCentralWidget(self.current_scene)

    def start_recall_phase(self, words):
        # This switches the screen to the Recall Phase
        self.current_scene = RecallScene(self, words)
        self.setCentralWidget(self.current_scene)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())