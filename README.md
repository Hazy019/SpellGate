# SpellGate

**SpellGate** is an educational screen-time management system that gamifies spelling. It consists of a robust, kiosk-mode Windows application for children and a real-time web dashboard for parents.

By intercepting screen time, SpellGate requires children to complete spelling challenges powered by a dynamic AI engine before they can unlock their PC. Parents can monitor progress in real-time, adjust rewards, and force-unlock the machine remotely.

---

## 🏗️ Architecture

SpellGate is built on a two-part architecture, synced instantly via Firebase:

1. **SpellGate Client (Python/PyQt6)**
   - A locked-down kiosk application installed on the child's Windows PC.
   - **AI Engine:** Uses a 3-model Gemini API cascade (Flash → Flash-Lite) to dynamically generate spelling challenges based on the child's mastery level.
   - **Offline Resilience:** Includes a static offline word bank and a local data queue. If the internet drops, progress is queued and synced automatically once reconnected.
   - **Security:** Utilizes Windows Registry Run Keys, a background Watchdog process to prevent Task Manager bypasses, and HMAC-SHA256 file signing to prevent local data tampering.

2. **Parent Dashboard (React/Vite)**
   - A responsive, cyber-themed web portal for parents.
   - **Real-time Data:** Uses Firebase `onSnapshot` listeners to stream the child's progress, accuracy, and earned screen time live.
   - **Controls:** Allows parents to adjust the "Screen Time Exchange Rate" (e.g., 1 word = 30 seconds) and trigger remote unlocks.

---

## ✨ Key Features

- **Adaptive Difficulty:** Automatically levels up the child (Novice → Apprentice → Scholar) as they master words.
- **Tamper-Proof Kiosk:** Aggressive system hooks suppress `Alt+Tab`, `Alt+F4`, and `Ctrl+Shift+Esc` to prevent the child from bypassing the lock screen.
- **Emergency Override:** A PIN-protected bypass (`Ctrl+Shift+P`) allows parents to use the locked PC instantly.
- **Remote Force Unlock:** Parents can click a button on the web dashboard to instantly unlock the child's PC from their phone.
- **Pairing System:** Secure 6-digit pairing codes securely link a child's local Windows installation to a parent's Firebase account.

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.12+**
- **Node.js 18+**
- A **Firebase** project with Authentication (Email/Password) and Firestore Database enabled.
- A **Google Gemini API Key**.

### 2. Parent Dashboard Setup
```bash
cd ParentDashboard
npm install

# Create a .env file with your Firebase config
# VITE_FIREBASE_API_KEY="..."
# VITE_FIREBASE_AUTH_DOMAIN="..."
# ...

npm run dev
```

### 3. Python Client Setup
```bash
cd SpellGate
python -m venv .env
.env\Scripts\activate
pip install -r requirements.txt

# Securely store your Gemini API Key in Windows Credential Manager:
# python -c "import keyring; keyring.set_password('SpellGate', 'gemini_api_key', 'YOUR_KEY_HERE')"

# Add your Firebase serviceAccountKey.json to the SpellGate root folder.

python main.py
```

### 4. Compiling the Executable
To package the Python app into a standalone `.exe` for distribution:
```bash
pyinstaller SpellGate.spec
```

---

## 🔒 Security Posture
- **API Keys:** Never bundled in the executable. Fetched at runtime via OS credential manager.
- **Database Rules:** Firestore strictly locks read/write access so users can only view their own family's data.
- **File Integrity:** All local JSON and text files are cryptographically signed to prevent manual edits.
