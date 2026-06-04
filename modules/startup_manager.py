import os
import sys
import win32com.client

def install_to_startup():
    """
    Creates a shortcut in the Windows Startup folder pointing to the current executable.
    Only works when bundled with PyInstaller (where sys.frozen is true) or if run directly.
    """
    if getattr(sys, 'frozen', False):
        exe_path = sys.executable
    else:
        exe_path = os.path.abspath(sys.argv[0])

    startup_dir = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
    shortcut_path = os.path.join(startup_dir, "SpellGate.lnk")

    # If it already exists, assume installed
    if os.path.exists(shortcut_path):
        return False

    try:
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = exe_path
        shortcut.WorkingDirectory = os.path.dirname(exe_path)
        shortcut.IconLocation = exe_path
        shortcut.save()
        print(f"Added SpellGate to Startup: {shortcut_path}")
        return True
    except Exception as e:
        print(f"Failed to add to startup: {e}")
        return False
