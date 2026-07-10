import sys
import keyboard
from PyQt6.QtCore import Qt

class KioskManager:
    def __init__(self, main_window):
        self.window = main_window
        self.is_locked = False

    def enable_kiosk_mode(self):
        """Forces Fullscreen and (safely) prepares to block keys."""
        self.is_locked = True
        self.window.showFullScreen()
        self.window.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.window.show()

        try:
            keyboard.block_key('windows')
            keyboard.block_key('esc')
            
            # Explicitly suppress system combos
            keyboard.add_hotkey('alt+tab', lambda: None, suppress=True)
            keyboard.add_hotkey('alt+f4', lambda: None, suppress=True)
            keyboard.add_hotkey('ctrl+shift+esc', lambda: None, suppress=True)
            keyboard.add_hotkey('ctrl+esc', lambda: None, suppress=True)
        except Exception as e:
            print(f"Keyboard hook error: {e}")

    def disable_kiosk_mode(self):
        """Unlocks the screen (For parents/debugging)."""
        self.is_locked = False

        try:
            keyboard.unhook_all()
        except:
            pass

        self.window.showNormal()
        self.window.setWindowFlags(Qt.WindowType.Window)
        self.window.show()

    #def check_exit_code(self):
        """
        Listen for Ctrl + Shift + P
        In PyQt, this is usually handled by a QShortcut in the Main Window,
        not here directly, but we define the logic here.
        """

    #    print("Parent Override Triggered!")
    #    self.disable_kiosk_mode()