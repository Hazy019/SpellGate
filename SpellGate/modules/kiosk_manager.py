import sys
import keyboard
from PyQt6.QtCore import Qt

def set_task_manager_disabled(disabled: bool):
    """
    Disable or enable Task Manager for the current user via HKCU registry.
    Does not require administrator privileges.
    """
    if sys.platform != "win32":
        return
    try:
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
        key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        
        if disabled:
            # 1 = Task Manager Disabled
            winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
            print("[KioskManager] Task Manager disabled in registry.")
        else:
            try:
                winreg.DeleteValue(key, "DisableTaskMgr")
                print("[KioskManager] Task Manager re-enabled in registry.")
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        print(f"[KioskManager] Failed to adjust Task Manager registry status: {e}")


class KioskManager:
    def __init__(self, main_window):
        self.window = main_window
        self.is_locked = False

    def enable_kiosk_mode(self):
        """Forces Fullscreen, blocks system keys, and disables Task Manager."""
        self.is_locked = True
        self.window.showFullScreen()
        self.window.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.window.show()

        # Disable Task Manager via registry
        set_task_manager_disabled(True)

        try:
            keyboard.block_key('windows')
            
            # Suppress standard keyboard shortcuts
            keyboard.add_hotkey('alt+tab', lambda: None, suppress=True)
            keyboard.add_hotkey('alt+f4', lambda: None, suppress=True)
            keyboard.add_hotkey('ctrl+shift+esc', lambda: None, suppress=True)
            keyboard.add_hotkey('ctrl+esc', lambda: None, suppress=True)
        except Exception as e:
            print(f"Keyboard hook error: {e}")

    def disable_kiosk_mode(self):
        """Unlocks the screen and restores Task Manager access."""
        self.is_locked = False

        # Re-enable Task Manager via registry
        set_task_manager_disabled(False)

        try:
            keyboard.unhook_all()
        except:
            pass

        self.window.showNormal()
        self.window.setWindowFlags(Qt.WindowType.Window)
        self.window.show()