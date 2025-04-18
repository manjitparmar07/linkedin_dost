import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QHBoxLayout, QMessageBox
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import MainWindow


class LoginScreen(QWidget):
    def __init__(self, login_success_callback):
        super().__init__()
        self.login_success_callback = login_success_callback
        self.setWindowTitle("Login - LBM Solutions")
        self.setFixedSize(500, 400)
        self.setStyleSheet("background-color: #f0f2f5;")
        self.setup_ui()


    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Title
        title = QLabel("Welcome Back 👋")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Login to continue to your account")
        subtitle.setFont(QFont("Arial", 10))
        subtitle.setStyleSheet("color: #555;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Email field
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.email_input.setStyleSheet(self.input_style())

        # Password field
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(self.input_style())

        login_button = QPushButton("Login")
        login_button.setStyleSheet(self.button_style())
        login_button.clicked.connect(self.handle_login)
        login_button.setDefault(True)  # 👈 This makes it respond to Enter key

        # Contact Us label
        contact_label = QLabel('<a href="https://lbmsolution.com">Contact Us</a>')
        contact_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        contact_label.setStyleSheet("color: #4a90e2; font-size: 12px;")
        contact_label.setOpenExternalLinks(True)

        # Add widgets to layout
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch()
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_input)
        layout.addWidget(login_button)
        layout.addWidget(contact_label)
        layout.addStretch()

        self.setLayout(layout)

    def input_style(self):
        return """
            QLineEdit {
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
            }
        """

    def button_style(self):
        return """
            QPushButton {
                background-color: #4a90e2;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3d7ecb;
            }
        """

    def handle_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()

        if not email or not password:
            QMessageBox.warning(self, "Validation Error", "Please enter both email and password.")
            return

        # TODO: Replace with real authentication
        if email == "admin@lbm.com" and password == "password123":
            QMessageBox.information(self, "Login Successful", "Welcome to the system!")
            self.open_main_window()

        else:
            QMessageBox.critical(self, "Login Failed", "Invalid email or password.")

    def open_main_window(self):
        from main import MainWindow  # Import here to avoid circular import issues
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginScreen()
    window.show()
    sys.exit(app.exec())
