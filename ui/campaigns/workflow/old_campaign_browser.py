import inspect
import sys
import json
import pickle

import os
import random
import openai
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QProgressBar, QFrame, QMessageBox)
from PyQt6.QtCore import QUrl, QTimer
from PyQt6.QtCore import QEventLoop  # ✅ QEventLoop is in QtCore
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtCore import QUrl
from PyQt6.QtWebChannel import QWebChannel
from cryptography.fernet import Fernet
from fontTools.unicodedata import script
from datetime import datetime


class CampaignBrowser(QMainWindow):
    JSON_FILE = "accounts.json"
    SECRET_KEY_FILE = "secret.key"
    QUEUE_FILE = "queue.json"
    COMPLETED_QUEUE_FILE = "completed_queue.json"
    old_profile=""
    client = openai.OpenAI(api_key="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")  # Replace with your actual API key

    def __init__(self):
        super().__init__()
        self.setWindowTitle("LinkedIn Professional Scraper")
        self.is_logged_in = False  # Track login state
        
        self.secret_key = None
        self.email = None
        self.password = None

        self.queue = []
        self.processed = []
        self.status = "inactive"
        self.active_workflow = None
        self.current_step = 0


        # Initialize UI first, so if errors occur after UI loads, user can still see something
        self.init_ui()

        try:
            self.secret_key = self.load_secret_key()
            self.email, self.password = self.get_active_account()
        except Exception as e:
            self.show_critical_error(f"Initialization failed: {e}")
            sys.exit(1)

        self.update_queue_status()


        self.workflow_dir = "workflows"
        self.active_workflows = {}

    def load_active_workflows(self):
        """Scans the workflows directory and loads active workflows into a dictionary."""
        if not os.path.exists(self.workflow_dir):
            print("[ERROR] Workflow folder not found!")
            return {}

        for filename in os.listdir(self.workflow_dir):
            if filename.endswith(".json"):
                path = os.path.join(self.workflow_dir, filename)
                try:
                    with open(path, "r", encoding="utf-8") as file:
                        data = json.load(file)
                        
                        # Check if workflow is active
                        if data.get("status") == "active":
                            self.active_workflows[filename] = data.get("steps", [])
                except json.JSONDecodeError:
                    print(f"[ERROR] Invalid JSON format in {filename}")
                except Exception as e:
                    print(f"[ERROR] Unexpected error while processing {filename}: {e}")
        return self.active_workflows

    def display_workflows(self):
        """Displays active workflows and their steps."""
        if not self.active_workflows:
            print("[INFO] No active workflows found.")
            return

        print("\n[INFO] Active Workflows:")
        for workflow, steps in self.active_workflows.items():
            print(f"  - {workflow}: {steps}")

    def init_ui(self):
        self.setStyleSheet("""
            QLabel, QPushButton {
                font-size: 14px;
            }
            QPushButton {
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
        """)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(8)

        self.header_frame = QWidget()
        self.header_layout = QHBoxLayout(self.header_frame)
        self.header_layout.setContentsMargins(10, 10, 10, 10)
        self.header_layout.setSpacing(10)

        self.start_button = QPushButton("▶ Start")
        self.start_button.setStyleSheet("background-color: #0077B5; color: white;")
        self.start_button.clicked.connect(self.start_scraping)

        self.stop_button = QPushButton("⛔ Stop")
        self.stop_button.setStyleSheet("background-color: #e74c3c; color: white;")
        self.stop_button.clicked.connect(self.stop_scraping)
        self.stop_button.setEnabled(False)

        self.header_layout.addWidget(self.start_button)
        self.header_layout.addWidget(self.stop_button)

        self.queue_count_label = QLabel("Queue: 0 Profiles Ready")
        self.queue_count_label.setStyleSheet("font-weight: bold; color: #0077B5;")
        self.header_layout.addWidget(self.queue_count_label)

        self.completed_queue_label = QLabel("Completed: 0 Profiles")
        self.completed_queue_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        self.header_layout.addWidget(self.completed_queue_label)

        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("color: #2c3e50; font-weight: bold;")
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.status_label)

        self.main_layout.addWidget(self.header_frame)

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
        self.main_layout.addWidget(self.progress_bar)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #e1e1e1;")
        self.main_layout.addWidget(separator)

        # Create persistent profile
        self.profile = QWebEngineProfile("linkedin_profile", self)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)

        # Create webview and assign custom profile via page
        self.webview = QWebEngineView()
        page = QWebEnginePage(self.profile, self.webview)
        self.webview.setPage(page)

        # Load LinkedIn
        self.webview.setUrl(QUrl("https://www.linkedin.com/login"))
        self.main_layout.addWidget(self.webview, 1)

        self.channel = QWebChannel()
        self.channel.registerObject("backend", self)
        self.webview.page().setWebChannel(self.channel)
        self.webview.loadFinished.connect(self.auto_login)

        container = QWidget()
        container.setLayout(self.main_layout)
        self.setCentralWidget(container)

    def resizeEvent(self, event):
        self.header_frame.setFixedHeight(int(self.height() * 0.05))
        super().resizeEvent(event)

    def load_secret_key(self):
        if not os.path.exists(self.SECRET_KEY_FILE):
            raise FileNotFoundError(f"Missing '{self.SECRET_KEY_FILE}'")

        with open(self.SECRET_KEY_FILE, "rb") as key_file:
            return key_file.read()

    def get_active_account(self):
        if not os.path.exists(self.JSON_FILE):
            raise FileNotFoundError(f"Missing '{self.JSON_FILE}'")

        with open(self.JSON_FILE, "r") as file:
            try:
                accounts = json.load(file)
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse '{self.JSON_FILE}': {e}")

        for account in accounts:
            if account.get("status") == "Active":
                return account["email"], self.decrypt_password(account["password"])

        raise Exception("No active account found in 'accounts.json'")

    def decrypt_password(self, encrypted_password):
        cipher = Fernet(self.secret_key)
        return cipher.decrypt(encrypted_password.encode()).decode()

    def auto_login(self):
        self.log_status("Attempting auto login...")

        script = f"""
            function waitForElement(selector, callback) {{
                const interval = setInterval(() => {{
                    const el = document.querySelector(selector);
                    if (el) {{
                        clearInterval(interval);
                        callback(el);
                    }}
                }}, 500);
            }}

            function slowType(selector, value, done) {{
                const input = document.querySelector(selector);
                if (!input) return;
                input.focus();
                let i = 0;
                const interval = setInterval(() => {{
                    input.value += value[i];
                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    i++;
                    if (i >= value.length) {{
                        clearInterval(interval);
                        if (done) done();
                    }}
                }}, 150);
            }}

            waitForElement("#username", () => {{
                slowType("#username", "{self.email}", () => {{
                    slowType("#password", "{self.password}", () => {{
                        document.querySelector("button[type='submit']").click();
                    }});
                }});
            }});
        """

        self.webview.page().runJavaScript(script)

    


