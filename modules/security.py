import os
import json
import hmac
import hashlib
import keyring
from modules.config import USER_PROGRESS_FILE, TIME_BANK_FILE

# Hardcoded secret key for HMAC generation (in a real app, obfuscate this)
HMAC_SECRET = b"spellgate-integrity-key-v1-prod"

# ─────────────────────────────────────────────────────────────
#  API KEY SECURITY (Credential Manager)
# ─────────────────────────────────────────────────────────────
def get_api_key():
    """Retrieves the Gemini API key securely from Windows Credential Manager."""
    return keyring.get_password("SpellGate", "gemini_api_key")

def set_api_key(api_key):
    """Saves the Gemini API key securely to Windows Credential Manager."""
    keyring.set_password("SpellGate", "gemini_api_key", api_key)


# ─────────────────────────────────────────────────────────────
#  TIME BANK INTEGRITY (HMAC)
# ─────────────────────────────────────────────────────────────
def _sign_time(value: int) -> str:
    """Create a SHA-256 HMAC signature for the time value."""
    msg = str(value).encode()
    return hmac.new(HMAC_SECRET, msg, hashlib.sha256).hexdigest()

def secure_save_time(seconds: int, file_path=TIME_BANK_FILE):
    """Saves time securely with an HMAC signature to prevent tampering."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        sig = _sign_time(seconds)
        with open(file_path, "w") as f:
            f.write(f"{seconds}:{sig}")
    except Exception as e:
        print(f"[Security] Error saving time: {e}")

def secure_load_time(file_path=TIME_BANK_FILE) -> int:
    """Loads time and verifies its HMAC signature. Resets to 0 if tampered."""
    try:
        with open(file_path, "r") as f:
            content = f.read().strip()
            
        if ":" not in content:
            # Handle legacy/unsigned time_bank.txt (just reset to 0 to be safe, or migrate)
            # We'll reset to 0 if it's tampered/unsigned to prevent cheating
            print("[Security] Unsigned time_bank.txt. Resetting to 0.")
            secure_save_time(0, file_path)
            return 0
            
        value_str, sig = content.split(":", 1)
        value = int(value_str)
        
        # Verify signature
        if not hmac.compare_digest(_sign_time(value), sig):
            print("[Security] TAMPER DETECTED in time_bank.txt! Resetting to 0.")
            secure_save_time(0, file_path)
            return 0
            
        return value
    except Exception as e:
        # If file doesn't exist or is corrupt
        return 0


# ─────────────────────────────────────────────────────────────
#  PROGRESS DATA INTEGRITY (HMAC)
# ─────────────────────────────────────────────────────────────
def _hash_progress(data: dict) -> str:
    """Create a SHA-256 HMAC signature for the JSON progress data."""
    # Ensure we don't include the hash itself in the calculation
    clean_data = {k: v for k, v in data.items() if k != '__hash__'}
    # Serialize consistently
    content = json.dumps(clean_data, sort_keys=True)
    return hmac.new(HMAC_SECRET, content.encode('utf-8'), hashlib.sha256).hexdigest()

def secure_save_progress(progress_data: dict, file_path=USER_PROGRESS_FILE):
    """Saves the player's progress securely with an HMAC signature."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        # Deep copy to avoid modifying the in-memory dict passed by reference
        save_data = dict(progress_data)
        save_data['__hash__'] = _hash_progress(save_data)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=4)
    except Exception as e:
        print(f"[Security] Error saving progress: {e}")

def secure_load_progress(file_path=USER_PROGRESS_FILE) -> dict:
    """Loads progress data and verifies its HMAC signature."""
    fresh_progress = {
        "mastered_words": [],
        "learning_pool": {},
        "current_level": "Novice",
    }
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        stored_hash = data.pop('__hash__', None)
        
        if stored_hash is None:
            print("[Security] Unsigned user_progress.json. Resetting.")
            secure_save_progress(fresh_progress, file_path)
            return fresh_progress
            
        if not hmac.compare_digest(_hash_progress(data), stored_hash):
            print("[Security] TAMPER DETECTED in user_progress.json! Resetting.")
            secure_save_progress(fresh_progress, file_path)
            return fresh_progress
            
        return data
    except (FileNotFoundError, json.JSONDecodeError):
        return fresh_progress
