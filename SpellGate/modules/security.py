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
_KEYRING_PARENT_UID       = "parent_uid"


def get_parent_uid() -> str | None:
    """Retrieves the paired parent UID from Windows Credential Manager."""
    return keyring.get_password(_KEYRING_SERVICE, _KEYRING_PARENT_UID)

def set_parent_uid(uid: str):
    """Saves the paired parent UID to Windows Credential Manager."""
    keyring.set_password(_KEYRING_SERVICE, _KEYRING_PARENT_UID, uid)



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
#  WINDOWS DPAPI (Data Protection API)
# ─────────────────────────────────────────────────────────────
import ctypes
from ctypes import wintypes

class DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_char))
    ]

def encrypt_dpapi(data: bytes) -> bytes:
    """Encrypts bytes using Windows DPAPI (CryptProtectData)."""
    try:
        crypt32 = ctypes.windll.crypt32
        kernel32 = ctypes.windll.kernel32
    except AttributeError:
        # Fallback for non-Windows platforms (e.g. testing)
        return data

    in_blob = DATA_BLOB(len(data), ctypes.create_string_buffer(data))
    out_blob = DATA_BLOB()
    # CRYPTPROTECT_UI_FORBIDDEN = 0x01
    success = crypt32.CryptProtectData(
        ctypes.byref(in_blob),
        None, None, None, None,
        0x01,
        ctypes.byref(out_blob)
    )
    if not success:
        raise ctypes.WinError()
    
    result = ctypes.string_at(out_blob.pbData, out_blob.cbData)
    kernel32.LocalFree(out_blob.pbData)
    return result

def decrypt_dpapi(data: bytes) -> bytes:
    """Decrypts bytes using Windows DPAPI (CryptUnprotectData)."""
    try:
        crypt32 = ctypes.windll.crypt32
        kernel32 = ctypes.windll.kernel32
    except AttributeError:
        # Fallback for non-Windows platforms (e.g. testing)
        return data

    in_blob = DATA_BLOB(len(data), ctypes.create_string_buffer(data))
    out_blob = DATA_BLOB()
    # CRYPTPROTECT_UI_FORBIDDEN = 0x01
    success = crypt32.CryptUnprotectData(
        ctypes.byref(in_blob),
        None, None, None, None,
        0x01,
        ctypes.byref(out_blob)
    )
    if not success:
        raise ctypes.WinError()
    
    result = ctypes.string_at(out_blob.pbData, out_blob.cbData)
    kernel32.LocalFree(out_blob.pbData)
    return result


# ─────────────────────────────────────────────────────────────
#  TIME BANK INTEGRITY (DPAPI Encrypted)
# ─────────────────────────────────────────────────────────────
def secure_save_time(seconds: int, file_path=TIME_BANK_FILE):
    """Saves time securely encrypted with Windows DPAPI."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        data = str(seconds).encode("utf-8")
        encrypted = encrypt_dpapi(data)
        with open(file_path, "wb") as f:
            f.write(encrypted)
    except Exception as e:
        print(f"[Security] Error saving time: {e}")

def secure_load_time(file_path=TIME_BANK_FILE) -> int:
    """Loads time and decrypts it. Resets to 0 if tampered or decryption fails."""
    try:
        if not os.path.exists(file_path):
            return 0
        with open(file_path, "rb") as f:
            raw_data = f.read()
        if not raw_data:
            return 0
        try:
            decrypted = decrypt_dpapi(raw_data)
            return int(decrypted.decode("utf-8"))
        except Exception:
            try:
                val = int(raw_data.decode("utf-8").strip())
                secure_save_time(val, file_path)
                return val
            except Exception:
                print("[Security] DPAPI Decryption failed for time_bank.txt. Resetting to 0.")
                secure_save_time(0, file_path)
                return 0
    except Exception as e:
        print(f"[Security] Unexpected error loading time: {e}")
        return 0


# ─────────────────────────────────────────────────────────────
#  PROGRESS DATA INTEGRITY (DPAPI Encrypted)
# ─────────────────────────────────────────────────────────────
def secure_save_progress(progress_data: dict, file_path=USER_PROGRESS_FILE):
    """Saves progress data securely encrypted with Windows DPAPI."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        clean_data = {k: v for k, v in progress_data.items() if k != '__hash__'}
        data = json.dumps(clean_data).encode("utf-8")
        encrypted = encrypt_dpapi(data)
        with open(file_path, "wb") as f:
            f.write(encrypted)
    except Exception as e:
        print(f"[Security] Error saving progress: {e}")

def secure_load_progress(file_path=USER_PROGRESS_FILE) -> dict:
    """Loads progress data and decrypts it. Resets to defaults if decryption fails."""
    fresh_progress = {
        "mastered_words": [],
        "learning_pool": {},
        "current_level": "Novice",
    }
    try:
        if not os.path.exists(file_path):
            return fresh_progress
        with open(file_path, "rb") as f:
            raw_data = f.read()
        if not raw_data:
            return fresh_progress
        
        # 1. Attempt DPAPI decryption
        try:
            decrypted = decrypt_dpapi(raw_data)
            data = json.loads(decrypted.decode("utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
            
        # 2. Fallback: parse as legacy unencrypted UTF-8 JSON
        try:
            data = json.loads(raw_data.decode("utf-8"))
            if isinstance(data, dict):
                secure_save_progress(data, file_path)
                return data
        except Exception:
            pass

        print("[Security] Decryption/parsing failed for user_progress.json. Resetting.")
        secure_save_progress(fresh_progress, file_path)
        return fresh_progress
    except Exception as e:
        print(f"[Security] Unexpected error loading progress: {e}")
        return fresh_progress


