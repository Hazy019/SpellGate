import threading
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QGraphicsDropShadowEffect, QLineEdit, QWidget, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

from modules.ui_scenes import BaseScene
from modules.firebase_sync import pair_device

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
        title = QLabel("PAIR DEVICE")
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
        
        subtitle = QLabel("Enter the 6-digit code shown in your Parent Dashboard to link this PC.\n"
                                "Single PC? Open your web browser to spellgate.web.app to get your code.")
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setStyleSheet("color: #cccccc; line-height: 1.4;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # Form container
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(15)
        
        # Pairing Code Input
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("000000")
        self.code_input.setMaxLength(6)
        self.code_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.code_input.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.code_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                background: #111;
                color: #00e5ff;
                border: 2px solid #00e5ff;
                border-radius: 8px;
                letter-spacing: 6px;
            }
        """)
        form_layout.addWidget(self.code_input)
        
        layout.addWidget(form_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # Buttons container
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        # Submit
        self.submit_btn = QPushButton("PAIR DEVICE")
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
        self.submit_btn.clicked.connect(self.handle_pairing)
        btn_layout.addWidget(self.submit_btn)

        # Minimize / Get Code Button (for single PC setup)
        self.minimize_btn = QPushButton("MINIMIZE (ESC)")
        self.minimize_btn.setFont(QFont(self.arcade_family, 14))
        self.minimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #8b5cf6;
                color: #ffffff;
                padding: 15px 30px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #a78bfa;
            }
        """)
        self.minimize_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.minimize_btn.clicked.connect(self.handle_minimize)
        btn_layout.addWidget(self.minimize_btn)

        layout.addLayout(btn_layout)
        
        # Status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #ff3864;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

    def handle_minimize(self):
        """Minimizes the game window to taskbar so single PC users can open browser."""
        if hasattr(self.parent_window, "handle_esc_pressed"):
            self.parent_window.handle_esc_pressed()
        else:
            self.parent_window.showMinimized()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.handle_minimize()
            event.accept()
        else:
            super().keyPressEvent(event)
        
    def handle_pairing(self):
        code = self.code_input.text().strip()
        
        if len(code) != 6 or not code.isdigit():
            self.status_label.setText("Please enter a valid 6-digit number.")
            return
            
        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("PAIRING...")
        self.status_label.setText("Waiting for Parent Dashboard to confirm...")
        self.status_label.setStyleSheet("color: #facc15;")
        
        # Run pairing in thread so UI doesn't freeze during polling
        threading.Thread(target=self._perform_pairing, args=(code,), daemon=True).start()
        
    def _perform_pairing(self, code):
        try:
            print(f"[LoginScene] Initiating device pairing for code: {code}...")
            success, err = pair_device(code)
            print(f"[LoginScene] Pairing result -> success={success}, error={err}")
            
            if success:
                QTimer.singleShot(0, self._on_pairing_success)
            else:
                QTimer.singleShot(0, lambda: self._on_pairing_failure(err))
        except Exception as e:
            print(f"[LoginScene] Unhandled exception during pairing: {e}")
            import traceback
            traceback.print_exc()
            QTimer.singleShot(0, lambda: self._on_pairing_failure(str(e)))
            
    def _on_pairing_success(self):
        self.login_successful.emit()
        
    def _on_pairing_failure(self, err):
        self.submit_btn.setEnabled(True)
        self.submit_btn.setText("PAIR DEVICE")
        self.status_label.setText(f"Pairing Failed: {err}")
        self.status_label.setStyleSheet("color: #ff3864;")

