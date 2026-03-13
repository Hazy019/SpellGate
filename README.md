# SPELLGATE: ARCADE KIOSK EDITION

**SPELLGATE** is a high-stakes educational kiosk that transforms screen time into a reward. Locked behind a neon-drenched retro aesthetic, users must prove their spelling mastery to earn every second of computer access.

> [!IMPORTANT]
> **SYSTEM LOCKED:** This application is designed to run in Fullscreen Kiosk Mode. It blocks system keys (Windows, Alt+Tab) to ensure the educational mission is completed.

---

## THE 3-PHASE CHALLENGE

1.  **PHASE 1: MEMORIZATION**
    *   Study 12 words curated by the **Google Gemini AI**.
    *   Listen to high-fidelity TTS pronunciations.
    *   *Goal:* Commit the sequence to memory before the timer hits zero.

2.  **PHASE 2: SEQUENTIAL RECALL**
    *   Type all 12 words in the exact order they appeared.
    *   **Economy:** `+5 Minutes` for every success | `-5 Minutes` for every error.

3.  **PHASE 3: SCRAMBLED FILL-IN**
    *   Solve C_t style puzzles for the mastered word list.
    *   Use hints wisely—they cost precious playtime!

---

## KIOSK SECURITY & CONTROLS

*   **HARD LOCK:** The application stay on top of all windows and suppresses the Windows Key, Alt+Tab, and Escape.
*   **AUTO-SHUTDOWN:** If the Draggable Timer hits `00:00:00`, the system triggers an OS-level shutdown command (`shutdown /s /t 60`).
*   **PARENT OVERRIDE:** Press `Ctrl + Shift + P` at any time to bypass the lock and exit the application.

---

## BUILDING THE EXECUTABLE (.EXE)

To transform the Python source code into a standalone arcade executable:

1.  **Install Build Tools:**
    ```bash
    pip install pyinstaller
    ```

2.  **Run the Build Script:**
    We've provided an automated script that handles asset bundling and formatting:
    ```bash
    python package_app.py
    ```

3.  **Result:** 
    Open the `dist` folder. You will find `SpellGate.exe` ready for kiosk deployment.

---

## INSTALLATION

1.  **Clone & Navigate:**
    ```bash
    git clone https://github.com/yourusername/SpellGate.git
    cd SpellGate
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure AI (Optional but Recommended):**
    Create a `gemini.env` file in the root directory:
    ```env
    GEMINI_API_KEY=your_api_key_here
    ```

4.  **Launch:**
    ```bash
    python main.py
    ```

---

## DESIGN SYSTEM

*   **Typography:** [Press Start 2P](https://fonts.google.com/specimen/Press+Start+2P)
*   **Palette:** 
    *   `#0a0a0a` (Deep Space)
    *   `#facc15` (Cyber Yellow)
    *   `#ff00ff` (Neon Magenta)
    *   `#22d3ee` (Electric Cyan)
    *   `#4ade80` (Arcade Green)

---

*Built for Grade 4 Scholars. Developed with Google DeepMind Advanced Agentic Coding.*
