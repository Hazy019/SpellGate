import queue
import threading

# The queue shared by producers (UI) and the consumer thread
speech_queue: queue.Queue = queue.Queue()

def _audio_worker() -> None:
    """Background thread that pulls strings from speech_queue and speaks."""
    # 1. Keep the COM initialization at the very start of the thread
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except ImportError:
        pass

    import pyttsx3

    while True:
        text = speech_queue.get()
        if text is None:
            speech_queue.task_done()
            break
            
        # THE FIX: Initialize a fresh engine for EVERY SINGLE utterance
        engine = pyttsx3.init()
        engine.setProperty("rate", 150)
        
        engine.say(text)
        engine.runAndWait()
        
        # Destroy the engine so Windows SAPI5 completely releases the audio lock
        del engine
        
        speech_queue.task_done()

# Start the worker on import
threading.Thread(target=_audio_worker, daemon=True).start()

def play_audio(text: str) -> None:
    """Enqueue text for speech synthesis."""
    speech_queue.put(text)

def stop_audio() -> None:
    """Request the audio worker to exit."""
    speech_queue.put(None)