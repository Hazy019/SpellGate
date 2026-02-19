import sys
import keyboard
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt

class KioskManager:
    def __init__(self, main_window):
        self.window = main_window

    def enable_kiosk_mode(self):
        """Forces Fullscreen and (safely) prepares to block keys."""
        self.window.showFullScreen()
        self.window.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.window.show()

        #try:
        #    keyboard.block_key('windows')
        #    keyboard.block_key('alt')
        #    keyboard.block_key('tab')
        #except ImportError:
        #    print("keyboard library not found or permission denied.")

    def disable_kiosk_mode(self):
        """Unlocks the screen (For parents/debugging)."""
        self.is_locked = False

        try:
            keyboard.unhook_all()
        except:
            pass

        self.window.close()

    def check_exit_code(self):
        """
        Listen for Ctrl + Shift + P
        In PyQt, this is usually handled by a QShortcut in the Main Window,
        not here directly, but we define the logic here.
        """

        print("Parent Override Triggered!")
        self.disable_kiosk_mode()