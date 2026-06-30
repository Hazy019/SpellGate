"""
SpellGate Watchdog — Redesigned as an internal daemon thread.

WHY THIS IS BETTER:
  - Old design: separate subprocess → visible CMD window, kid can kill it,
    dies if the game never starts in the first place.
  - New design: daemon thread INSIDE SpellGate.exe → completely invisible,
    no process to kill, always alive as long as the EXE is alive.

HOW IT WORKS:
  - MainWindow calls watchdog.tick() every second via QTimer.
  - This thread checks that tick() was called within the last N seconds.
  - If it wasn't (process frozen/hung), it relaunches SpellGate.exe.
  - On intentional exit (PIN override, playtime), call authorize_exit()
    so the watchdog doesn't fight the legitimate close.

CRASH RECOVERY:
  - If the whole process dies (crash), the Task Scheduler restart policy
    (set up by the installer) brings it back. The watchdog thread handles
    soft-freezes and hung UI scenarios.
"""

import threading
import time
import subprocess
import sys

# How often the watchdog checks the heartbeat (seconds)
_CHECK_INTERVAL = 5

# Max seconds without a heartbeat before declaring the app hung
_HEARTBEAT_TIMEOUT = 15


class WatchdogThread(threading.Thread):
    """
    Daemon thread that monitors the SpellGate UI heartbeat.
    Runs inside SpellGate.exe — no separate process, no CMD window.
    """

    def __init__(self):
        super().__init__(daemon=True, name="SpellGate-Watchdog")
        self._stop_event = threading.Event()
        self._authorized_exit = threading.Event()
        self._last_heartbeat = time.monotonic()
        self._lock = threading.Lock()

        # Path to this EXE (only valid when frozen/compiled)
        if getattr(sys, 'frozen', False):
            self._exe_path = sys.executable
        else:
            self._exe_path = None  # Dev mode — don't auto-relaunch

    # ── Public API ────────────────────────────────────────────

    def tick(self):
        """
        Called every second by the Qt timer in main.py.
        Tells the watchdog: "the UI is still alive and responsive."
        """
        with self._lock:
            self._last_heartbeat = time.monotonic()

    def authorize_exit(self):
        """
        Call this BEFORE any intentional app close (PIN override, playtime,
        uninstall). Tells the watchdog: "don't relaunch when we die."
        """
        self._authorized_exit.set()

    def stop(self):
        """Gracefully stop the watchdog thread."""
        self._authorized_exit.set()
        self._stop_event.set()

    # ── Thread body ───────────────────────────────────────────

    def run(self):
        """
        Checks heartbeat every _CHECK_INTERVAL seconds.
        If the heartbeat is stale AND exit wasn't authorised → relaunch.
        """
        while not self._stop_event.wait(_CHECK_INTERVAL):
            if self._authorized_exit.is_set():
                break

            with self._lock:
                age = time.monotonic() - self._last_heartbeat

            if age > _HEARTBEAT_TIMEOUT:
                self._relaunch()
                break  # Our process is about to die anyway

    def _relaunch(self):
        """Silently relaunch SpellGate.exe — no CMD window, no flash."""
        if not self._exe_path:
            return  # Dev mode — nothing to relaunch
        try:
            subprocess.Popen(
                [self._exe_path],
                creationflags=subprocess.CREATE_NO_WINDOW
                              | subprocess.DETACH_PROCESS,
                close_fds=True,
            )
        except Exception:
            pass  # Can't log here — process is dying
