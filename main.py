import customtkinter as ctk
from tkinter import messagebox
import os

PARENT_PASSWORD = "15302531"
APP_TITLE = "SpellGate: Student Portal"

class SpellGateApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(APP_TITLE)
        self.geometry("800x600")

        self.attributes("-fullscreen", True)
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        self.bind("<Control-Alt-p>", self.admin_unlock)

        self.container =ctk.CTkFrame(self)
        self.container.pack(fill = "both", expand = True)

        self.frames = {}

        for F in (StudyFrame, TestFrame, TimerFrame):
            page_name = F.__name__
            frame = F(parent = self.container, controller = self)
            self.frames[page_name] = frame

            frame.grid(row = 0, column = 0, sticky = "nsew")

        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.show_frame("StudyFrame")

        def show_frame(self, page_name):
            '''Show a frame for the given page name'''
            frame = self.frames[page_name]
            frame.tkraise()

        def admin_unlock(self, event=None):
            dialog = ctk.CTkInputDialog(
                text="Enter Parent Password:",
                title="Admin Unlock"
            )
            if dialog.get_input() == PARENT_PASSWORD:
                self.destroy()
            else:
                messagebox.showerror("Error", "Wrong Password!")

class StudyFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.remaining_time = 100

        label = ctk.CTkLabel(
            self,
            text = "Phase 1: Study Mode",
            font = ("Arial", 30)
        )
        label.pack(pady=20)

        self.timer_label = ctk.CTkLabel(
            self,
            text = f"Time Remaining: {self.remaining_time} seconds",
            font = ("Arial", 20),
            text_color = "red"
        )
        self.timer_label.pack(pady = 20)

        self.word_display = ctk.CTkLabel(
            self,
            width = 400,
            height = 200,
            font = ("Arial", 20)
        )
        self.word_display.insert("0.0", "1. CAT\n2. DOG\n3. SUN\n(Words will go here...)")
        self.word_display.configure(state = "disabled")
        self.word_display.pack(pady = 20)

        btn = ctk.CTkButton(
            self,
            text = "Start Test",
            command = lambda: controller.show_frame("TestFrame")
        )
        btn.pack(pady = 20)
    
if __name__ == "__main__":
    app = SpellGateApp()
    app.mainloop()