import threading
import queue
import json
import os
import time
from pathlib import Path
import platform
import datetime
import requests
from google.cloud import firestore
from google.oauth2 import credentials

# ─────────────────────────────────────────────────────────────
#  FIREBASE CONFIGURATION
# ─────────────────────────────────────────────────────────────
FIREBASE_API_KEY = "AIzaSyBaxgMa1KjvF017XSfUFob0KBiJ2DmGQCo"
FIREBASE_PROJECT_ID = "spellgate-eb1e8"

_db           = None
_parent_uid   = None
_force_unlock_watch = None   # Firestore real-time listener handle
_token_refresh_timer = None

# Offline queue — if sync fails, hold data and retry on next call
_offline_queue = queue.Queue()

# ─────────────────────────────────────────────────────────────
#  AUTHENTICATION & INIT
# ─────────────────────────────────────────────────────────────

def init_firebase():
    """
    Initialize Firebase using the stored Refresh Token.
    Returns True if successful, False if no token or login required.
    """
    from modules.security import get_firebase_refresh_token
    refresh_token = get_firebase_refresh_token()
    
    if not refresh_token:
        print("[Firebase] No refresh token found. User must log in.")
        return False
        
    return _refresh_and_init(refresh_token)

def login_with_email(email, password):
    """
    Log in using Email and Password via Firebase Auth REST API.
    Returns (True, None) on success, (False, error_msg) on failure.
    """
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    
    try:
        resp = requests.post(url, json=payload)
        data = resp.json()
        
        if "error" in data:
            return False, data["error"].get("message", "Unknown error")
            
        id_token = data["idToken"]
        refresh_token = data["refreshToken"]
        local_id = data["localId"]
        
        from modules.security import set_firebase_refresh_token
        set_firebase_refresh_token(refresh_token)
        
        _init_firestore_client(id_token, local_id)
        _schedule_token_refresh(refresh_token, int(data.get("expiresIn", 3600)))
        register_app_install()
        return True, None
        
    except Exception as e:
        return False, str(e)

def _refresh_and_init(refresh_token):
    """Exchanges a refresh token for a new ID token and initializes Firestore."""
    url = f"https://securetoken.googleapis.com/v1/token?key={FIREBASE_API_KEY}"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    
    try:
        resp = requests.post(url, json=payload)
        data = resp.json()
        
        if "error" in data:
            print(f"[Firebase] Refresh token expired or invalid: {data['error']}")
            return False
            
        id_token = data["id_token"]
        new_refresh_token = data["refresh_token"]
        local_id = data["user_id"]
        
        from modules.security import set_firebase_refresh_token
        set_firebase_refresh_token(new_refresh_token)
        
        _init_firestore_client(id_token, local_id)
        _schedule_token_refresh(new_refresh_token, int(data.get("expires_in", 3600)))
        return True
        
    except Exception as e:
        print(f"[Firebase] Failed to refresh token: {e}")
        return False

def _init_firestore_client(id_token, uid):
    global _db, _parent_uid
    _parent_uid = uid
    cred = credentials.Credentials(token=id_token)
    _db = firestore.Client(project=FIREBASE_PROJECT_ID, credentials=cred)
    print(f"[Firebase] ✅ Initialized Firestore for user: {uid}")

def _schedule_token_refresh(refresh_token, expires_in):
    global _token_refresh_timer
    if _token_refresh_timer:
        _token_refresh_timer.cancel()
        
    # Refresh 5 minutes before expiry
    refresh_delay = max(0, expires_in - 300)
    _token_refresh_timer = threading.Timer(refresh_delay, _refresh_and_init, args=(refresh_token,))
    _token_refresh_timer.daemon = True
    _token_refresh_timer.start()

# ─────────────────────────────────────────────────────────────
#  PARENT PIN
# ─────────────────────────────────────────────────────────────

def fetch_parent_pin() -> str | None:
    """
    Fetch the parent's emergency override PIN from Firestore.
    Returns None if not set or offline.
    """
    if not _db or not _parent_uid:
        return None
    try:
        doc = _get_settings_ref().get()
        if doc.exists:
            pin = doc.to_dict().get("parent_pin")
            if pin:
                from modules.security import set_local_pin
                set_local_pin(str(pin))
                return str(pin)
    except Exception as e:
        print(f"[Firebase] Could not fetch PIN: {e}")
    return None

