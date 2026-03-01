import queue
import threading
import pyttsx3

# The queue shared by producers (UI) and the consumer thread
speech_queue: queue.Queue = queue.Queue()

def _audio_worker() -> None:
    """Background thread that pulls strings from speech_queue and speaks."""
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except ImportError:
        pass

    while True:
        text = speech_queue.get()
        if text is None:
            break
            
        engine = pyttsx3.init()
        engine.setProperty("rate", 80)
        engine.say(text)
        engine.runAndWait()
        
        del engine
        
        speech_queue.task_done()

threading.Thread(target=_audio_worker, daemon=True).start()

def play_audio(text: str) -> None:
    """Enqueue text for speech synthesis."""
    speech_queue.put(text)
