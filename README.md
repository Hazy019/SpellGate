# SpellGate 🚀 | Educational Screen-Time Management Kiosk

> **Transforming screen time into a hard-earned reward through AI-driven linguistic mastery.**

**SpellGate** is an educational screen-time management system that gamifies spelling. It consists of a robust, kiosk-mode Windows application for children (Python/PyQt6) and a real-time web dashboard for parents (React/Vite/Firebase).

By intercepting screen time, SpellGate requires children to complete spelling challenges powered by a dynamic AI cascade engine before they can unlock their PC. Parents can monitor progress in real-time, adjust rewards, and force-unlock the machine remotely.

---

## 🏗️ Project Architecture & Directory Layout

The workspace is organized into a single unified repository containing both frontend and backend modules:

```text
SpellGate/ (Workspace Root)
├── .git/                 # Git repository configuration (hidden)
├── ParentDashboard/      # Parent Dashboard (React + Vite + Firebase)
│   ├── src/              # React components & pages
│   ├── public/           # Static assets
│   ├── firebase.json     # Firebase deployment configuration
│   └── package.json      # Node.js dependencies & scripts
├── SpellGate/            # Child Kiosk client (Python + PyQt6)
│   ├── assets/           # UI fonts, logo images, offline word bank, audio
│   ├── modules/          # Core Python modules (game logic, kiosk lock, security, sync)
│   ├── main.py           # Main application entry point
│   ├── watchdog.py       # Security watchdog daemon script
│   └── requirements.txt  # Python package requirements
├── installer/            # Inno Setup compilation directory
│   ├── SpellGateSetup.exe # Compiled installer executable
│   └── SpellGateSetup.iss # Inno Setup compiler script
└── README.md             # Project documentation (this file)
```

---

## ✨ Key Features

### 1. SpellGate Child Client (Python)
*   **🔒 Kiosk Lockdown Mode**: Automatically locks the screen, disables the Windows key, Alt-Tab, and Task Manager (when run as Administrator). The child must spell words to unlock the PC.
*   **📈 Adaptive Difficulty**: Tracks word mastery using a 3-strike system. The difficulty adapts as the child successfully spells words (Novice → Apprentice → Scholar).
*   **🧠 Model Cascade Engine (Offline Resilient)**: Powered by Google's Gemini AI cascade to generate custom, educational sentences. If the primary AI model fails, it automatically tries 2 fallback models.
*   **🔌 100% Offline Support**: If the internet goes down, the app falls back seamlessly to a built-in library of over 150+ curated spelling words and sentences across all difficulty tiers.
*   **⏳ Time Bank Persistence**: Earned playtime is saved locally (`LOCALAPPDATA`). If the PC restarts, the earned time is preserved.
*   **🔁 Spaced Repetition (Recall Stage)**: Seamlessly slips 1-2 previously mastered words back into the daily learning pool to test long-term retention. If they fail, they must re-master the word!
*   **🖥️ Floating Desktop Timer**: An always-on-top, draggable cyberpunk-styled timer that counts down earned time.
*   **🗣️ Audio Pronunciation (TTS)**: Uses a built-in zero-lag Text-to-Speech engine to read out words and sentences.

### 2. Parent Web Dashboard (React)
*   **📊 Real-time Data Sync**: Uses Firebase `onSnapshot` listeners to stream the child's progress, accuracy, and remaining screen time live.
*   **🎛️ Remote Force Unlock**: Parents can click a button on the web dashboard to instantly unlock the child's PC from their phone or computer.
*   **⚙️ Custom Exchange Rates**: Allows parents to adjust the "Screen Time Exchange Rate" (e.g., 1 correct spelling word = 30 seconds of playtime).
*   **🔑 Secure Pairing**: Secure 6-digit pairing codes securely link a child's local Windows installation to a parent's Firebase account.

---

## 🚀 Getting Started

### 📋 Prerequisites
*   **Python 3.12+**
*   **Node.js 18+**
*   A **Firebase** project with Firestore Database and Email/Password Authentication enabled.
*   A **Google Gemini API Key**.

---

### 💻 1. Parent Dashboard Setup (React)

1. Navigate to the dashboard directory:
   ```bash
   cd ParentDashboard
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Create a `.env` file in the `ParentDashboard` directory and populate it with your Firebase configuration:
   ```env
   VITE_FIREBASE_API_KEY="your_api_key"
   VITE_FIREBASE_AUTH_DOMAIN="your_project.firebaseapp.com"
   VITE_FIREBASE_PROJECT_ID="your_project_id"
   VITE_FIREBASE_STORAGE_BUCKET="your_project.appspot.com"
   VITE_FIREBASE_MESSAGING_SENDER_ID="your_sender_id"
   VITE_FIREBASE_APP_ID="your_app_id"
   ```
4. Run the development server:
   ```bash
   npm run dev
   ```

#### 🌐 Firebase Hosting Deployment
To deploy the parent dashboard live to Firebase Hosting:
1. Install the Firebase CLI:
   ```bash
   npm install -g firebase-tools
   ```
2. Authenticate and initialize hosting:
   ```bash
   firebase login
   firebase init hosting
   # Select your Firebase project, set "dist" as public directory, and configure as a single-page app.
   ```
3. Build and deploy:
   ```bash
   npm run build
   firebase deploy --only hosting
   ```

---

### 🐍 2. Child Client Setup & Build (Python)

1. Navigate to the client directory:
   ```bash
   cd SpellGate
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .env
   .env\Scripts\activate
   ```
3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Add your Firebase `serviceAccountKey.json` into the `SpellGate` folder.
5. Securely store your Gemini API Key in the Windows Credential Manager:
   ```powershell
   python -c "import keyring; keyring.set_password('SpellGate', 'gemini_api_key', 'YOUR_KEY_HERE')"
   ```
6. Run the application:
   ```bash
   python main.py
   ```

#### 📦 Compiling the Standalone Executable (`.exe`)
To package the Python application into a single executable that runs without Python installed:
```powershell
pyinstaller SpellGate.spec
```
The built `SpellGate.exe` will be located inside the `dist/` directory.

---

## 🔒 Security & Data Persistence

*   **API Keys**: Never bundled in the executable. Fetched securely at runtime via the Windows OS credential manager.
*   **Database Rules**: Firestore security rules lock read/write access so parents can only view and modify their own family's pairing codes and session data.
*   **Local Persistence**: Kiosk progress data is stored in the user's local AppData folder:
    *   **Path**: `C:\Users\[Username]\AppData\Local\SpellGate`
    *   `user_progress.json`: Stores difficulty levels and spelling progress.
    *   `time_bank.txt`: Tracks remaining play time.
*   **Watchdog Security**: A background watchdog process prevents children from closing the kiosk process via Task Manager or other bypass tools.

---

## 🎨 Theme & Typography

*   **Typography**: *Press Start 2P* for retro-arcade gaming aesthetic, paired with *Outfit* for modern sleek dashboard design.
*   **Color Palette**: Sleek neon cyberpunk, featuring `#4ADE80` (Arcade Green) and `#9333EA` (Cyber Purple).

---

## 👨‍💻 Development & Author Credits

SpellGate is designed, engineered, and maintained by **[Kyrell Santillan (Hazy019)](https://github.com/Hazy019)**.
*   **GitHub**: [@Hazy019](https://github.com/Hazy019)
*   **Email**: [kyrell0602@gmail.com](mailto:kyrell0602@gmail.com)
*   **Role**: Lead Architect & Developer

