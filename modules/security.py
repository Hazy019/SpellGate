import os
import json
import hmac
import hashlib
import keyring
import winreg
from modules.config import USER_PROGRESS_FILE, TIME_BANK_FILE

# ─────────────────────────────────────────────────────────────
#  KEYRING SERVICE NAMES
# ─────────────────────────────────────────────────────────────
_KEYRING_SERVICE          = "SpellGate"
_KEYRING_API_KEY          = "gemini_api_key"
_KEYRING_FIREBASE_REFRESH_TOKEN = "firebase_refresh_token"
_KEYRING_PARENT_PIN       = "parent_pin"


# ─────────────────────────────────────────────────────────────
#  MACHINE-BOUND HMAC KEY
#  Derived from the Windows MachineGuid — unique per PC.
#  Even if someone knows the algorithm they cannot forge
#  signatures for a different machine.
# ─────────────────────────────────────────────────────────────
def _get_hmac_secret() -> bytes:
    """Derive a machine-unique HMAC secret from the Windows MachineGuid."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography"
        )
        machine_guid, _ = winreg.QueryValueEx(key, "MachineGuid")
        winreg.CloseKey(key)
        # Salt it with app namespace so collisions with other apps are impossible
        return f"spellgate-v2-{machine_guid}".encode("utf-8")
    except Exception:
        # Fallback (VM / stripped registry) — still better than nothing
        return b"spellgate-integrity-key-v1-prod"


# ─────────────────────────────────────────────────────────────
#  API KEY SECURITY (Windows Credential Manager)
# ─────────────────────────────────────────────────────────────
def get_api_key() -> str | None:
    """Retrieves the Gemini API key from Windows Credential Manager."""
    return keyring.get_password(_KEYRING_SERVICE, _KEYRING_API_KEY)

def set_api_key(api_key: str):
    """Saves the Gemini API key to Windows Credential Manager."""
    keyring.set_password(_KEYRING_SERVICE, _KEYRING_API_KEY, api_key)


# ─────────────────────────────────────────────────────────────
#  FIREBASE REFRESH TOKEN (Windows Credential Manager)
# ─────────────────────────────────────────────────────────────
def get_firebase_refresh_token() -> str | None:
    """Retrieves the Firebase refresh token from Windows Credential Manager."""
    return keyring.get_password(_KEYRING_SERVICE, _KEYRING_FIREBASE_REFRESH_TOKEN)

def set_firebase_refresh_token(token: str):
    """Saves the Firebase refresh token to Windows Credential Manager."""
    keyring.set_password(_KEYRING_SERVICE, _KEYRING_FIREBASE_REFRESH_TOKEN, token)


# ─────────────────────────────────────────────────────────────
#  PARENT PIN (Windows Credential Manager — local backup)
#  Primary source of truth is Firestore; this is the offline
#  fallback so the parent can still override if offline.
# ─────────────────────────────────────────────────────────────
def get_local_pin() -> str | None:
    """Return the locally cached parent PIN from Credential Manager."""
    return keyring.get_password(_KEYRING_SERVICE, _KEYRING_PARENT_PIN)

def set_local_pin(pin: str):
    """Cache the parent PIN in Credential Manager (offline backup)."""
    keyring.set_password(_KEYRING_SERVICE, _KEYRING_PARENT_PIN, pin)


# ─────────────────────────────────────────────────────────────
#  TIME BANK INTEGRITY (Machine-bound HMAC)
# ─────────────────────────────────────────────────────────────
def _sign_time(value: int) -> str:
    """Create a SHA-256 HMAC signature for the time value."""
    secret = _get_hmac_secret()
    msg = str(value).encode()
    return hmac.new(secret, msg, hashlib.sha256).hexdigest()

def secure_save_time(seconds: int, file_path=TIME_BANK_FILE):
    """Saves time securely with a machine-bound HMAC signature."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        sig = _sign_time(seconds)
        with open(file_path, "w") as f:
            f.write(f"{seconds}:{sig}")
    except Exception as e:
        print(f"[Security] Error saving time: {e}")

def secure_load_time(file_path=TIME_BANK_FILE) -> int:
    """Loads time and verifies its HMAC. Resets to 0 if tampered."""
    try:
        with open(file_path, "r") as f:
            content = f.read().strip()

        if ":" not in content:
            print("[Security] Unsigned time_bank.txt — resetting to 0.")
            secure_save_time(0, file_path)
            return 0

        value_str, sig = content.split(":", 1)
        value = int(value_str)

        if not hmac.compare_digest(_sign_time(value), sig):
            print("[Security] TAMPER DETECTED in time_bank.txt! Resetting to 0.")
            secure_save_time(0, file_path)
            return 0

        return value
    except Exception:
        return 0


# ─────────────────────────────────────────────────────────────
#  PROGRESS DATA INTEGRITY (Machine-bound HMAC)
# ─────────────────────────────────────────────────────────────
def _hash_progress(data: dict) -> str:
    """Create a SHA-256 HMAC signature for the JSON progress data."""
    secret = _get_hmac_secret()
    clean_data = {k: v for k, v in data.items() if k != '__hash__'}
    content = json.dumps(clean_data, sort_keys=True)
    return hmac.new(secret, content.encode('utf-8'), hashlib.sha256).hexdigest()

def secure_save_progress(progress_data: dict, file_path=USER_PROGRESS_FILE):
    """Saves the player's progress securely with a machine-bound HMAC signature."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        save_data = dict(progress_data)
        save_data['__hash__'] = _hash_progress(save_data)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, indent=4)
    except Exception as e:
        print(f"[Security] Error saving progress: {e}")

def secure_load_progress(file_path=USER_PROGRESS_FILE) -> dict:
    """Loads progress data and verifies its machine-bound HMAC signature."""
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
            print("[Security] Unsigned user_progress.json — resetting.")
            secure_save_progress(fresh_progress, file_path)
            return fresh_progress

        if not hmac.compare_digest(_hash_progress(data), stored_hash):
            print("[Security] TAMPER DETECTED in user_progress.json! Resetting.")
            secure_save_progress(fresh_progress, file_path)
            return fresh_progress

        return data
    except (FileNotFoundError, json.JSONDecodeError):
        return fresh_progress
