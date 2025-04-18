import json
import os
import sys
import webbrowser
import re
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QLabel, QLineEdit,
    QHBoxLayout, QMessageBox, QHeaderView, QSizePolicy
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from cryptography.fernet import Fernet


class EncryptionHelper:
    """Handles encryption & decryption of passwords using Fernet."""

    KEY_FILE = "secret.key"  # File to store encryption key

    @staticmethod
    def generate_key():
        """Generates a new encryption key and saves it."""
        key = Fernet.generate_key()
        with open(EncryptionHelper.KEY_FILE, "wb") as key_file:
            key_file.write(key)

    @staticmethod
    def load_key():
        """Loads the encryption key, or generates a new one if missing."""
        if not os.path.exists(EncryptionHelper.KEY_FILE):
            EncryptionHelper.generate_key()
        with open(EncryptionHelper.KEY_FILE, "rb") as key_file:
            return key_file.read()

    @staticmethod
    def encrypt_password(password):
        """Encrypts the password using Fernet."""
        cipher = Fernet(EncryptionHelper.load_key())
        return cipher.encrypt(password.encode()).decode()

    @staticmethod
    def decrypt_password(encrypted_password):
        """Decrypts the password using Fernet."""
        cipher = Fernet(EncryptionHelper.load_key())
        return cipher.decrypt(encrypted_password.encode()).decode()




