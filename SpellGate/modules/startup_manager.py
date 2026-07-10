import os
import sys
import winreg
import win32com.client
import datetime

# ─────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────

def _get_exe_path() -> str:
    """Return the path of the running EXE (or script in dev mode)."""
    if getattr(sys, 'frozen', False):
        return sys.executable
    return os.path.abspath(sys.argv[0])


# ─────────────────────────────────────────────────────────────
#  METHOD 1 — HKCU Registry Run Key (user-level, always written)
# ─────────────────────────────────────────────────────────────

def _install_hkcu_run_key(exe_path: str):
    """
    Write to HKCU\\..\\Run.
    Value is a properly-quoted path — no 'cmd /c' wrapper, no shell.
    This alone is removable by the user from Task Manager > Startup,
    but it's a reliable baseline.
    """
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        # Always quote the path — spaces in path would break it otherwise
        winreg.SetValueEx(key, "SpellGate", 0, winreg.REG_SZ, f'"{exe_path}"')
        winreg.CloseKey(key)
        print("[Startup] HKCU Run key written.")
        return True
    except Exception as e:
        print(f"[Startup] HKCU Run key failed: {e}")
        return False


# ─────────────────────────────────────────────────────────────
#  METHOD 2 — HKLM Registry Run Key (system-level, requires admin)
#  Harder for the kid to remove — needs admin to delete from HKLM.
# ─────────────────────────────────────────────────────────────

def _install_hklm_run_key(exe_path: str):
    """
    Write to HKLM\\..\\Run (requires elevated privileges).
    Survives even if the user deletes the HKCU key.
    Silently skipped if not running as admin.
    """
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "SpellGate", 0, winreg.REG_SZ, f'"{exe_path}"')
        winreg.CloseKey(key)
        print("[Startup] HKLM Run key written (admin privilege confirmed).")
        return True
    except PermissionError:
        print("[Startup] HKLM Run key skipped — not running as admin (expected in user mode).")
        return False
    except Exception as e:
        print(f"[Startup] HKLM Run key failed: {e}")
        return False


# ─────────────────────────────────────────────────────────────
#  METHOD 3 — Task Scheduler (most robust)
#  - Runs at SYSTEM level (or user level if no admin)
#  - Built-in restart policy: restarts if the process dies
#  - NOT visible in the Startup tab of Task Manager
# ─────────────────────────────────────────────────────────────

def _install_task_scheduler(exe_path: str):
    """
    Register SpellGate in Windows Task Scheduler.
    Key properties:
    - Trigger: At user logon
    - Restart if fails: every 30s, up to 999 times
    - Hidden from Task Scheduler UI (Hidden = True)
    - Runs with highest available privileges
    """
    try:
        scheduler = win32com.client.Dispatch("Schedule.Service")
        scheduler.Connect()
        root_folder = scheduler.GetFolder("\\")
        task_def = scheduler.NewTask(0)

        # Principal (run as current user with highest privilege)
        principal = task_def.Principal
        principal.RunLevel = 1   # TASK_RUNLEVEL_HIGHEST

        # Logon trigger
        triggers = task_def.Triggers
        trigger = triggers.Create(9)   # TASK_TRIGGER_LOGON
        trigger.Enabled = True

        # Action
        actions = task_def.Actions
        action = actions.Create(0)     # TASK_ACTION_EXEC
        action.Path = exe_path
        action.WorkingDirectory = os.path.dirname(exe_path)

        # Settings
        settings = task_def.Settings
        settings.Enabled = True
        settings.Hidden = True                  # Not visible in UI
        settings.DisallowStartIfOnBatteries = False
        settings.StopIfGoingOnBatteries = False
        settings.ExecutionTimeLimit = "PT0S"    # No time limit

        # ── Restart policy: restart up to 999× every 30 seconds ──
        settings.RestartCount    = 999
        settings.RestartInterval = "PT30S"

        # ── Multi-instance: stop existing before starting new ──
        settings.MultipleInstances = 3  # TASK_INSTANCES_STOP_EXISTING

        # Register (TASK_CREATE_OR_UPDATE = 6, TASK_LOGON_INTERACTIVE_TOKEN = 3)
        root_folder.RegisterTaskDefinition(
            "SpellGate Security Monitor",
            task_def,
            6,   # TASK_CREATE_OR_UPDATE
            "", "", 3  # TASK_LOGON_INTERACTIVE_TOKEN
        )
        print("[Startup] Task Scheduler entry created with restart policy.")
        return True
    except Exception as e:
        print(f"[Startup] Task Scheduler registration failed: {e}")
        return False


