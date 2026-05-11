# SPELLGATE: Arcade Kiosk Edition

> **Transforming screen time into a hard-earned reward through AI-driven linguistic mastery.**

SPELLGATE is a high-stakes educational kiosk application that locks system access behind a neon-drenched retro interface. To earn computer playtime, users must prove their spelling proficiency through a rigorous, multi-phase challenge.

---

## Kiosk Security & Control System

This application is engineered for **Fullscreen Kiosk Mode**. It is designed to act as a system wrapper with the following security features:

* **Hard Lock:** Stays "Always on Top" and suppresses system hotkeys (`Windows Key`, `Alt+Tab`, `Esc`).
* **Auto-Shutdown:** If the session timer reaches `00:00:00`, the application executes an OS-level shutdown command (`shutdown /s /t 60`).
* **Parental Override:** Secure bypass available via `Ctrl + Shift + P` to exit the application and restore system control.

---

## The 3-Phase Challenge

The core gameplay loop is designed to maximize retention through three distinct cognitive stages:

### **Phase 1: Memorization**
* **AI Curation:** 12 dynamic words generated via **Google Gemini AI**.
* **Auditory Learning:** High-fidelity Text-to-Speech (TTS) for pronunciation mastery.
* **Goal:** Commit the sequence to memory before the countdown expires.

### **Phase 2: Sequential Recall**
* **Precision Entry:** Users must type the full list in the exact order appeared.
* **Time Economy:** Earn `+5 Minutes` per success; penalized `-5 Minutes` per error.

### **Phase 3: Scrambled Fill-In**
* **Pattern Recognition:** Solve complex "fill-in-the-blank" puzzles based on the mastered word list.
* **Strategic Hints:** Hints are available but cost precious earned playtime.

---

## Technical Implementation

### **Prerequisites**
* Python 3.x
* Google Gemini API Key (for dynamic word generation)

### **Installation**
1. **Clone the Repository:**
   ```bash
   git clone [https://github.com/Hazy019/SpellGate.git](https://github.com/Hazy019/SpellGate.git)
   cd SpellGate
