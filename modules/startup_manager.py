import os
import sys
import win32com.client
import winreg

def install_to_startup():
    """
    Writes to HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
    This persists across reboots and cannot be deleted by navigating to a folder.
    ALSO writes the shortcut as a backup.
    """
    if getattr(sys, 'frozen', False):
        exe_path = sys.executable
    else:
        exe_path = os.path.abspath(sys.argv[0])

    # Method 1: Registry Run Key (primary)
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "SpellGate", 0, winreg.REG_SZ, f'"{exe_path}"')
        winreg.CloseKey(key)
        print("Added SpellGate to Registry Startup.")
    except Exception as e:
        print(f"Registry startup failed: {e}")

    # Method 2: Startup folder (backup)
    startup_dir = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
    shortcut_path = os.path.join(startup_dir, "SpellGate.lnk")

    try:
        if not os.path.exists(shortcut_path):
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = exe_path
            shortcut.WorkingDirectory = os.path.dirname(exe_path)
            shortcut.IconLocation = exe_path
            shortcut.save()
            print(f"Added SpellGate to Startup Folder: {shortcut_path}")
    except Exception as e:
        print(f"Failed to add to startup folder: {e}")
        
    return True
