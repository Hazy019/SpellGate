import subprocess
import os
import sys

def build():
    print("🚀 Starting SpellGate Build Process...")
    
    # Ensure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Build command
    # --onefile: Bundles everything into one EXE
    # --noconsole: Hides the command prompt window
    # --name: Resulting file name
    # --add-data: Include assets and modules
    # Format for --add-data: "source;destination" (Windows uses semicolon)
    
    cmd = [
        "pyinstaller",
        "--onefile",
        "--noconsole",
        "--name=SpellGate",
        "--icon=assets/icons/logo.ico",
        "--add-data=assets;assets",
        "--add-data=modules;modules",
        "--add-data=data;data",
        "--add-data=gemini.env;.",
        "main.py"
    ]
    
    print(f"🛠️ Executing: {' '.join(cmd)}")
    subprocess.call(cmd)
    
    print("\n✅ Build Complete! Check the 'dist' folder for SpellGate.exe")

if __name__ == "__main__":
    build()
