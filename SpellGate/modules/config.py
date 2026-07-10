import os
from pathlib import Path

def get_data_dir():
    app_data = os.getenv('LOCALAPPDATA')
    if not app_data:
        app_data = str(Path.home() / ".spellgate")
    path = Path(app_data) / "SpellGate"
    path.mkdir(parents=True, exist_ok=True)
    return path

DATA_DIR = get_data_dir()
TIME_BANK_FILE = str(DATA_DIR / "time_bank.txt")
USER_PROGRESS_FILE = str(DATA_DIR / "user_progress.json")
