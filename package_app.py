import subprocess
import os
import sys


def build():
    print("Starting SpellGate Build Process...")
    print("-" * 45)

    # Ensure PyInstaller is installed
    try:
        import PyInstaller
        print(f"PyInstaller found: v{PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Use the .spec file — it has all the correct settings including
    # hidden imports for google-genai, pyttsx3, and keyboard internals.
    # Do NOT use --onefile flags here; the spec handles everything.
    cmd = [
        "pyinstaller",
        "--clean",          # clear previous build cache
        "SpellGate.spec",
    ]

    print(f"Running: {' '.join(cmd)}")
    print()
    result = subprocess.call(cmd)

    print()
    print("-" * 45)
    if result == 0:
        exe_path = os.path.abspath(os.path.join("dist", "SpellGate.exe"))
        size_mb = os.path.getsize(exe_path) / 1024 / 1024
        print(f"Build COMPLETE! ({size_mb:.1f} MB)")
        print(f"EXE location: {exe_path}")
        print()
        print("Deployment steps:")
        print("  1. Copy dist/SpellGate.exe to the child's PC")
        print("  2. Right-click SpellGate.exe -> Run as Administrator")
        print("  3. Kiosk mode activates automatically on launch")
        print("  4. Parent exit: Ctrl+Shift+P")
    else:
        print("Build FAILED. Check output above for errors.")


if __name__ == "__main__":
    build()
