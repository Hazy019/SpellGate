import psutil
import time
import subprocess
import sys
import os

WATCHDOG_INTERVAL = 3  # seconds
GAME_EXE = "SpellGate.exe"

def main():
    print("SpellGate Watchdog Started...")
    
    # If running from source, the process name is python.exe and we need to check args
    is_frozen = getattr(sys, 'frozen', False)
    
    while True:
        time.sleep(WATCHDOG_INTERVAL)
        
        running = False
        
        for p in psutil.process_iter(['name', 'cmdline']):
            try:
                # If compiled, look for SpellGate.exe
                if is_frozen:
                    if p.info['name'] == GAME_EXE:
                        running = True
                        break
                # If running from source, look for python process running main.py
                else:
                    if p.info['name'] in ('python.exe', 'pythonw.exe'):
                        cmdline = p.info.get('cmdline', [])
                        if cmdline and any('main.py' in arg for arg in cmdline):
                            running = True
                            break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        if not running:
            print("SpellGate process not found! Restarting...")
            try:
                if is_frozen:
                    exe_path = os.path.join(os.path.dirname(sys.executable), GAME_EXE)
                    subprocess.Popen([exe_path])
                else:
                    main_py_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
                    subprocess.Popen([sys.executable, main_py_path])
            except Exception as e:
                print(f"Failed to restart SpellGate: {e}")

if __name__ == "__main__":
    main()
