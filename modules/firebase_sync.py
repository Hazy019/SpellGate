import firebase_admin
from firebase_admin import credentials, firestore
import threading
import json
import os

# To make this real, download a serviceAccountKey.json from Firebase Console
# and place it in the same directory or set the path in config.
SERVICE_ACCOUNT_PATH = "serviceAccountKey.json"

_db = None

def init_firebase():
    global _db
    if not os.path.exists(SERVICE_ACCOUNT_PATH):
        print("Firebase sync disabled: serviceAccountKey.json not found.")
        return
        
    try:
        cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred)
        _db = firestore.client()
        print("Firebase initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize Firebase: {e}")

def sync_progress_to_cloud(progress_data):
    """Sync the user's progress up to Firestore."""
    if not _db: return
    
    def _upload():
        try:
            # Assuming a generic user ID 'child_1' for now
            doc_ref = _db.collection('users').document('child_1')
            doc_ref.set(progress_data, merge=True)
            print("Successfully synced progress to cloud.")
        except Exception as e:
            print(f"Failed to sync to cloud: {e}")
            
    threading.Thread(target=_upload, daemon=True).start()

def fetch_config_from_cloud(callback):
    """Fetch settings (like the reward multiplier) from Firestore."""
    if not _db: return
    
    def _download():
        try:
            doc_ref = _db.collection('config').document('game_settings')
            doc = doc_ref.get()
            if doc.exists:
                config = doc.to_dict()
                if callback:
                    callback(config)
        except Exception as e:
            print(f"Failed to fetch config from cloud: {e}")
            
    threading.Thread(target=_download, daemon=True).start()
