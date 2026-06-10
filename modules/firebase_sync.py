import firebase_admin
from firebase_admin import credentials, firestore
import threading
import queue
import json
import os
from pathlib import Path
import platform
import datetime

# ─────────────────────────────────────────────────────────────
#  HOW TO GET serviceAccountKey.json:
#  1. Go to https://console.firebase.google.com
#  2. Open your SpellGate project
#  3. Click the gear icon → "Project Settings"
#  4. Go to the "Service Accounts" tab
#  5. Click "Generate new private key" → "Generate Key"
#  6. A .json file downloads — rename it serviceAccountKey.json
#  7. Place it in: SpellGate/SpellGate/serviceAccountKey.json
#  ⚠  NEVER share or commit this file. It has full admin access.
# ─────────────────────────────────────────────────────────────

# Path is relative to main.py location (SpellGate root folder)
SERVICE_ACCOUNT_PATH = os.path.join(os.path.dirname(__file__), "..", "serviceAccountKey.json")

# The local config file that stores the parent's UID after pairing
PAIRING_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "pairing.json")

_db = None
_parent_uid = None

# Offline queue: if sync fails, we hold data here and retry later
_offline_queue = queue.Queue()


# ─────────────────────────────────────────────────────────────
#  PAIRING — links this app install to a parent's account
# ─────────────────────────────────────────────────────────────

def load_parent_uid():
    """Load the stored parent UID from the local pairing file."""
    global _parent_uid
    try:
        with open(PAIRING_FILE, "r") as f:
            data = json.load(f)
            _parent_uid = data.get("parent_uid")
            print(f"[Firebase] Loaded parent UID: {_parent_uid}")
    except (FileNotFoundError, json.JSONDecodeError):
        _parent_uid = None
        print("[Firebase] No pairing file found. App is not linked to a parent account.")
    return _parent_uid


def save_parent_uid(uid: str):
    """Save the parent UID after a successful pairing."""
    global _parent_uid
    _parent_uid = uid
    os.makedirs(os.path.dirname(PAIRING_FILE), exist_ok=True)
    with open(PAIRING_FILE, "w") as f:
        json.dump({"parent_uid": uid}, f)
    print(f"[Firebase] Paired with parent UID: {uid}")


def pair_with_code(pairing_code: str) -> bool:
    """
    Given a 6-digit code the parent gets from the Dashboard,
    look it up in Firestore and save the parent's UID locally.
    Returns True on success, False on failure.
    """
    if not _db:
        print("[Firebase] Cannot pair — Firebase not initialized.")
        return False
    try:
        code_ref = _db.collection("pairing_codes").document(pairing_code)
        doc = code_ref.get()
        if doc.exists:
            uid = doc.to_dict().get("parent_uid")
            if uid:
                save_parent_uid(uid)
                # Delete the code so it can't be reused
                code_ref.delete()
                return True
        print(f"[Firebase] Pairing code '{pairing_code}' not found or expired.")
        return False
    except Exception as e:
        print(f"[Firebase] Pairing error: {e}")
        return False

def register_app_install():
    """Sends a heartbeat to Firestore so the Dashboard knows the app is installed and alive."""
    if not _db or not _parent_uid:
        return
        
    def _heartbeat():
        try:
            doc_ref = _db.collection('users').document(_parent_uid).collection('child_data').document('device')
            doc_ref.set({
                'installed': True,
                'install_date': datetime.datetime.utcnow().isoformat(),
                'hostname': platform.node(),
                'os_version': platform.version(),
                'app_version': '1.0.0',
                'last_heartbeat': firestore.SERVER_TIMESTAMP,
            }, merge=True)
            print("[Firebase] Sent heartbeat / app install registration.")
        except Exception as e:
            print(f"[Firebase] Heartbeat failed: {e}")
            
    threading.Thread(target=_heartbeat, daemon=True).start()

# ─────────────────────────────────────────────────────────────
#  INIT
# ─────────────────────────────────────────────────────────────

def init_firebase():
    """Initialize the Firebase Admin SDK using the service account key."""
    global _db
    key_path = os.path.normpath(SERVICE_ACCOUNT_PATH)

    if not os.path.exists(key_path):
        print(
            "[Firebase] ⚠  Sync DISABLED — serviceAccountKey.json not found.\n"
            "           To enable: download from Firebase Console →\n"
            "           Project Settings → Service Accounts → Generate new private key\n"
            f"           and place it at: {key_path}"
        )
        return

    try:
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred)
        _db = firestore.client()
        load_parent_uid()
        if _parent_uid:
            register_app_install()
        print("[Firebase] ✅ Initialized successfully.")
    except Exception as e:
        print(f"[Firebase] ❌ Failed to initialize: {e}")


# ─────────────────────────────────────────────────────────────
#  WRITE — Child progress UP to Firestore
# ─────────────────────────────────────────────────────────────

def sync_progress_to_cloud(progress_data: dict):
    """
    Push the child's progress to Firestore under the parent's UID.
    Runs on a background thread so it never blocks the game.
    If it fails, data is queued and retried on the next sync.
    """
    if not _db or not _parent_uid:
        _offline_queue.put(dict(progress_data))
        return

    def _upload():
        try:
            # Drain any previously failed syncs first
            while not _offline_queue.empty():
                queued = _offline_queue.get_nowait()
                _get_progress_ref().set(queued, merge=True)
                print("[Firebase] ✅ Retried queued sync.")

            # Upload the current data
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
    """
    Fetch game settings (reward multiplier, force_unlock flag, etc.)
    from Firestore. Calls `callback(config_dict)` on the background thread.
    """
    if not _db or not _parent_uid:
        return

    def _download():
        try:
            doc = _get_settings_ref().get()
            if doc.exists:
                config = doc.to_dict()
                print(f"[Firebase] ✅ Config fetched: {config}")
                if callback:
                    callback(config)
        except Exception as e:
            print(f"[Firebase] ❌ Failed to fetch config: {e}")

    threading.Thread(target=_download, daemon=True).start()


def check_force_unlock(on_unlock_callback):
    """
    Checks if the parent has pressed "Force Unlock" in the Dashboard.
    If yes, triggers the callback and resets the flag in Firestore.
    Call this every 60 seconds from the main game loop.
    """
    if not _db or not _parent_uid:
        return

    def _check():
        try:
            doc = _get_settings_ref().get()
            if doc.exists and doc.to_dict().get("force_unlock") is True:
                print("[Firebase] 🔓 Force unlock triggered by parent!")
                # Reset the flag
                _get_settings_ref().update({"force_unlock": False})
                if on_unlock_callback:
                    on_unlock_callback()
        except Exception as e:
            print(f"[Firebase] ❌ Force unlock check failed: {e}")

    threading.Thread(target=_check, daemon=True).start()


# ─────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────

def _get_progress_ref():
    """Returns the Firestore document ref for this child's progress."""
    return (
        _db.collection("users")
           .document(_parent_uid)
           .collection("child_data")
           .document("progress")
    )


def _get_settings_ref():
    """Returns the Firestore document ref for this family's game settings."""
    return (
        _db.collection("users")
           .document(_parent_uid)
           .collection("child_data")
           .document("settings")
    )


def is_connected() -> bool:
    """Returns True if Firebase is initialized and paired with a parent account."""
    return _db is not None and _parent_uid is not None
