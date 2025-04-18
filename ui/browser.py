import sys
import json
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QProgressBar, QFrame, QMessageBox, QLineEdit)
from PyQt6.QtCore import QUrl, Qt, QTimer
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from cryptography.fernet import Fernet

class LinkedInBrowser(QMainWindow):
    JSON_FILE = "accounts.json"
    SECRET_KEY_FILE = "secret.key"

    ACTION_DELAY = 15000  # Global delay in milliseconds (5 seconds for each step)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("LinkedIn Professional Scraper")
        self.secret_key = None
        self.email = None
        self.password = None

        # Initialize UI first, so if errors occur after UI loads, user can still see something
        self.init_ui()

        try:
            self.secret_key = self.load_secret_key()
            self.email, self.password = self.get_active_account()
        except Exception as e:
            self.show_critical_error(f"Initialization failed: {e}")
            sys.exit(1)

        self.current_page = 1
        self.total_pages = 1
        self.all_profiles = []
        self.is_scraping = False

        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QLabel, QLineEdit, QPushButton {
                font-size: 14px;
            }
            QLineEdit {
                padding: 6px;
                border: 1px solid #d1d1d1;
                border-radius: 4px;
            }
            QPushButton {
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
        """)

        # Main Vertical Layout (Header + Webview)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # -- Header Section (30% Height) --
        header_frame = QWidget()
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 10, 10, 10)
        header_layout.setSpacing(6)

        # Search Bar Row
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search Query (e.g., MERN Stack Developer)")
        self.search_input.returnPressed.connect(self.perform_search)
        search_layout.addWidget(self.search_input)

        self.start_button = QPushButton("▶ Start")
        self.start_button.setStyleSheet("background-color: #0077B5; color: white;")
        self.start_button.clicked.connect(self.start_scraping)
        search_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("⛔ Stop")
        self.stop_button.setStyleSheet("background-color: #e74c3c; color: white;")
        self.stop_button.clicked.connect(self.stop_scraping)
        self.stop_button.setEnabled(False)
        search_layout.addWidget(self.stop_button)

        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.setStyleSheet("background-color: #f39c12; color: white;")
        self.refresh_button.clicked.connect(self.refresh_page)
        search_layout.addWidget(self.refresh_button)

        header_layout.addLayout(search_layout)

        # Status Row (Status Label + Progress Bar)
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("color: #2c3e50; font-weight: bold;")
        status_layout.addWidget(self.status_label, 1)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                height: 14px;
                border: 1px solid #d1d1d1;
                background-color: #f5f5f5;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #0077B5;
            }
        """)
        status_layout.addWidget(self.progress_bar, 2)

        header_layout.addLayout(status_layout)


        header_frame.setFixedHeight(int(self.height() * 0.15))  # 15% height
        main_layout.addWidget(header_frame)

        # Separator Line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #e1e1e1;")
        main_layout.addWidget(separator)

        # -- Webview Section (70% Height) --
        self.webview = QWebEngineView()
        self.webview.setUrl(QUrl("https://www.linkedin.com/login"))
        self.webview.setStyleSheet("""
            border: 1px solid #d1d1d1;
            border-radius: 4px;
        """)
        main_layout.addWidget(self.webview, 1)

        # WebChannel Setup
        self.channel = QWebChannel()
        self.channel.registerObject("backend", self)
        self.webview.page().setWebChannel(self.channel)
        self.webview.loadFinished.connect(self.auto_login)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def load_secret_key(self):
        if not os.path.exists(self.SECRET_KEY_FILE):
            QMessageBox.critical(self, "Error", f"Missing '{self.SECRET_KEY_FILE}'")
            sys.exit(1)

        with open(self.SECRET_KEY_FILE, "rb") as key_file:
            return key_file.read()

    def get_active_account(self):
        if not os.path.exists(self.JSON_FILE):
            QMessageBox.critical(self, "Error", "Missing 'accounts.json'")
            sys.exit(1)

        with open(self.JSON_FILE, "r") as file:
            accounts = json.load(file)

        for account in accounts:
            if account.get("status") == "Active":
                return account["email"], self.decrypt_password(account["password"])
        QMessageBox.critical(self, "Error", "No active account found in 'accounts.json'")
        sys.exit(1)

    def decrypt_password(self, encrypted_password):
        cipher = Fernet(self.secret_key)
        return cipher.decrypt(encrypted_password.encode()).decode()

    def auto_login(self):
        self.log_status("Attempting auto login...")

        script = f"""
            async function slowType(selector, value) {{
                const input = document.querySelector(selector);
                input.focus();
                for (let char of value) {{
                    input.value += char;
                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    await new Promise(r => setTimeout(r, 150));
                }}
            }}

            (async () => {{
                await slowType("#username", "{self.email}");
                await slowType("#password", "{self.password}");
                document.querySelector("button[type='submit']").click();

                setTimeout(() => {{
                    let errorBox = document.querySelector('.alert-content');
                    if (errorBox && errorBox.innerText.includes('unexpected error')) {{
                        qtBackend.log_status("Login failed: Unexpected error detected on LinkedIn.");
                    }}
                }}, 5000);
            }})();
        """

        self.webview.page().runJavaScript(script)

    def refresh_page(self):
        self.webview.reload()
        QMessageBox.information(self, "Page Refreshed", "The page has been refreshed.")

    def perform_search(self):
        search_query = self.search_input.text().strip()
        if not search_query:
            QMessageBox.warning(self, "Input Error", "Please enter a search query!")
            return

        script = f"""
            setTimeout(() => {{
                let searchBox = document.querySelector('input[placeholder="Search"]');
                searchBox.value = "{search_query}";
                searchBox.dispatchEvent(new Event('input', {{ bubbles: true }}));
                setTimeout(() => {{
                    searchBox.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', bubbles: true }}));
                }}, 1000);
            }}, 1000);
        """
        self.webview.page().runJavaScript(script)

    def start_scraping(self):
        self.current_page = 1
        self.all_profiles = []
        self.is_scraping = True

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        self.log_status("Performing search and waiting for results...")
        QTimer.singleShot(self.ACTION_DELAY, self.scroll_and_detect_pages)

    def scroll_and_detect_pages(self):
        self.log_status("Scrolling to trigger pagination...")
        script = "window.scrollTo(0, document.body.scrollHeight);"
        self.webview.page().runJavaScript(script)

        QTimer.singleShot(self.ACTION_DELAY, self.detect_total_pages)

    def detect_total_pages(self):
        self.log_status("Detecting total pages...")
        script = """
            (() => {
                let pages = document.querySelectorAll('.artdeco-pagination__indicator[data-test-pagination-page-btn]');
                if (pages.length === 0) {
                    console.log("❌ Pagination not found after scroll. Assuming 1 page.");
                    return 1;
                }
                let lastPage = pages[pages.length - 1].getAttribute('data-test-pagination-page-btn');
                return parseInt(lastPage, 10) || 1;
            })();
        """
        self.webview.page().runJavaScript(script, self.on_page_count_detected)

    def on_page_count_detected(self, total_pages):
        try:
            self.total_pages = int(total_pages)
            self.log_status(f"✅ Detected {self.total_pages} pages.")
        except (ValueError, TypeError):
            self.total_pages = 1
            self.log_status("⚠️ Failed to detect pages reliably. Assuming 1 page.")

        if self.total_pages == 1:
            QMessageBox.warning(self, "Warning", "Only 1 page detected. This may indicate a loading issue.")

        QTimer.singleShot(5000, self.scrape_current_page)  # Proceed after 5 seconds

    def scrape_current_page(self):
        if not self.is_scraping:
            return

        self.progress_bar.setValue(int((self.current_page / self.total_pages) * 100))
        self.log_status(f"Scraping page {self.current_page}/{self.total_pages}...")

        script = """
                        (() => {
                const profiles = [];

                document.querySelectorAll('li').forEach(profileItem => {
                    // Get name
                    const name = profileItem.querySelector('span[aria-hidden="true"]')?.innerText?.trim();

                    // Get profile link
                    let link = profileItem.querySelector('a[aria-hidden="false"]')?.href;

                    // Get title (e.g., HR Manager)
                    const title = profileItem.querySelector('div.t-14.t-black.t-normal')?.innerText?.trim() || 'N/A';

                    // Get location (e.g., Chandigarh)
                    const location = profileItem.querySelectorAll('div.t-14.t-normal')?.[1]?.innerText?.trim() || 'N/A';
                    // Get image URL
                    const imageUrl = profileItem.querySelector('img')?.src || 'No image available';

                    if (name && link) {
                        profiles.push({ name, link, title, location,imageUrl });
                    }
                });

                
                return profiles;
            })();
        """
        self.webview.page().runJavaScript(script, self.on_profiles_scraped)

    def on_profiles_scraped(self, profiles):
        self.all_profiles.extend(profiles)
        self.log_status(f"Scraped {len(profiles)} profiles from Page {self.current_page}")

        # ✅ Load existing data (if file exists)
        if os.path.exists("Queue.json"):
            with open("Queue.json", "r", encoding="utf-8") as file:
                try:
                    existing_profiles = json.load(file)
                except json.JSONDecodeError:
                    existing_profiles = []
        else:
            existing_profiles = []

        # ✅ Convert existing profile links to a set for fast lookup
        existing_links = {profile.get("link") for profile in existing_profiles}

        # ✅ Filter out duplicates from new profiles
        new_unique_profiles = [p for p in profiles if p.get("link") not in existing_links]

        # ✅ Combine existing + unique new profiles
        all_profiles = existing_profiles + new_unique_profiles

        # ✅ Save back to Queue.json
        with open("Queue.json", "w", encoding="utf-8") as file:
            json.dump(all_profiles, file, indent=4, ensure_ascii=False)

        self.log_status(f"Added {len(new_unique_profiles)} new profiles, total now: {len(all_profiles)}")

        # ✅ Move to next page or finish
        if self.current_page < self.total_pages and self.is_scraping:
            QTimer.singleShot(self.ACTION_DELAY, self.goto_next_page)
        else:
            self.finish_scraping()


    def goto_next_page(self):
        self.current_page += 1
        self.log_status(f"Scrolling down before loading page {self.current_page}...")

        # Scroll to bottom to force LinkedIn to load the next button (if needed)
        scroll_script = "window.scrollTo(0, document.body.scrollHeight);"
        self.webview.page().runJavaScript(scroll_script)

        # After scroll, wait and then click next page button
        QTimer.singleShot(self.ACTION_DELAY, self.click_next_page_button)

    def click_next_page_button(self):
        self.log_status(f"Clicking 'Next' button to load page {self.current_page}...")

        next_page_script = """
            (() => {
                let nextButton = document.querySelector('button.artdeco-pagination__button--next');
                if (nextButton && !nextButton.disabled) {
                    nextButton.scrollIntoView({behavior: 'smooth'});
                    nextButton.click();
                    return true;
                }
                return false;
            })();
        """
        self.webview.page().runJavaScript(next_page_script, self.on_next_page_clicked)

    def on_next_page_clicked(self, success):
        if success:
            self.log_status(f"✅ Successfully clicked 'Next'. Waiting for page {self.current_page} to load...")
            QTimer.singleShot(self.ACTION_DELAY, self.scrape_current_page)
        else:
            self.log_status("⚠️ Next button not found or disabled. Ending scraping.")
            self.finish_scraping()

    def finish_scraping(self):
        # json.dump(self.all_profiles, open("Queue.json", "w"), indent=4, ensure_ascii=False)
        self.log_status(f"Scraping complete - {len(self.all_profiles)} profiles saved")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def stop_scraping(self):
        self.is_scraping = False
        self.log_status("⚠️ Scraping Stop.")

    def log_status(self, message):
        self.status_label.setText(f"Status: {message}")
        print(f"[LOG] {message}")