# ─────────────────────────────────────────────────────────────
#  METHOD 4 — Startup Folder Shortcut (lowest-priority backup)
# ─────────────────────────────────────────────────────────────

def _install_startup_folder(exe_path: str):
    """Create a .lnk shortcut in the user's Startup folder as a last resort."""
    startup_dir = os.path.join(
        os.environ.get("APPDATA", ""),
        "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
    )
    shortcut_path = os.path.join(startup_dir, "SpellGate.lnk")
    try:
        if not os.path.exists(shortcut_path):
            shell     = win32com.client.Dispatch("WScript.Shell")
            shortcut  = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath        = exe_path
            shortcut.WorkingDirectory  = os.path.dirname(exe_path)
            shortcut.IconLocation      = exe_path
            shortcut.save()
            print(f"[Startup] Startup folder shortcut created: {shortcut_path}")
        return True
    except Exception as e:
        print(f"[Startup] Startup folder shortcut failed: {e}")
        return False


# ─────────────────────────────────────────────────────────────
#  PUBLIC API
# ─────────────────────────────────────────────────────────────

def install_to_startup():
    """
    Register SpellGate with all available persistence mechanisms.
    Tries the strongest method first, falls back on failure.

    Priority (strongest → weakest):
      1. Task Scheduler  — restart policy, hidden, admin-hard-to-remove
      2. HKLM Run key   — survives user-level deletion attempts
      3. HKCU Run key   — always works, user-removable from Startup tab
      4. Startup folder — last resort shortcut

    All methods that succeed are registered simultaneously for redundancy.
    """
    exe_path = _get_exe_path()
    print(f"[Startup] Registering persistence for: {exe_path}")

    results = {
        "task_scheduler": _install_task_scheduler(exe_path),
        "hklm_run_key":   _install_hklm_run_key(exe_path),
        "hkcu_run_key":   _install_hkcu_run_key(exe_path),
        "startup_folder": _install_startup_folder(exe_path),
    }

    successes = [k for k, v in results.items() if v]
    print(f"[Startup] Active persistence methods: {', '.join(successes) or 'NONE — startup may not work!'}")
    return len(successes) > 0


def remove_from_startup():
    """
    Remove all SpellGate persistence entries.
    Called by the uninstaller.
    """
    exe_path = _get_exe_path()

    # Remove HKCU key
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, "SpellGate")
        winreg.CloseKey(key)
        print("[Startup] HKCU Run key removed.")
    except Exception:
        pass

    # Remove HKLM key (requires admin)
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, "SpellGate")
        winreg.CloseKey(key)
        print("[Startup] HKLM Run key removed.")
    except Exception:
        pass

    # Remove Task Scheduler entry
    try:
        scheduler = win32com.client.Dispatch("Schedule.Service")
        scheduler.Connect()
        root_folder = scheduler.GetFolder("\\")
        root_folder.DeleteTask("SpellGate Security Monitor", 0)
        print("[Startup] Task Scheduler entry removed.")
    except Exception:
        pass

    # Remove startup folder shortcut
    try:
        startup_dir = os.path.join(
            os.environ.get("APPDATA", ""),
            "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
        )
        shortcut_path = os.path.join(startup_dir, "SpellGate.lnk")
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
            print("[Startup] Startup folder shortcut removed.")
    except Exception:
        pass