#check the permission ------ start


    def load_settings(self):
            with open("settingdata.json", "r", encoding="utf-8") as f:
                return json.load(f)

    def load_daily_usage(self):
            today = datetime.now().strftime("%Y-%m-%d")
            if not os.path.exists("daily_usage.json"):
                return {}, today

            with open("daily_usage.json", "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
            return data, today

    def save_daily_usage(self, data):
            with open("daily_usage.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

    def can_perform(self, action_type):
            settings = self.load_settings()
            data, today = self.load_daily_usage()

            limits = next((s for s in settings if s["type"].lower() == action_type.lower()), None)
            if not limits:
                return False

            today_usage = data.get(today, {}).get(action_type, 0)
            return today_usage < limits.get("per_day_select", 0)

    def update_usage(self, action_type):
            data, today = self.load_daily_usage()
            if today not in data:
                data[today] = {}
            data[today][action_type] = data[today].get(action_type, 0) + 1
            self.save_daily_usage(data)

    

#check permission ------ end




    def mark_login_complete(self, result=None):  # Accepts an optional argument
        self.is_logged_in = True

    def show_critical_error(self, message):
        QMessageBox.critical(self, "Critical Error", message)

    def log_status(self, message):
        self.status_label.setText(f"Status: {message}")
        print(f"[LOG] {message}")

    def update_queue_status(self):
        queue_count = self.get_json_count(self.QUEUE_FILE)
        completed_count = self.get_json_count(self.COMPLETED_QUEUE_FILE)

        self.queue_count_label.setText(f"Queue: {queue_count} Profiles Ready")
        self.completed_queue_label.setText(f"Completed: {completed_count} Profiles")

        total = queue_count + completed_count
        self.progress_bar.setValue(int((completed_count / total) * 100) if total > 0 else 0)

    def get_json_count(self, file_path):
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump([], file)

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                if not isinstance(data, list):
                    raise ValueError(f"Invalid format in {file_path} (expected list)")
                return len(data)
        except (json.JSONDecodeError, ValueError) as e:
            self.log_status(f"Queue Load Error: {e}")
            # Auto-repair if the file is corrupt
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump([], file)
            return 0

    def check_daily_limits(self):
        self.log_status("📊 Checking daily usage limits...")

        settings = self.load_settings()
        usage, today = self.load_daily_usage()

        all_exceeded = True
        exceeded_report = []

        for setting in settings:
            action_type = setting.get("type")
            limit = setting.get("per_day_select", 0)
            done = usage.get(today, {}).get(action_type, 0)

            if done < limit:
                all_exceeded = False
            else:
                exceeded_report.append(f"{action_type}: {done}/{limit}")

        if all_exceeded:
            msg = "🚫 All daily limits are reached:\n\n" + "\n".join(exceeded_report)
            QMessageBox.warning(self, "Daily Limit Reached", msg)
            self.log_status("⚠️ Start canceled — All limits reached.")
            return False

        return True


    # def start_scraping(self):
    #     self.log_status("🟢 Scraping started...")

    #     settings = self.load_settings()
    #     print(settings)
    #     usage, today = self.load_daily_usage()
    #     print(usage)
    #     print(today)
    #     # Check if all actions are exhausted
    #     all_exceeded = True
    #     exceeded_report = []

    #     for setting in settings:
    #         action_type = setting.get("type")
    #         print(action_type)
    #         limit = setting.get("per_day_select", 0)
    #         print("daily limit",limit)
    #         done = usage.get(today, {}).get(action_type, 0)
    #         print("done check",done)
    #         if done < limit:
    #             all_exceeded = False
    #         else:
    #             exceeded_report.append(f"{action_type}: {done}/{limit}")
    #             print(exceeded_report)

    #     if all_exceeded:
    #         msg = "🚫 All daily limits are reached:\n\n" + "\n".join(exceeded_report)
    #         QMessageBox.warning(self, "Daily Limit Reached", msg)
    #         self.log_status("⚠️ Start canceled — All limits reached.")
    #         return

    #     # ✅ At least one task allowed, proceed
    #     self.start_button.setEnabled(False)
    #     self.stop_button.setEnabled(True)
    #     self.is_scraping = True

    #     QTimer.singleShot(7000, lambda: self.process_next_profile())

    def start_scraping(self):
        self.log_status("🟢 Scraping started...")

        if not self.check_daily_limits():
            return


        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.is_scraping = True

        if self.check_phase1_limits():
            self.log_status("✅ Phase 1 limits available — proceeding to next profile.")
            QTimer.singleShot(1000, lambda: self.process_next_profile("LikeCommentConnection"))
        elif self.check_followup_limit():
            self.log_status("✅ Phase 1 limits exhausted. Phase 2 (FollowUp) still available — going to FollowUp.")
            # self.queue = self.load_workflow_queue()
            # self.current_step = 0
            QTimer.singleShot(1000, lambda: self.process_next_profile("FollowUp"))
        else:
            self.log_status("🚫 All daily limits reached (Phase 1 & Phase 2).")
            QMessageBox.warning(self, "Daily Limit Reached", "Phase 1 and FollowUp limits are exhausted.")
            self.stop_scraping()

        #QTimer.singleShot(7000, lambda: self.process_next_profile("All"))

    def check_phase1_limits(self):
        settings = self.load_settings()
        usage, today = self.load_daily_usage()
        phase1_types = ["Like", "Comment", "Connection"]

        for setting in settings:
            if setting.get("type") in phase1_types:
                limit = setting.get("per_day_select", 0)
                done = usage.get(today, {}).get(setting.get("type"), 0)
                if done < limit:
                    return True  # At least one action can be done
        return False  # All exhausted

    def check_followup_limit(self):
        settings = self.load_settings()
        usage, today = self.load_daily_usage()

        for setting in settings:
            if setting.get("type") == "FollowUp":
                limit = setting.get("per_day_select", 0)
                done = usage.get(today, {}).get("FollowUp", 0)
                return done < limit
        return False

    def stop_scraping(self):
        self.log_status("Scraping stopped.")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.is_scraping = False

    # process_next_profile will go here — no changes needed for now

    def process_next_profile(self,action_text):
        if not self.is_scraping:
            return

        if not self.check_daily_limits():  # 🔥 <- ADD THIS
            self.log_status("⛔ Daily limit exhausted. Stopping scraping.")
            self.stop_scraping()
            return
        if action_text=="All" or action_text=="LikeCommentConnection":

            with open(self.QUEUE_FILE, "r", encoding="utf-8") as file:
                queue = json.load(file)

            completed_links = set()
            completed_profiles = []
            if os.path.exists(self.COMPLETED_QUEUE_FILE):
                with open(self.COMPLETED_QUEUE_FILE, "r", encoding="utf-8") as file:
                    try:
                        completed_profiles = json.load(file)
                        completed_links = {profile['link'] for profile in completed_profiles}
                    except json.JSONDecodeError:
                        completed_profiles = []
                        completed_links = set()

            self.current_profile = None
            for profile in queue:
                if 'link' in profile and profile['link'] not in completed_links:
                    self.current_profile = profile
                    break

            if not self.current_profile:
                self.log_status("Queue is empty or all profiles completed.")
                self.stop_scraping()
                return

            self.log_status(f"🚀 Processing profile: {self.current_profile['name']}")
            # ✅ Safe disconnect + reconnect
            self.safe_disconnect_signal(self.webview.loadFinished, self.step1_profile_load)
            self.webview.loadFinished.connect(self.step1_profile_load)
            QTimer.singleShot(3000, lambda: self.webview.setUrl(QUrl(self.current_profile['link'])))

        else:
            index = self.get_followup_message_index()
            print("check the index------",index)
            step = self.queue[index]
            QTimer.singleShot(10000, lambda: self._delayed_followup_execution(step))  # ✅ Fixed

    def get_followup_message_index(self):
        active = self.find_active_workflow()
        if not active:
            QMessageBox.warning(self, "No Active Workflow", "No active workflow found.")
            return
        if isinstance(active, list) and len(active) > 1:
            QMessageBox.critical(self, "Multiple Actives", "More than one active workflow found!")
            return

        filename = active if isinstance(active, str) else active[0]
        self.load_workflow(filename)
        if self.queue:
            self.log_status(f"▶️ Starting workflow: {filename}")
       

        try:
            workflow_path = os.path.join("workflows", self.active_workflow)
            with open(workflow_path, "r", encoding="utf-8") as f:
                workflow_data = json.load(f)
            actions = workflow_data.get("actions", [])
            for index, action in enumerate(actions):
                if action.get("name") == "Send_Follow_up_Message":
                    return index

            return -1  # Not found
        except Exception as e:
            print(f"[ERROR] Failed to read or parse the workflow file: {e}")
            return -1

    def step1_profile_load(self):
        self.log_status("Loading profile...")

        QTimer.singleShot(7000, self.start_workflow)
        

#-------------------------------------------     WORK START     --------------------------

    def start_workflow(self):
        active = self.find_active_workflow()

        if not active:
            QMessageBox.warning(self, "No Active Workflow", "No active workflow found.")
            return
        if isinstance(active, list) and len(active) > 1:
            QMessageBox.critical(self, "Multiple Actives", "More than one active workflow found!")
            return

        filename = active if isinstance(active, str) else active[0]
        self.load_workflow(filename)
        if self.queue:
            self.log_status(f"▶️ Starting workflow: {filename}")
            self.execute_next_step()

    def find_active_workflow(self):
        folder = "workflows"
        if not os.path.exists(folder):
            return None

        active_files = []
        for filename in os.listdir(folder):
            if filename.endswith(".json"):
                path = os.path.join(folder, filename)
                try:
                    with open(path, "r") as file:
                        data = json.load(file)
                        if data.get("status", "").lower() == "active":
                            active_files.append(filename)
                except (json.JSONDecodeError, ValueError):
                    continue

        if len(active_files) == 1:
            return active_files[0]
        elif len(active_files) > 1:
            return active_files  # return list to trigger error
        return None

    def load_workflow(self, filename):
        folder = "workflows"
        path = os.path.join(folder, filename)
        if os.path.exists(path):
            try:
                with open(path, "r") as file:
                    content = file.read().strip()
                    if not content:
                        raise ValueError("Workflow file is empty.")
                    data = json.loads(content)
                    self.queue = data.get("actions", [])
                    self.status = data.get("status", "inactive")
                    self.active_workflow = filename
            except (json.JSONDecodeError, ValueError) as e:
                QMessageBox.critical(None, "Load Error", f"Failed to load workflow: {e}")
                self.queue = []
                self.status = "inactive"
                self.active_workflow = None
        else:
            QMessageBox.warning(None, "File Not Found", "Selected workflow file does not exist.")

        self.processed = []

    def check_if_all_main_actions_done(self):
        if self.current_profile is None:
            return

        workflow_path = os.path.join("workflows", self.active_workflow)
        if not os.path.exists(workflow_path):
            print(f"[ERROR] Workflow file not found: {workflow_path}")
            return

        with open(workflow_path, "r", encoding="utf-8") as f:
            try:
                workflow_data = json.load(f)
            except json.JSONDecodeError:
                print("[ERROR] Failed to load workflow JSON")
                return

        all_actions = workflow_data.get("actions", [])
        remaining_actions = self.queue[self.current_step:]

        # These are the 3 main tracked types
        action_flags = {
            "Like_Post": "like_done",
            "Comment_Post": "comment_done",
            "Send_Connection_Request": "connection_sent"
        }


        # Step 1: Which of these actions are in the workflow?
        required_action_keys = [action_flags[a["name"]] for a in all_actions if a["name"] in action_flags]

        # Step 2: Are they all done in current_profile?
        all_done = all(self.current_profile.get(flag) for flag in required_action_keys)

        # Step 3: Are any of those actions still left in remaining queue?
        still_pending = [
            step.get("name") for step in remaining_actions
            if step.get("name") in action_flags
        ]

        if all_done and not still_pending:
            self.log_status("✅ All Like/Comment/Connection actions completed from workflow. Marking final status as pending.")
            if self.current_profile['welcome_sent']=="Premium":
                self.current_profile['welcome_sent'] = "Premium"
            else:
                self.current_profile['welcome_sent'] = "Pending"
            
            self.current_profile['final_status'] = "Pending"
            self.move_to_completed("Pending")

    

    def execute_next_step(self):
        if self.current_step >= len(self.queue):
            self.log_status("✅ Workflow completed.")
            self.current_profile['final_status'] = 'done'
            self.move_to_completed("done")
            return

        # Call our universal action check
        self.check_if_all_main_actions_done()

        # Get the current step to execute
        step = self.queue[self.current_step]
        self.current_step += 1
        action_type = step.get("name")  # Assuming each step has a 'type' field like 'Like', 'Comment', etc.
        if not self.check_action_limit(action_type):
            # Skip this step if the limit is exceeded
            self.log_status(f"🚫 {action_type} limit exceeded, skipping.")
            QTimer.singleShot(1000, self.execute_next_step)
            return

        name = step.get("name", "unknown")
        self.log_status(f"⚙️ Executing step: {name}")

        method = getattr(self, f"Step_{name}", None)
        if method:
            print("Execution steps:", step)
            method(step)
        else:
            self.log_status(f"❌ No method found for: {name}")
            QTimer.singleShot(1000, self.execute_next_step)

    def check_action_limit(self, action_type):
        if action_type=="Like_Post":
            action_type="Like"
        elif action_type=="Comment_Post":
            action_type="Comment"
        elif action_type=="Send_Connection_Request":
            action_type="Connection"
        else:
            action_type="FollowUp"

        """ Check if the action type's limit is exceeded for the day. """
        settings = self.load_settings()  # Load settings to get daily limits
        usage, today = self.load_daily_usage()  # Get today's usage data

        for setting in settings:
            if setting.get("type") == action_type:
                limit = setting.get("per_day_select", 0)
                done = usage.get(today, {}).get(action_type, 0)

                if done < limit:
                    return True  # Action can be performed
                else:
                    return False  # Action limit exceeded

        return False 
   

#like the post ------- start
   
    def Step_Like_Post(self, step):
        self.log_status("👍 Liking posts dynamically based on workflow JSON...")
        num_likes = step.get("count", 1)
        print("Total like posts:", num_likes)

        # Step 1: Click "Show all posts"
        show_posts_script = """
            (function() {
                const button = [...document.querySelectorAll('a.artdeco-button')].find(el =>
                    el.innerText.trim().toLowerCase().includes('show all posts') ||
                    el.innerText.trim().toLowerCase().includes('show all activity')
                );
                if (button) {
                    button.click();
                    return "Clicked show all posts";
                } else {
                    return "❌ Show all posts button not found.";
                }
            })();
        """
        self.webview.page().runJavaScript(show_posts_script)

        # Step 2: Like posts with tracking
        def like_posts():
            like_script = f"""
                window.likeCompleted = false;

                (function() {{
                    let likeButtons = [...document.querySelectorAll('button')].filter(
                        btn => btn.innerText.trim().toLowerCase().includes('like')
                    );

                    if (likeButtons.length < {num_likes}) {{
                        window.likeCompleted = "❌ Not enough posts to like.";
                        return;
                    }}

                    async function likeSequentially() {{
                        for (let i = 0; i < {num_likes}; i++) {{
                            try {{
                                likeButtons[i].scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                                await new Promise(r => setTimeout(r, 1000));
                                //likeButtons[i].click();
                                console.log("✅ Liked post", i + 1);
                                await new Promise(r => setTimeout(r, 2000));
                            }} catch (err) {{
                                console.error("⚠️ Like error on post", i + 1, err);
                            }}
                        }}
                        window.likeCompleted = "done";
                    }}

                    likeSequentially();
                }})();
            """
            self.webview.page().runJavaScript(like_script)

            # Step 3: Poll for completion
            def poll_like_complete():
                check_script = "window.likeCompleted;"
                self.webview.page().runJavaScript(check_script, lambda result: handle_like_result(result))

            def handle_like_result(result):
                if result == "done":
                    self.log_status("✅ Liking posts completed!")
                    self.current_profile['like_done'] = f"{num_likes} Done"
                    self.update_usage("Like")
                    # Go back and proceed to next step
                    self.webview.page().runJavaScript("window.history.back();")
                    QTimer.singleShot(3000, self.execute_next_step)
                elif isinstance(result, str) and result.startswith("❌"):
                    self.log_status(f"❌ Error: {result}")
                    
                    self.current_profile['like_done'] = f"{num_likes} Done"
                    self.update_usage("Like")
                    QTimer.singleShot(3000, self.execute_next_step)
                else:
                    QTimer.singleShot(1000, poll_like_complete)

            QTimer.singleShot(5000, poll_like_complete)  # start polling after a short delay

        QTimer.singleShot(3000, like_posts)  # wait for activity page to load

   
#like the post -------- end

#comment the post ------- start
    
    def Step_Comment_Post(self, step):
        num_posts = step.get("count", 1)

        # Step 1: Click "Show all posts"
        show_posts_script = """
            (function() {
                const button = [...document.querySelectorAll('a.artdeco-button')].find(el =>
                    el.innerText.trim().toLowerCase().includes('show all posts') ||
                    el.innerText.trim().toLowerCase().includes('show all activity')
                );
                if (button) {
                    button.click();
                    return "Clicked show all posts";
                } else {
                    return "❌ Show all posts button not found.";
                }
            })();
        """
        # Run the first script to click the button
        self.webview.page().runJavaScript(show_posts_script)

        # Add delay before executing next script (simulate human wait)
        QTimer.singleShot(4000, lambda: self.start_scroll_and_wait(step, num_posts))
    
    def start_scroll_and_wait(self, step, num_posts):
        js_scroll_wait = """
            (async function () {
                async function autoScroll(scrollCount = 6, delay = 1000) {
                    for (let i = 0; i < scrollCount; i++) {
                        window.scrollBy(0, window.innerHeight / 2);
                        await new Promise(resolve => setTimeout(resolve, delay + Math.random() * 1000));
                    }
                }

                function waitForElements(selector, timeout = 10000) {
                    return new Promise((resolve, reject) => {
                        const interval = 500;
                        let timeElapsed = 0;
                        const checker = setInterval(() => {
                            const elements = document.querySelectorAll(selector);
                            if (elements.length > 0) {
                                clearInterval(checker);
                                resolve(elements);
                            }
                            timeElapsed += interval;
                            if (timeElapsed >= timeout) {
                                clearInterval(checker);
                                reject("Timeout: Elements not found");
                            }
                        }, interval);
                    });
                }

                await autoScroll();
                await waitForElements('.feed-shared-update-v2, .update-components-text');
                return true;
            })();
        """

        self.webview.page().runJavaScript(js_scroll_wait, lambda _: self.fetch_raw_posts(step, num_posts))
    def fetch_raw_posts(self, step, num_posts):
        js_fetch = f"""
            (function () {{
                const posts = document.querySelectorAll('.feed-shared-update-v2, .update-components-text');
                const rawPosts = [];

                posts.forEach((post, index) => {{
                    const textEl = post.querySelector('.feed-shared-update-v2__description-wrapper, .update-components-text');
                    const text = textEl ? textEl.innerText.trim() : "";
                    if (text) {{
                        rawPosts.push(text);
                    }}
                }});

                return rawPosts.slice(0, {num_posts});
            }})();
        """

        self.webview.page().runJavaScript(js_fetch, lambda result: self.process_raw_posts(step, result))

    def process_raw_posts(self, step, result):
        print("check the result data :")
        print(result)
        
        # raw_texts = json.loads(result)
        raw_texts = result
        postData = []

        for i, text in enumerate(raw_texts):
            if text and len(text.strip()) > 0:
                postData.append({
                    "postNumber": i + 1,
                    "postType": "text",
                    "content": text[:2000]
                })

        self.log_status(f"✅ Found {len(postData)} valid text posts.")
        self.process_text_posts(step, postData)

        
    def process_text_posts(self, step, result):
        print("📥 JS result received in Python:")
        print(result)

        # Optional: parse and work with the data
        import json
        try:
            posts = result
            print(f"✅ Total posts received: {len(posts)}")
            for post in posts:
                print(f"📝 Post {post['postNumber']}: {post['content'][:100]}...")
        except Exception as e:
            print("❌ Error parsing JS result:", e)

        comments = []
        for post in posts:
            print(f"Processing Text Post {post['postNumber']}")
            if(step.get("comment_type","AI")=="AI"):
                post_content=post["content"]
                ai_comment = self.generate_ai_comment(f"Write a short, professional, and thoughtful LinkedIn comment in response to this post: '{post_content}'. The tone should be supportive and engaging. Keep it under 60 words.")
                print(f"AI Comment for Post {post['postNumber']}: {ai_comment}")
            else:
                ai_comment = step.get("Message","")
                print(f"Manual Comment for Post {post['postNumber']}: {ai_comment}")

            comments.append(ai_comment)

        self.comment_on_posts(step, comments)


    def comment_on_posts(self, step, comments):
        comments_json = json.dumps(comments)

        script = f"""
            window.commentingDone = false;
            window.commentResult = "";

            async function handleCommentsSequentially() {{
                try {{
                    let commentButtons = [...document.querySelectorAll('button[aria-label="Comment"]')];
                    let comments = {comments_json};

                    for (let i = 0; i < Math.min(commentButtons.length, comments.length); i++) {{
                        try {{
                            commentButtons[i].scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                            commentButtons[i].click();
                            await new Promise(r => setTimeout(r, 3000));

                            let commentBoxList = document.querySelectorAll('.ql-editor[contenteditable="true"]');
                            if (commentBoxList.length === 0) continue;

                            let commentBox = commentBoxList[commentBoxList.length - 1];
                            commentBox.closest('[class*=comments-comment-box]').scrollIntoView({{
                                behavior: 'smooth',
                                block: 'center'
                            }});
                            commentBox.focus();
                            await new Promise(innerResolve => {{
                                let text = comments[i];
                                let index = 0;

                                function typeChar() {{
                                    if (index < text.length) {{
                                        commentBox.focus();
                                        commentBox.textContent += text[index];
                                        commentBox.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                        index++;
                                        setTimeout(typeChar, 100 + Math.random() * 100);
                                    }} else {{
                                        setTimeout(() => {{
                                            const submitButtons = document.querySelectorAll('.comments-comment-box__submit-button--cr');
                                            const submitButton = submitButtons[submitButtons.length - 1];
                                            if (submitButton) {{
                                                // submitButton.click();
                                            }}
                                            innerResolve();
                                        }}, 3000);
                                    }}
                                }}
                                setTimeout(typeChar, 100);
                            }});
                        }} catch (err) {{
                            console.error("Error during one comment", err);
                        }}
                    }}

                    window.commentResult = "All comments done";
                    window.commentingDone = true;
                }} catch (error) {{
                    window.commentResult = "Commenting failed: " + error;
                    window.commentingDone = true;
                }}
            }}

            handleCommentsSequentially();
        """
        self.webview.page().runJavaScript(script)
        self.check_if_commenting_done(step)


    def check_if_commenting_done(self, step):
        self.webview.page().runJavaScript("window.commentingDone", lambda done: self.handle_comment_done_check(done, step))

    def handle_comment_done_check(self, done, step):
        if done:
            self.webview.page().runJavaScript("window.commentResult", lambda result: self.step_after_comment_posts(step, {"status": result}))
        else:
            QTimer.singleShot(1000, lambda: self.check_if_commenting_done(step))  # Retry after 1 second


    def step_after_comment_posts(self,step, result):
        self.log_status(f"Comment post result: {result}")
         # Ensure result is not None or empty
        if not result:
            self.log_status("⚠️ Warning: Received empty result from JavaScript!")
            return

            # Try parsing the JSON result
        try:
            # If result is already a dictionary, use it directly
            if isinstance(result, dict):
                status = result.get("status", "Unknown status")
                self.log_status(f"✅ Status received: {status}")

                if status == "All comments done":
                    num_posts= step.get("count", 1)
                    self.current_profile['comment_done'] = f' {num_posts}  Done'  # Replace with actual count you used
                    self.update_usage("Comment")

                    QTimer.singleShot(10000, self.execute_next_step)
                    return

                    
            else:
                self.log_status(f"❌ Unexpected result format: {result}, type: {type(result)}")

        except json.JSONDecodeError as e:
            self.log_status(f"❌ Error decoding JSON result: {e}")
            return
        
        

#comment the post ------- end


# send connection request ----- start
   
    def Step_Send_Connection_Request(self, step):
        self.connection_done = False
        self.log_status("🔍 Step 1: Checking pending connection button...")
        self.webview.page().runJavaScript("""
            ( function() {
                window.scrollBy(0, Math.random() * 3000);
                let targetContainer = document.querySelector('[class*="entry-point"], [class*="connect"], [class*="actions"]');
                if (!targetContainer) return { status: "target_container_not_found" };

                let pendingBtn = [...targetContainer.querySelectorAll('button')]
                    .find(btn => btn.innerText.trim().toLowerCase().includes('pending'));

                return { status: pendingBtn ? "Connection already pending." : "No Pending Button" };
            })();
        """, lambda result: self.step3_wait_afterpending_button(step, result, "connect"))


    def step3_wait_afterpending_button(self, step, result,action_type):
        self.log_status(f"📥 Step 2: Result from pending button check: {result} ----- {action_type}")
        if not result:
            self.log_status("⚠️ Warning: Received empty result from JavaScript!")
            return

        if isinstance(result, dict):
            status = result.get("status", "Unknown status")
            self.log_status(f"✅ Status received: {status}")
            if status == "Connection already pending.":
                self.connection_done = True
                QTimer.singleShot(3000, self.wait_until_connection_done)
            elif status == "No Pending Button":
                self.log_status("🔍 Step 3: Searching for Connect button...")
                QTimer.singleShot(3000, lambda: self.step4_search_connectbutton(step,action_type))



    def step4_search_connectbutton(self, step, action_type):
        self.log_status(f"🔍 Step 4: Looking for {action_type.capitalize()} button in the page...")
        
        button_text = "connect" if action_type == "connect" else "message"
        self.webview.page().runJavaScript(f"""
            (function() {{
                let targetContainer = document.querySelector('[class*="entry-point"], [class*="connect"], [class*="actions"]');
                if (!targetContainer) return {{ status: "target_container_not_found" }};
                let button = [...targetContainer.querySelectorAll('button')]
                    .find(btn => btn.innerText.trim().toLowerCase().includes('{button_text}'));
                
                if (button) {{
                    button.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    button.click();
                    return {{ status: "{button_text}_button_found" }};
                }} else {{
                    return {{ status: "{button_text}_button_not_found" }};
                }}
            }})();
        """, lambda result: self.step5_wait_after_button_click(step, result, action_type))

    def step5_wait_after_button_click(self, step, result, action_type):
        self.log_status(f"📥 Step 5: Result after {action_type} button click: {result}")
        
        if result.get("status") == f"{action_type}_button_found":
            QTimer.singleShot(3000, lambda: self.step6_add_note_or_send(result,step, action_type))
        else:
            self.mark_connection_done_and_continue(result,action_type)


    def step6_add_note_or_send(self,result,step, action_type):
        
        
        if action_type == "connect":
            self.log_status(f"📝 Step 6: {action_type.capitalize()} - Click 'Add a note' or 'Send without a note'...")
        
            # Check if we need to add a note or send without one
            with_note = step.get("send_type", "withnote") == "withnote"
            script = """
                (function() {
                    let addNoteBtn = [...document.querySelectorAll('button')]
                        .find(btn => btn.innerText.includes('Add a note'));
                    if (addNoteBtn) {
                        addNoteBtn.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        addNoteBtn.click();
                        return { status: "add_note_button_clicked" };
                    } else {
                        return { status: "add_note_button_not_found" };
                    }
                })();
            """ if with_note else """
                (function() {
                    let addNoteBtn = [...document.querySelectorAll('button')]
                        .find(btn => btn.innerText.includes('Send without a note'));
                    if (addNoteBtn) {
                        addNoteBtn.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        addNoteBtn.click();
                        return { status: "without_add_note_button_clicked" };
                    } else {
                        return { status: "without_add_note_button_not_found" };
                    }
                })();
            """
            self.webview.page().runJavaScript(script, lambda result: self.step7_wait_after_add_note_or_send_button(step, result, action_type))

        elif action_type == "message":
            self.log_status(f"📝 Step 6: {action_type.capitalize()} - Click 'welcome Message'...")
            QTimer.singleShot(5000, lambda: self.step7_wait_after_add_note_or_send_button(step,result,action_type))

    def step7_wait_after_add_note_or_send_button(self, step, result, action_type):
        self.log_status(f"📥 Step 7: Result after {action_type} action: {result}")
        
        if action_type == "connect":
            if result.get("status") == "add_note_button_clicked":
                QTimer.singleShot(5000, lambda: self.step_typemessage(step,action_type))
            else:
                self.mark_connection_done_and_continue(result,action_type)
        elif action_type == "message":
            if result.get("status") == "message_button_found":
               
                self.check_premium_dialog(lambda is_premium: self.handle_step7_premium_check(is_premium, step, result, action_type))
            else:
                self.mark_connection_done_and_continue(result,action_type)

#premium dialog box check  --- start
    def check_premium_dialog(self, callback):
        check_premium_modal_js = """!!document.querySelector('div.artdeco-modal.modal-upsell.perks-insights__perks-in-upsell-wrapper')"""
        self.webview.page().runJavaScript(check_premium_modal_js, callback)


    def handle_step7_premium_check(self, is_premium, step, result, action_type):
        print("💬 Premium dialog status:", is_premium)

        if is_premium:
            self.dismiss_premium_modal()
        else:
            QTimer.singleShot(5000, lambda: self.step_typemessage(step, action_type))


    def dismiss_premium_modal(self):
        print("🧹 Attempting to close the Premium dialog...")
        dismiss_modal_js = """
        let btn = document.querySelector('button.artdeco-modal__dismiss');
        if (btn) { btn.click(); }
        """
        self.webview.page().runJavaScript(dismiss_modal_js)
        self.mark_connection_done_and_continue({ "status": "Premium" }, "message")

#premium dialog box check  --- end 

    def step_typemessage(self, step,action_type):
        self.connection_done = False
        self.log_status("⌨️ Step 8: Typing message in the note box...")
        if action_type=="connect":
            if step.get("note_type", "AI") == "AI":
                ai_comment = self.generate_ai_comment("Craft a concise, polite LinkedIn connection request message under 30 words. The message should convey professional respect, show genuine interest in the person’s background or expertise, and express a desire for mutual growth or knowledge-sharing. Avoid being overly enthusiastic or formal, and do not include greetings or sign-offs like 'Hi [Name]' or 'Best regards'.")

            else:
                ai_comment = step.get("Message", "")
            
            print("connect message : ",ai_comment)
            import json
            script = f"""
                    window.messageTypingDone = false;

                    (function() {{
                        let textarea = document.querySelector('textarea[name="message"]');
                        if (!textarea) {{
                            window.messageTypingDone = true;
                            return {{ status: "No Message Box Found." }};
                        }}

                        textarea.focus();
                        let index = 0;
                        let message = {json.dumps(ai_comment)};

                        function typeNextCharacter() {{
                            if (index < message.length) {{
                                textarea.value += message[index];
                                textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                index++;
                                setTimeout(typeNextCharacter, 100);
                            }} else {{
                                window.messageTypingDone = true;
                            }}
                        }}

                        setTimeout(typeNextCharacter, 100);
                    }})();
                """
        else:
            if step.get("message_type", "AI") == "AI":
                message = self.generate_ai_comment("this person accepted my connection request on LinkedIn, so send a positive welcome")
            else:
                message = step.get("Message", "Hi, thank you for connecting!")
            
            print("follow message : ",message)
            import json
            try:
                script = f"""
                    (function() {{
                        let editor = document.querySelector('div[contenteditable="true"][aria-label="Write a message…"]');
                        if (editor) {{
                            editor.click();
                            let index = 0;
                            let message = {json.dumps(message)};
                            
                            function typeNextCharacter() {{
                                if (index < message.length) {{
                                    editor.textContent += message[index];
                                    editor.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    index++;
                                    setTimeout(typeNextCharacter, 100);  // delay simulates human typing
                                }} else {{
                                    // Click Send button after typing the message
                                    let sendButton = document.querySelector('button.msg-form__send-button');
                                    if (sendButton && !sendButton.disabled) {{
                                        //sendButton.click();
                                        setTimeout(function() {{
                                            // Close the message box
                                            let closeButton = document.querySelector('header.msg-overlay-conversation-bubble-header button[aria-label*="Close"]');
                                            if (closeButton) {{
                                                closeButton.click();
                                            }}
                                        }}, 1500);  // wait for the send action to complete
                                    }} else {{
                                        console.log("⚠️ Send button not found or disabled.");
                                    }}
                                }}
                            }}
                            setTimeout(typeNextCharacter, 100);
                        }} else {{
                            console.log("❌ Message box not found.");
                        }}
                    }})();
                    """
                # Execute the script in the page
                self.page().runJavaScript(script)
            except:
                self.mark_connection_done_and_continue({ "status": "Pending" }, action_type)

        self.webview.page().runJavaScript(script)
        QTimer.singleShot(1000, lambda: self.wait_until_typing_done(step,action_type))



    def wait_until_typing_done(self, step, action_type):
        if action_type=="connect":
            self.webview.page().runJavaScript("window.messageTypingDone", lambda done: self.handle_typing_done_check(done, step,action_type))
        else:
            self.mark_connection_done_and_continue({ "status": "Pending" }, action_type)


    def handle_typing_done_check(self, done, step,action_type):
        if done:
            self.step_aftertype_sendbutton({})
        else:
            QTimer.singleShot(1000, lambda: self.wait_until_typing_done(step, action_type))


    def step_aftertype_sendbutton(self, result):
        self.log_status("🚀 Step 9: Looking for Send button to finalize connection...")
        script = """
            (function() {
                let sendBtn = [...document.querySelectorAll('button')]
                    .find(btn => btn.innerText.includes('Send'));
                if (sendBtn && !sendBtn.disabled) {
                    sendBtn.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    //sendBtn.click();
                    return { status: "invitation_send" };
                } else {
                    return { status: "send_button_not_found" };
                }
            })();
        """
        self.webview.page().runJavaScript(script, lambda result: self.mark_connection_done_and_continue(result,"connect"))

    def mark_connection_done_and_continue(self, result,action_type):
        if self.current_profile is None:
            self.log_status("⚠️ current_profile is None. Cannot update status.")
            return
        if action_type=="connect":
            self.log_status(f"Connection result: {result}")
            self.current_profile['connection_sent'] = "Done"
            self.update_usage("Connection")

            self.connection_done = True
        else:
            self.log_status(f"Message result: {result.get("status")}")
            self.current_profile['welcome_sent'] = result.get("status")
            if result.get("status")=="Done":
                self.update_usage("FollowUp")
                self.connection_done = True
            
            elif result.get("status")=="Premium":
                self.current_profile['welcome_sent'] = "Premium"
                self.update_usage("FollowUp")

                self.connection_done = True
            
        
            else:
                self.current_profile['welcome_sent'] = "Pending"
                self.connection_done = True
            
        self.wait_until_connection_done()


    def wait_until_connection_done(self):
        if getattr(self, 'connection_done', False):
            QTimer.singleShot(500, self.execute_next_step)
        else:
            QTimer.singleShot(500, self.wait_until_connection_done)

# send connection request ------ end

# check connection request accept ---- start

    def fetch_pending_welcome_messages(self):
        print("check fetch:")
        # Load completed profiles from completed_queue.json
        completed_profiles = []
        if os.path.exists(self.COMPLETED_QUEUE_FILE):
            with open(self.COMPLETED_QUEUE_FILE, "r", encoding="utf-8") as file:
                try:
                    completed_profiles = json.load(file)
                    print(completed_profiles)
                except json.JSONDecodeError:
                    completed_profiles = []

        # Filter profiles where "Send_welcome_message" is "pending"
        pending_profiles = [profile for profile in completed_profiles if profile.get("welcome_sent") == "Pending"]
        return pending_profiles

    def Step_Send_Follow_up_Message(self, step):
        self.log_status("⏳ Waiting 5 seconds before fetching pending messages...")
        QTimer.singleShot(10000, lambda: self._delayed_followup_execution(step))  # ✅ Fixed


    def _delayed_followup_execution(self, step):
        if self.load_next_followup_profile():
            # Add delay before proceeding to check pending connection
            QTimer.singleShot(10000, lambda: self.check_followup_connection_pending(step))

    def load_next_followup_profile(self):
        print("⏳ 5 sec delay start")

        pending_profiles = self.fetch_pending_welcome_messages()
        print("check pending")
        if not pending_profiles:
            self.log_status("No pending welcome messages.")
            QTimer.singleShot(1000, self.execute_next_step)
            return False  # ⛔ Stop further steps if no profile found

        self.current_profile = pending_profiles[0]

        if self.current_profile and 'link' in self.current_profile:
            self.log_status(f"🚀 Processing profile from completed queue: {self.current_profile['name']}")
        # ✅ Disconnect existing signals to avoid multiple triggers
            try:
                self.webview.loadFinished.disconnect()
            except:
                pass

            # ✅ Connect the page load signal to your next step
            self.webview.loadFinished.connect(self.step_after_profile_loaded)

            # 🌐 Load profile
            QTimer.singleShot(3000, lambda: self.webview.setUrl(QUrl(self.current_profile['link'])))
            return True  # ✅ Ready to proceed
        else:
            print("⚠️ Warning: No valid profile or missing 'link'")
            return False

    def step_after_profile_loaded(self):
        print("✅ Profile page fully loaded!")
        
        # ⛔ Disconnect to avoid multiple triggers
        try:
            self.webview.loadFinished.disconnect()
        except:
            pass

        

    def check_followup_connection_pending(self, step):
        self.connection_done = False
        self.log_status("🔍 Step 1: Checking pending connection button in follow-up...")

        js_code = """
            (function() {
                window.scrollBy(0, Math.random() * 5000);
                let targetContainer = document.querySelector('[class*="entry-point"], [class*="connect"], [class*="actions"]');
                if (!targetContainer) return { status: "target_container_not_found" };

                let pendingBtn = [...targetContainer.querySelectorAll('button')]
                    .find(btn => btn.innerText.trim().toLowerCase().includes('pending'));

                return { status: pendingBtn ? "Connection already pending." : "No Pending Button" };
            })();
        """

        self.webview.page().runJavaScript(js_code, lambda result: self.step3_wait_afterpending_button(step, result, "message"))

    # def _delayed_followup_execution(self, step):
    #     print("5 sec delay start")
      
    #     pending_profiles = self.fetch_pending_welcome_messages()

    #    # 2 second delay before fetching
    #     if not pending_profiles:
    #         self.log_status("No pending welcome messages.")
    #         QTimer.singleShot(1000, self.execute_next_step)

    #         #self.stop_scraping()
    #         return

    #     self.current_profile = pending_profiles[0]
    
    #     if self.current_profile and 'link' in self.current_profile:
    #             self.log_status(f"🚀 Processing profile completed Queue: {self.current_profile['name']}")

    #             # ✅ Safe signal cleanup (don't reconnect since you're not using step1_profile_load)
    #             self.safe_disconnect_signal(self.webview.loadFinished, self.step1_profile_load)

    #             QTimer.singleShot(3000, lambda: self.webview.setUrl(QUrl(self.current_profile['link'])))
    #     else:
    #             print("Warning: No profile loaded or missing 'link' key")
    #             return

    #     self.connection_done = False
    #     self.log_status("🔍 Step 1: Checking pending connection button in followup ...")
    #     self.webview.page().runJavaScript("""
    #         ( function() {
    #             window.scrollBy(0, Math.random() * 3000);
    #             let targetContainer = document.querySelector('[class*="entry-point"], [class*="connect"], [class*="actions"]');
    #             if (!targetContainer) return { status: "target_container_not_found" };

    #             let pendingBtn = [...targetContainer.querySelectorAll('button')]
    #                 .find(btn => btn.innerText.trim().toLowerCase().includes('pending'));

    #             return { status: pendingBtn ? "Connection already pending." : "No Pending Button" };
    #         })();
    #     """, lambda result: self.step3_wait_afterpending_button(step, result,"message"))


    def safe_disconnect_signal(self, signal, slot):
        try:
            signal.disconnect(slot)
        except TypeError:
            pass  # Not connected, no problem

#check connection request accept ----- end
    
# common methods -------- start

    def generate_ai_comment(self, post_content):
        """Generates a short, professional, and concise AI-based comment based on the post content"""
        prompt = f"{post_content}"

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional AI assistant that writes short and natural-sounding LinkedIn connection messages. "
                        "Messages should be friendly, professional, and under 60 words. "
                        "Avoid using names, greetings like 'Hi', or sign-offs like 'Best' or '[Your Name]'. "
                        "Write like a human trying to genuinely connect in a professional space."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=60  # Lowering max_tokens to ensure brevity
        )

        return response.choices[0].message.content.strip()
    
    def move_to_completed(self, result):
        if self.current_profile is None:
            self.log_status("⚠️ Warning: No current profile to update final status.")
            return

        self.current_profile['final_status'] = result
      

        # Load existing completed profiles
        completed_profiles = []
        if os.path.exists(self.COMPLETED_QUEUE_FILE):
            with open(self.COMPLETED_QUEUE_FILE, "r", encoding="utf-8") as file:
                try:
                    completed_profiles = json.load(file)
                except json.JSONDecodeError:
                    completed_profiles = []

        # Update or append current profile based on 'link'
        updated = False
        for idx, profile in enumerate(completed_profiles):
            if profile.get("link") == self.current_profile.get("link"):
                print(self.current_profile)
                completed_profiles[idx] = self.current_profile
                updated = True
                self.log_status("🔄 Updated existing profile in completed queue.")
                break

        if not updated:
            completed_profiles.append(self.current_profile)
            self.log_status("➕ Added new profile to completed queue.")

        # Save updated list
        with open(self.COMPLETED_QUEUE_FILE, "w", encoding="utf-8") as file:
            json.dump(completed_profiles, file, indent=4)

        self.current_profile = None
        self.log_status("🛑 Profile processing complete. Moving to the next profile...")

        self.update_queue_status()
        if self.is_scraping:
            QTimer.singleShot(5000, self.start_scraping)

#common methods --------- end

    def log_status(self, message, level="info"):
        self.status_label.setText(f"Status: {message}")
        function_name = inspect.stack()[1].function  # Get the caller function name
        if level == "error":
            print(f"[ERROR] [{function_name}] {message}")
        else:
            print(f"[LOG] [{function_name}] {message}")


#-----------------------------------------------      WORK END      -------------------------------------------


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CampaignBrowser()
    window.show()
    sys.exit(app.exec())


