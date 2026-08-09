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
        "-y",               # overwrite output directory without prompt
        "--clean",          # clear previous build cache
        "SpellGate.spec",
    ]

    print(f"Running: {' '.join(cmd)}")
    print()
    result = subprocess.call(cmd)

    print()
    print("-" * 45)
    if result == 0:
        # COLLECT mode puts the EXE inside dist/SpellGate/ (not dist/ directly)
        exe_path = os.path.abspath(os.path.join("dist", "SpellGate", "SpellGate.exe"))
        dist_dir = os.path.dirname(exe_path)
        size_mb = os.path.getsize(exe_path) / 1024 / 1024
        print(f"[OK] Build COMPLETE! SpellGate.exe = {size_mb:.1f} MB")
        print(f"   Folder: {dist_dir}")
        print()
        print("Next steps:")
        print("  1. Build installer:  iscc installer\\SpellGateSetup.iss")
        print("  2. Upload SpellGateSetup.exe to GitHub Releases (tag: v1.x.x)")
        print("  3. Parents download SpellGateSetup.exe from the website")
        print()
        print("For quick local testing (dev only):")
        print(f"  Run: {exe_path}")
    else:
        print("Build FAILED. Check output above for errors.")


if __name__ == "__main__":
    build()
