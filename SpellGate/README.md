# SPELLGATE 🚀 | Arcade Kiosk Edition

> **Transforming screen time into a hard-earned reward through AI-driven linguistic mastery.**

**SpellGate** is a high-stakes educational lock-screen and kiosk application designed for children. It locks system access behind a neon-drenched retro interface and gamifies screen time management by requiring the user to master spelling words to "earn" computer playtime. Once time is earned, a floating timer sits on the desktop, gracefully shutting down the PC when time runs out.

---

## 🎯 Core Features

*   **🔒 Kiosk Lockdown Mode**: Automatically locks the screen, disables the Windows key, Alt-Tab, and Task Manager (when run as Administrator). The child must spell words to unlock the PC.
*   **📈 Progressive Difficulty (Novice → Apprentice → Scholar)**: Tracks word mastery using a 3-strike system. The difficulty adapts as the child successfully spells words.
*   **🧠 Model Cascade Engine (Offline Resilient)**: Powered by Google's Gemini AI to generate custom, educational sentences for words.
    *   **Fallback Chain**: If the primary AI model fails (e.g., API quota reached), it automatically tries 2 fallback models.
    *   **100% Offline Support**: If the internet goes down or all API calls fail, the app falls back seamlessly to a built-in library of over 150+ curated spelling words and sentences across all difficulty tiers.
*   **⏳ Time Bank Persistence**: Earned playtime is saved locally (`LOCALAPPDATA`). If the PC restarts, the earned time is preserved.
*   **🔁 Spaced Repetition (Recall Stage)**: Seamlessly slips 1-2 previously mastered words back into the daily learning pool to test long-term retention. If they fail, they must re-master the word!
*   **🖥️ Floating Desktop Timer**: An always-on-top, draggable cyberpunk-styled timer that counts down earned time.
*   **🗣️ Audio Pronunciation (TTS)**: Uses a built-in zero-lag Text-to-Speech engine to read out words and sentences.

---

## 🔐 Kiosk Security & Control System

*   **Hard Lock:** Stays "Always on Top" and suppresses system hotkeys.
*   **Auto-Shutdown:** Executes an OS-level shutdown if the timer hits `00:00:00`.
*   **Parental Override:** Secure bypass via **`Ctrl + Shift + P`** from the kiosk screen.

### App Data Location
SpellGate stores user progress and time bank balances in the local application data directory. This ensures data survives app updates and is safely partitioned per Windows user.
*   **Path**: `C:\Users\[Username]\AppData\Local\SpellGate`
*   `user_progress.json` - Tracks mastered words and current difficulty level. Delete this to wipe the child's progress.
*   `time_bank.txt` - Tracks the remaining seconds of playtime. You can manually edit this file to grant bonus time or penalize time.

---

## 🛠️ Technical Implementation & Deployment

SpellGate is built using Python, `PyQt6`, and `PyInstaller`. It compiles down into a **single portable executable (`SpellGate.exe`)** that does not require Python or any dependencies to be installed on the target machine.

### ⚙️ Requirements (For Developers)
*   Python 3.12+
*   Windows 10 / 11
*   A Google Gemini API Key placed in a `gemini.env` file (Optional, required only for dynamic sentence generation).

### Step 1: Building the Executable
If you are compiling from source on your main PC:

1. **Clone the Repository:**
   ```cmd
   git clone https://github.com/Hazy019/SpellGate.git
   ```
2. **Install Dependencies:**
   ```cmd
   pip install -r requirements.txt
   ```
3. **Run the build script:**
   ```cmd
   python package_app.py
   ```
4. A single `SpellGate.exe` file will be generated in the `dist/` folder.

### Step 2: Deploying to the Child's PC
1. Copy the built `dist/SpellGate.exe` to the child's Windows machine (e.g., via USB drive or Network Share).
2. Right-click the executable and select **"Run as Administrator"**.
   > *Note: Administrator privileges are required for the low-level keyboard hooks to block `Windows Key`, `Alt+Tab`, and other system shortcuts.*
3. (Optional) **Set to auto-launch on startup**:
   * Press `Win + R`, type `shell:startup`, and press Enter.
   * Create a shortcut to `SpellGate.exe` in this folder.
   * Right-click the shortcut → **Properties** → **Advanced** → Check **"Run as administrator"**.

---

## 🎨 Design System

*   **Typography:** Press Start 2P
*   **Success/Safe:** `#4ADE80` (Arcade Green)
*   **Theme:** Neon-drenched Retro / Cyberpunk

---

## 👨‍💻 Development Credits

**Lead Developer:** Kyrell Santillan
