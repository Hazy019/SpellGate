import threading
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QGraphicsDropShadowEffect, QLineEdit, QWidget, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

from modules.ui_scenes import BaseScene
from modules.firebase_sync import login_with_email, set_parent_pin

class LoginScene(BaseScene):
    login_successful = pyqtSignal()

    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        # Title
        title = QLabel("PARENT LOGIN")
        title.setObjectName("Header")
        title.setFont(QFont(self.arcade_family, 36))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #00e5ff; margin-bottom: 10px;")
        
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(20)
        glow.setColor(QColor("#00e5ff"))
        glow.setOffset(0, 0)
        title.setGraphicsEffect(glow)
        layout.addWidget(title)
        
        subtitle = QLabel("Please log in with your Parent Dashboard account.")
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setStyleSheet("color: #cccccc;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # Form container
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(15)
        
        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email Address")
        self.email_input.setFont(QFont("Arial", 14))
        self.email_input.setStyleSheet("padding: 12px; background: #111; color: #fff; border: 2px solid #333; border-radius: 5px;")
        form_layout.addWidget(self.email_input)
        
        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFont(QFont("Arial", 14))
        self.password_input.setStyleSheet("padding: 12px; background: #111; color: #fff; border: 2px solid #333; border-radius: 5px;")
        form_layout.addWidget(self.password_input)
        
        # PIN
        pin_label = QLabel("Set Emergency Unlock PIN (min 4 digits):")
        pin_label.setStyleSheet("color: #ffc857; margin-top: 10px;")
        pin_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        form_layout.addWidget(pin_label)
        
        self.pin_input = QLineEdit()
        self.pin_input.setPlaceholderText("e.g. 1234")
        self.pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_input.setMaxLength(8)
        self.pin_input.setFont(QFont("Arial", 14))
        self.pin_input.setStyleSheet("padding: 12px; background: #111; color: #ffc857; border: 2px solid #ffc857; border-radius: 5px;")
        form_layout.addWidget(self.pin_input)
        
        layout.addWidget(form_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # Submit
        self.submit_btn = QPushButton("CONNECT DEVICE")
        self.submit_btn.setFont(QFont(self.arcade_family, 14))
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #00e5ff;
                color: #000;
                padding: 15px 30px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3dffa0;
            }
        """)
        self.submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.submit_btn.clicked.connect(self.handle_login)
        layout.addWidget(self.submit_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #ff3864;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
    def handle_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()
        pin = self.pin_input.text().strip()
        
        if not email or not password:
            self.status_label.setText("Please enter email and password.")
            return
            
        if len(pin) < 4 or not pin.isdigit():
            self.status_label.setText("PIN must be at least 4 digits.")
            return
            
        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("CONNECTING...")
        self.status_label.setText("")
        
        # Run in thread so UI doesn't freeze
        threading.Thread(target=self._perform_login, args=(email, password, pin), daemon=True).start()
        
    def _perform_login(self, email, password, pin):
        success, err = login_with_email(email, password)
        
        # Use QTimer to safely update UI from background thread
        if success:
            QTimer.singleShot(0, lambda: self._on_login_success(pin))
        else:
            QTimer.singleShot(0, lambda: self._on_login_failure(err))
            
    def _on_login_success(self, pin):
        set_parent_pin(pin)
        self.login_successful.emit()
        
    def _on_login_failure(self, err):
        self.submit_btn.setEnabled(True)
        self.submit_btn.setText("CONNECT DEVICE")
        self.status_label.setText(f"Login Failed: {err}")
