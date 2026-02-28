# SpellGate: Gamified Screen Lock

**SpellGate** is an educational productivity tool designed to transform computer screen time into a reward for learning. Built with Python and PyQt6, the application locks the Windows environment in a secure Kiosk mode upon startup. To unlock the PC, the user must successfully complete a 3-phase spelling bee.

Correct answers reward the user with banked computer playtime, while mistakes deduct time, teaching both spelling mastery and resource management.

## Key Features

* **Secure Kiosk Lock:** Utilizes keyboard hooks and frameless window generation to lock the system until the educational module is complete.

* **3-Phase Learning System:**

    * **Phase 1 (Memorize):** Interactive flashcards with AI Text-to-Speech pronunciation.

    * **Phase 2 (Recall):** Sequential recall typing to build memory muscle.

    * **Phase 3 (Scrambled):** Randomized puzzle-solving with dynamic letter hiding based on word length.

* **Time-Bank Economy:** A mathematically balanced reward system (+5 mins for correct, -3 mins for errors, -1 min for hints).

* **Smart AI Teacher (The Bridge):** Tracks strikes and attempts in a JSON database, automatically promoting mastered words and pulling new challenges from a CSV master library.

* **Draggable UI Tracker:** Upon unlocking, a sleek, draggable overlay remains on the screen, tracking the remaining earned playtime (HH:MM:SS).

## Tech Stack

* **Language:** Python 3.x
* **GUI Framework:** PyQt6
* **Audio Engine:** pyttsx3 (with queue threading and COM initialization for SAPI5 stability)
* **System Control:** keyboard, os, pywin32

## Audio Subsystem

Text-to-speech is provided via ``pyttsx3`` but the Windows SAPI5 engine is
not thread-safe.  To prevent crashes when users click rapidly we employ a
producer/consumer queue:

* UI code calls ``modules.audio.play_audio(text)`` which quickly enqueues the
  phrase.
* A dedicated background thread initializes COM (``pythoncom.CoInitialize()``)
  and processes the queue one item at a time, calling ``engine.say`` and
  ``engine.runAndWait()``.

This keeps audio off the main Qt thread, avoids overlapping runloops, and
makes the app stable even under rapid user interaction.


## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yourusername/SpellGate.git](https://github.com/yourusername/SpellGate.git)
   cd SpellGate
