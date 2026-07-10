import queue
import threading
import pyttsx3
import time

# ── Queues ────────────────────────────────────────────────────────────────────
# Each item in speech_queue is a tuple: (text: str, on_done: callable | None)
speech_queue: queue.Queue = queue.Queue()

# Thread-safe callback queue: worker posts callables here after speech ends.
# The UI thread polls this via a QTimer to fire them on the main thread.
done_callbacks: queue.Queue = queue.Queue()


def _make_engine():
    """Create and configure a pyttsx3 engine with best available voice."""
    engine = pyttsx3.init()
    engine.setProperty("rate", 120)   # 120 wpm — clear and deliberate
    engine.setProperty("volume", 1.0)

    # Prefer Zira (natural female EN-US) → David (male EN-US) → whatever's there
    chosen = None
    for voice in engine.getProperty("voices"):
        vname = voice.name
        if "Zira" in vname:
            chosen = voice.id
            break
        if "David" in vname and chosen is None:
            chosen = voice.id
    if chosen:
        engine.setProperty("voice", chosen)
    return engine


def _audio_worker() -> None:
    """
    Background thread — pulls (text, on_done) tuples from speech_queue.
    Speaks text, then posts on_done to done_callbacks so the UI thread can
    safely re-enable buttons without any cross-thread Qt calls.
    """
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except ImportError:
        pass

    engine = None
    try:
        engine = _make_engine()
    except Exception as e:
        print(f"[Audio] TTS init failed: {e}")

    while True:
        item = speech_queue.get()

        # Support both old-style plain strings and new-style (text, callback) tuples
        if item is None:          # poison-pill → clean shutdown
            break
        if isinstance(item, str):
            text, on_done, slow = item, None, False
        elif len(item) == 2:
            text, on_done = item
            slow = False
        else:
            text, on_done, slow = item

        if engine is None:
            speech_queue.task_done()
            if on_done:
                done_callbacks.put(on_done)
            continue

        try:
            # Drain only plain-string stale entries (don't discard queued callbacks)
            while not speech_queue.empty():
                try:
                    stale = speech_queue.get_nowait()
                    if stale is None:
                        speech_queue.put(None)
                        break
                    # If stale item had its own callback, fire it immediately (no speech)
                    if isinstance(stale, tuple):
                        stale_cb = stale[1] if len(stale) >= 2 else None
                        if stale_cb:
                            done_callbacks.put(stale_cb)
                    speech_queue.task_done()
                except queue.Empty:
                    break

            if slow:
                engine.setProperty("rate", 60)
            else:
                engine.setProperty("rate", 120)

            parts = text.split("<PAUSE>")
            for i, part in enumerate(parts):
                part = part.strip()
                if part:
                    engine.say(part)
                    engine.runAndWait()
                if i < len(parts) - 1:
                    time.sleep(1)   # 1-second gap between word and sentence

        except RuntimeError:
            # Engine died externally — rebuild and retry once
            try:
                engine = _make_engine()
                if slow:
                    engine.setProperty("rate", 60)
                else:
                    engine.setProperty("rate", 120)

                parts = text.split("<PAUSE>")
                for i, part in enumerate(parts):
                    part = part.strip()
                    if part:
                        engine.say(part)
                        engine.runAndWait()
                    if i < len(parts) - 1:
                        time.sleep(1)
            except Exception as reinit_err:
                print(f"[Audio] Re-init failed: {reinit_err}")

        finally:
            speech_queue.task_done()
            if on_done:
                # Post to done_callbacks so the Qt main thread can pick it up safely
                done_callbacks.put(on_done)


# Start the singleton worker thread
_worker_thread = threading.Thread(target=_audio_worker, daemon=True)
_worker_thread.start()


def play_audio(text: str, on_done=None, slow: bool = False) -> None:
    """
    Enqueue text for speech synthesis (non-blocking).

    Args:
        text:    The text to speak.
        on_done: Optional callable fired on the Qt main thread after speech
                 finishes.  Use this to re-enable buttons, etc.
        slow:    If True, sets speech rate to 60 (half speed).
    """
    if text:
        speech_queue.put((text, on_done, slow))


def stop_audio() -> None:
    """Gracefully stop the audio worker (send poison-pill)."""
    speech_queue.put(None)
