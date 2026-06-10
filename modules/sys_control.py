import os
import time
import threading


from modules.security import secure_load_time, secure_save_time

class SystemController:
    def __init__(self):
        self.time_remaining = self.load_time()
        self.is_running = True
    
    def load_time(self):
        return secure_load_time()

    def save_time(self):
        secure_save_time(self.time_remaining)

    def start_countdown(self):
        while self.is_running:
            if self.time_remaining > 0:
                self.time_remaining -= 1
                time.sleep(1)
                if self.time_remaining % 60 == 0:
                    self.save_time()

    def trigger_shutdown(self):
        os.system("shutdown /s /t 60")
        print("Shutdown Initiated")