class AddAccountDialog(QDialog):
    """Dialog box for adding/editing LinkedIn credentials with validation."""

    def __init__(self, parent=None, account=None):
        super().__init__(parent)
        # self.setWindowTitle("Add LinkedIn Account")
        # self.setGeometry(300, 300, 400, 250)
        self.account = account

        layout = QVBoxLayout()

        # Email Input
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter LinkedIn Email")
        if account:
            self.email_input.setText(account["email"])
        layout.addWidget(QLabel("Email:"))
        layout.addWidget(self.email_input)

        # Password Input
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter LinkedIn Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        if account:
            self.password_input.setText(EncryptionHelper.decrypt_password(account["password"]))
        layout.addWidget(QLabel("Password:"))
        layout.addWidget(self.password_input)

        # Save Button
        self.save_button = QPushButton("Save")
        self.save_button.setStyleSheet("background-color: #2ecc71; color: white; padding: 10px;")
        self.save_button.clicked.connect(self.validate_and_accept)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def validate_and_accept(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()

        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            QMessageBox.warning(self, "Invalid Email", "Please enter a valid email address.")
            return
        if len(password) < 6:
            QMessageBox.warning(self, "Weak Password", "Password must be at least 6 characters long.")
            return

        self.accept()

    def get_data(self):
        return {
            "email": self.email_input.text(),
            "password": EncryptionHelper.encrypt_password(self.password_input.text()),
            "status": "Inactive"  # Always save with default status
        }


class ProfilePage(QWidget):
    """Main Profile Page for managing LinkedIn accounts."""
    JSON_FILE = "accounts.json"  # JSON file to store account data

    def __init__(self):
        super().__init__()
        self.setWindowTitle("LinkedIn Account Manager")
        self.accounts = []
        self.filtered_accounts = []

        layout = QVBoxLayout()

        # Search Bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search by Email...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #3498DB;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 14px;
                color: #333;
                height: 30px;  /* Reduced height */
            }
        """)
        self.search_input.textChanged.connect(self.filter_accounts)
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Table for accounts
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Email", "Status", "Start", "Pause", "Stop", "Actions"])

        # ✅ Fix: Use QSizePolicy for Expanding Table
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # 🌟 Make columns stretch to fit window size
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # ✅ **Increased Row Height**
        self.table.verticalHeader().setDefaultSectionSize(60)  # Increase row height

        # Table Styling
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #f8f9fa;
                border: 1px solid #d1d1d1;
                border-radius: 5px;
                gridline-color: #dee2e6;
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: #3498DB;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 6px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #AED6F1;
                color: black;
            }
        """)

        # Enable alternating row colors
        self.table.setAlternatingRowColors(True)

        layout.addWidget(self.table)

        # Add Button
        self.add_button = QPushButton("➕ Add Account")
        self.add_button.setStyleSheet("background-color: #3498DB; color: white; padding: 10px;")
        self.add_button.clicked.connect(self.add_record)
        layout.addWidget(self.add_button)

        self.setLayout(layout)

        # Load accounts from JSON
        self.load_accounts()

    def load_accounts(self):
        """Loads account data from JSON file."""
        if os.path.exists(self.JSON_FILE):
            with open(self.JSON_FILE, "r") as file:
                self.accounts = json.load(file)
        else:
            self.accounts = []

        self.filtered_accounts = self.accounts  # Initially, show all accounts

        self.refresh_table()

    def save_accounts(self):
        """Saves account data to JSON file."""
        with open(self.JSON_FILE, "w") as file:
            json.dump(self.accounts, file, indent=4)

    def add_record(self):
        """Opens dialog to add a new LinkedIn account."""
        dialog = AddAccountDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            data["status"] = "Inactive"  # Set default status

            self.accounts.append(data)
            self.save_accounts()
            #self.refresh_table()
            self.filter_accounts()  # Update filtered list & refresh table

    def filter_accounts(self):
        """Filters accounts based on search input."""
        search_text = self.search_input.text().strip().lower()
        if search_text:
            self.filtered_accounts = [acc for acc in self.accounts if search_text in acc["email"].lower()]
        else:
            self.filtered_accounts = self.accounts  # Show all if search is empty

        self.refresh_table()

    def refresh_table(self):
        """Refreshes table with updated account data."""
        self.table.setRowCount(len(self.filtered_accounts))
        for row, account in enumerate(self.filtered_accounts):
            self.table.setItem(row, 0, QTableWidgetItem(account["email"]))
            self.table.setItem(row, 1, QTableWidgetItem(account["status"]))

            # Start Button
            start_btn = QPushButton("▶ Start")
            start_btn.clicked.connect(lambda _, r=row: self.start_linkedin(r))
            self.table.setCellWidget(row, 2, start_btn)

            # Pause Button
            pause_btn = QPushButton("⏸ Pause")
            pause_btn.clicked.connect(lambda _, r=row: self.pause_account(r))
            self.table.setCellWidget(row, 3, pause_btn)

            # Stop Button
            stop_btn = QPushButton("⏹ Stop")
            stop_btn.clicked.connect(lambda _, r=row: self.stop_account(r))
            self.table.setCellWidget(row, 4, stop_btn)

            # ✅ **Updated Edit Button with Icon**
            actions_layout = QHBoxLayout()
            edit_btn = QPushButton("✏️ Edit")  # Pencil Icon for Edit
            edit_btn.clicked.connect(lambda _, r=row: self.edit_record(r))
            delete_btn = QPushButton("🗑 Delete")  # Trash Icon for Delete
            delete_btn.clicked.connect(lambda _, r=row: self.delete_record(r))
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            action_widget = QWidget()
            action_widget.setLayout(actions_layout)
            self.table.setCellWidget(row, 5, action_widget)

    def start_linkedin(self, row):
        """Opens LinkedIn in project browser."""
        email = self.filtered_accounts[row]["email"]

        # Update status in the main accounts list
        for account in self.accounts:
            if account["email"] == email:
                account["status"] = "Active"
                break

        self.save_accounts()
        self.refresh_table()
        QMessageBox.information(self, "Starting", f"Opening LinkedIn inside project browser for {email}")

    def pause_account(self, row):
        """Pauses account session."""
        self.table.item(row, 1).setText("Paused")
        email = self.filtered_accounts[row]["email"]

        for account in self.accounts:
            if account["email"] == email:
                account["status"] = "Paused"
                break

        self.save_accounts()
        self.refresh_table()
        QMessageBox.information(self, "Paused", f"Paused account: {email}")

    def stop_account(self, row):
        """Stops account session."""
        self.table.item(row, 1).setText("Inactive")
        email = self.filtered_accounts[row]["email"]

        for account in self.accounts:
            if account["email"] == email:
                account["status"] = "Inactive"
                break
        self.save_accounts()
        self.refresh_table()
        QMessageBox.information(self, "Stopped", f"Stopped account: {email}")

    def edit_record(self, row):
        """Edits an existing account."""
        dialog = AddAccountDialog(self, self.accounts[row])
        if dialog.exec():
            self.accounts[row] = dialog.get_data()
            self.save_accounts()
           # self.refresh_table()
            self.filter_accounts()  # Update filtered list & refresh table


    def delete_record(self, row):
        """Deletes an account."""
        confirm = QMessageBox.question(self, "Delete", "Are you sure you want to delete this account?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            del self.accounts[row]
            self.save_accounts()
            self.refresh_table()
            self.filter_accounts()  # Update filtered list & refresh table


class MainWindow(QMainWindow):
    """Main Application Window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("LinkedIn Account Manager")
        self.setGeometry(100, 100, 700, 400)
        self.profile_page = ProfilePage()
        self.setCentralWidget(self.profile_page)


# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = MainWindow()
#     window.show()
#     sys.exit(app.exec())