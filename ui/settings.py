from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QLabel,
    QLineEdit, QTextEdit, QFrame, QSizePolicy, QApplication, QMainWindow
)
from PyQt6.QtCore import Qt
import sys


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f2f5;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QPushButton {
                background-color: #0077B5;
                color: white;
                padding: 8px 14px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #005c8a;
            }
            QLabel {
                font-weight: bold;
                margin-bottom: 6px;
            }
            QLineEdit, QTextEdit {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QFrame#Card {
                background-color: white;
                border-radius: 8px;
                padding: 16px;
            }
        """)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar Navigation
        nav_layout = QVBoxLayout()
        nav_layout.setContentsMargins(16, 16, 8, 16)
        nav_layout.setSpacing(6)

        self.buttons = {
            "Change Password": QPushButton("🔒  Change Password"),
            "Manage Subscription": QPushButton("📦  Manage Subscription"),
            "Invoice": QPushButton("📄  Invoice"),
            "Payment Method": QPushButton("💳  Payment Method"),
            "About Us": QPushButton("ℹ️  About Us")
        }

        for name, btn in self.buttons.items():
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #2c3e50;
                    text-align: left;
                    padding: 8px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #e6f0f8;
                }
            """)
            btn.clicked.connect(lambda checked, n=name: self.switch_page(n))
            nav_layout.addWidget(btn)

        nav_container = QWidget()
        nav_container.setFixedWidth(200)
        nav_container.setLayout(nav_layout)
        nav_container.setStyleSheet("background-color: #ffffff; border-right: 1px solid #dcdcdc;")

        # Pages Stack
        self.pages = QStackedWidget()
        self.page_widgets = {
            "Change Password": self.create_change_password_page(),
            "Manage Subscription": self.create_subscription_page(),
            "Invoice": self.create_invoice_page(),
            "Payment Method": self.create_payment_method_page(),
            "About Us": self.create_about_us_page()
        }

        for page in self.page_widgets.values():
            self.pages.addWidget(page)

        main_layout.addWidget(nav_container)
        main_layout.addWidget(self.pages)

    def switch_page(self, name):
        page = self.page_widgets.get(name)
        if page:
            self.pages.setCurrentWidget(page)

    def create_change_password_page(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.addWidget(QLabel("Change Your Password"))
        layout.addWidget(QLabel("Current Password"))
        layout.addWidget(QLineEdit())
        layout.addWidget(QLabel("New Password"))
        layout.addWidget(QLineEdit())
        layout.addWidget(QLabel("Confirm New Password"))
        layout.addWidget(QLineEdit())
        layout.addWidget(QPushButton("Update Password"))
        return self._wrap_card(layout)

    def create_subscription_page(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.addWidget(QLabel("Manage Your Subscription"))
        layout.addWidget(QLabel("Current Plan: Pro"))
        layout.addWidget(QPushButton("Upgrade to Premium"))
        layout.addWidget(QPushButton("Cancel Subscription"))
        return self._wrap_card(layout)

    def create_invoice_page(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.addWidget(QLabel("Recent Invoices"))
        layout.addWidget(QLabel("Invoice #12345 - $99"))
        layout.addWidget(QPushButton("Download PDF"))
        return self._wrap_card(layout)

    def create_payment_method_page(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.addWidget(QLabel("Your Current Payment Method"))
        layout.addWidget(QLabel("💳 Visa ending in 4242"))
        layout.addWidget(QPushButton("Update Card"))
        layout.addWidget(QPushButton("Remove Card"))
        return self._wrap_card(layout)

    def create_about_us_page(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.addWidget(QLabel("About LBM Solutions"))
        about_text = QTextEdit("LBM Solutions is a leading tech company specializing in AI, blockchain, and full-stack development training.")
        about_text.setReadOnly(True)
        layout.addWidget(about_text)
        return self._wrap_card(layout)

    def _wrap_card(self, inner_layout):
        frame = QFrame()
        frame.setObjectName("Card")
        frame.setLayout(inner_layout)
        outer = QVBoxLayout()
        outer.setContentsMargins(20, 20, 20, 20)
        outer.addWidget(frame)
        container = QWidget()
        container.setLayout(outer)
        return container


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QMainWindow()
    settings_page = SettingsPage()
    window.setCentralWidget(settings_page)
    window.setWindowTitle("Settings")
    window.resize(820, 520)
    window.show()
    sys.exit(app.exec())
