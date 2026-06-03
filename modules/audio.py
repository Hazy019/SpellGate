import queue
import threading
import pyttsx3

# The queue shared by producers (UI) and the consumer thread
speech_queue: queue.Queue = queue.Queue()

def _audio_worker() -> None:
    """
    Background thread — pulls strings from speech_queue and speaks them.
    The TTS engine is created ONCE (singleton) and reused for every call,
    which avoids the lag from re-initializing it on every word.
    """
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except ImportError:
        pass

    # ── Singleton engine ────────────────────────────────
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 160)   # slightly faster than 80 — more natural
        engine.setProperty("volume", 1.0)
    except Exception as e:
        print(f"[Audio] TTS init failed: {e}")
        engine = None

    while True:
        text = speech_queue.get()

        if text is None:          # poison-pill → clean shutdown
            break

        if engine is None:
            speech_queue.task_done()
            continue

        try:
            # Drain stale entries so speech never falls behind typing
            while not speech_queue.empty():
                try:
                    stale = speech_queue.get_nowait()
                    if stale is None:   # preserve the shutdown signal
                        speech_queue.put(None)
                        break
                    speech_queue.task_done()
                except queue.Empty:
                    break

            engine.say(text)
            engine.runAndWait()
        except RuntimeError:
            # Engine was stopped externally — re-initialize
            try:
                engine = pyttsx3.init()
                engine.setProperty("rate", 160)
                engine.setProperty("volume", 1.0)
                engine.say(text)
                engine.runAndWait()
            except Exception as reinit_err:
                print(f"[Audio] Re-init failed: {reinit_err}")

        speech_queue.task_done()


# Start the singleton worker thread
_worker_thread = threading.Thread(target=_audio_worker, daemon=True)
_worker_thread.start()


def play_audio(text: str) -> None:
    """Enqueue text for speech synthesis (non-blocking)."""
    if text:
        speech_queue.put(text)


def stop_audio() -> None:
    """Gracefully stop the audio worker (send poison-pill)."""
    speech_queue.put(None)
