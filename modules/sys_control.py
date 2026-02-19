import os
import time
import threading


class SystemController:
    def __init__(self):
        self.time_remaining = self.load_time()
        self.is_running = True
    
    def load_time(self):
        try:
            with open("data/time_bank.txt", "r") as f:
                return int(f.read())  
        except:
            return 0

    def save_time(self):
        with open("data/time_bank.txt", "w") as f:
            f.write(str(self.time_remaining))

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