def set_parent_pin(pin: str):
    """
    Saves the PIN to Firestore and caches it locally.
    """
    from modules.security import set_local_pin
    set_local_pin(str(pin))
    
    if _db and _parent_uid:
        try:
            _get_settings_ref().set({"parent_pin": str(pin)}, merge=True)
        except Exception as e:
            print(f"[Firebase] Could not save PIN to cloud: {e}")

# ─────────────────────────────────────────────────────────────
#  FORCE UNLOCK — Real-time listener
# ─────────────────────────────────────────────────────────────

def start_force_unlock_listener(on_unlock_callback):
    """
    Start a Firestore real-time listener that fires when parent presses "Force Unlock".
    """
    global _force_unlock_watch
    if not _db or not _parent_uid:
        return None

    settings_ref = _get_settings_ref()

    def _on_snapshot(doc_snapshot, changes, read_time):
        for doc in doc_snapshot:
            if doc.exists and doc.to_dict().get("force_unlock") is True:
                print("[Firebase] 🔓 Force unlock received from parent!")
                try:
                    settings_ref.update({"force_unlock": False})
                except Exception:
                    pass
                if on_unlock_callback:
                    on_unlock_callback()

    try:
        _force_unlock_watch = settings_ref.on_snapshot(_on_snapshot)
        print("[Firebase] ✅ Force-unlock real-time listener active.")
        return _force_unlock_watch
    except Exception as e:
        print(f"[Firebase] ⚠ Could not start force-unlock listener: {e}")
        return None

def stop_force_unlock_listener():
    """Stop the real-time listener."""
    global _force_unlock_watch
    if _force_unlock_watch:
        try:
            _force_unlock_watch.unsubscribe()
        except Exception:
            pass
        _force_unlock_watch = None

def check_force_unlock(on_unlock_callback):
    start_force_unlock_listener(on_unlock_callback)

# ─────────────────────────────────────────────────────────────
#  DEVICE HEARTBEAT
# ─────────────────────────────────────────────────────────────

def register_app_install():
    """Send a heartbeat to Firestore so the Dashboard knows the app is installed."""
    if not _db or not _parent_uid:
        return

    def _heartbeat():
        try:
            doc_ref = (
                _db.collection('users')
                   .document(_parent_uid)
                   .collection('child_data')
                   .document('device')
            )
            doc_ref.set({
                'installed':        True,
                'install_date':     datetime.datetime.utcnow().isoformat(),
                'hostname':         platform.node(),
                'os_version':       platform.version(),
                'app_version':      '1.1.0',
                'last_heartbeat':   firestore.SERVER_TIMESTAMP,
            }, merge=True)
            print("[Firebase] Sent heartbeat / app install registration.")
        except Exception as e:
            print(f"[Firebase] Heartbeat failed: {e}")

    threading.Thread(target=_heartbeat, daemon=True).start()

# ─────────────────────────────────────────────────────────────
#  WRITE — Child progress UP to Firestore
# ─────────────────────────────────────────────────────────────

def sync_progress_to_cloud(progress_data: dict):
    if not _db or not _parent_uid:
        _offline_queue.put(dict(progress_data))
        return

    def _upload():
        try:
            while not _offline_queue.empty():
                queued = _offline_queue.get_nowait()
                _get_progress_ref().set(queued, merge=True)
            _get_progress_ref().set(progress_data, merge=True)
            print("[Firebase] ✅ Progress synced to cloud.")
        except Exception as e:
            print(f"[Firebase] ❌ Sync failed, re-queued: {e}")
            _offline_queue.put(dict(progress_data))

    threading.Thread(target=_upload, daemon=True).start()

# ─────────────────────────────────────────────────────────────
#  READ — Pull game settings DOWN from Firestore
# ─────────────────────────────────────────────────────────────

def fetch_config_from_cloud(callback):
    if not _db or not _parent_uid:
        return

    def _download():
        try:
            doc = _get_settings_ref().get()
            if doc.exists:
                config = doc.to_dict()
                if callback:
                    callback(config)
        except Exception as e:
            print(f"[Firebase] ❌ Failed to fetch config: {e}")

    threading.Thread(target=_download, daemon=True).start()

# ─────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────

def _get_progress_ref():
    return (
        _db.collection("users")
           .document(_parent_uid)
           .collection("child_data")
           .document("progress")
    )

def _get_settings_ref():
    return (
        _db.collection("users")
           .document(_parent_uid)
           .collection("child_data")
           .document("settings")
    )

def is_connected() -> bool:
    return _db is not None and _parent_uid is not None
