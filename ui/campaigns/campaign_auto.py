import sys
import threading
import time
import random
import os
import json

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QWidget,
    QVBoxLayout, QHBoxLayout, QProgressBar, QFrame, QSplitter, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QGroupBox, QGridLayout


class CampaignAuto(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LinkedIn Campaign Automation")
        self.setGeometry(100, 100, 600, 300)
        
        self.queue = []
        self.followups = []
        self.workflow = []
        self.is_running = False
        self.current_step_queue = 0
        self.current_step_followup = 0

        self.completed_queue = self.load_json("completed_queue.json")  # Initialize completed_queue
        self.queue = self.load_json("queue.json")

        # Store the last modification time of the completed_queue.json file
        self.last_modified_time = self.get_file_modification_time("completed_queue.json")

        # Set up a timer to check the file every 5 min 
        self.file_check_timer = QTimer(self)
        self.file_check_timer.timeout.connect(self.check_for_updates)
        self.file_check_timer.start(50000)  # Check every 5 min


        self.init_ui()


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
                transition: background-color 0.3s;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
            QWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 12px;
            }
            QLabel {
                font-weight: bold;
                font-size: 15px;
            }
            .status-card {
                background-color: #2c3e50;
                color: white;
                border-radius: 8px;
                padding: 10px;
            }
            .stat-card {
                background-color: #ecf0f1;
                color: #34495e;
                border-radius: 8px;
                padding: 12px;
                margin-right: 12px;
                font-size: 14px;
                display: inline-block;
                min-width: 160px;
                text-align: center;
            }
            .stat-card:hover {
                background-color: #dcdfe1;
            }
        """)

        # --- Top Widget (20%) ---
        top_widget = QWidget()
        top_layout = QVBoxLayout()
        top_layout.setContentsMargins(10, 10, 10, 10)
        top_layout.setSpacing(12)

        # --- Line 1: Buttons + Status ---
        line1_layout = QHBoxLayout()

        button_height = 36

        self.start_button = QPushButton("▶ Start Workflow")
        self.start_button.setStyleSheet("background-color: #0077B5; color: white;")
        self.start_button.setFixedHeight(button_height)

        self.stop_button = QPushButton("⏹ Stop Workflow")
        self.stop_button.setStyleSheet("background-color: #e74c3c; color: white;")
        self.stop_button.setFixedHeight(button_height)

        self.status_label = QLabel("Status: Idle")
        self.status_label.setStyleSheet("color: white;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        status_card = QWidget()
        status_card.setFixedHeight(button_height)
        status_card.setStyleSheet("background-color: #2c3e50; border-radius: 4px;")
        status_card_layout = QVBoxLayout()
        status_card_layout.setContentsMargins(8, 0, 8, 0)
        status_card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_card_layout.addWidget(self.status_label)
        status_card.setLayout(status_card_layout)

        line1_layout.addWidget(self.start_button)
        line1_layout.addWidget(self.stop_button)
        line1_layout.addStretch()
        line1_layout.addWidget(status_card)

        # --- Line 2: Stats ---
        line2_layout = QHBoxLayout()

        self.total_queue_label = QLabel("📋 Queue: 0")
        self.total_likes_label = QLabel("👍 Likes: 0")
        self.total_comments_label = QLabel("💬 Comments: 0")
        self.total_connections_label = QLabel("🔗 Connections: 0")
        self.total_followups_label = QLabel("📨 Follow-ups: 0")

        stats = [
            self.total_queue_label, self.total_likes_label, self.total_comments_label,
            self.total_connections_label, self.total_followups_label
        ]

        for widget in stats:
            stat_card = QWidget()
            stat_card.setStyleSheet("background-color: #ecf0f1; color: #34495e; border-radius: 8px; padding: 12px; margin-right: 12px; font-size: 14px; display: inline-block; min-width: 160px; text-align: center;")
            stat_card_layout = QVBoxLayout()
            stat_card_layout.addWidget(widget)
            stat_card.setLayout(stat_card_layout)
            line2_layout.addWidget(stat_card)

        top_layout.addLayout(line1_layout)
        top_layout.addLayout(line2_layout)
        top_widget.setLayout(top_layout)

        # --- Bottom Widget (80%) ---
        bottom_widget = QWidget()
        bottom_widget.setStyleSheet("background-color: white;")
        bottom_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # --- Splitter for vertical layout ---
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(top_widget)
        splitter.addWidget(bottom_widget)
        splitter.setSizes([200, 800])  # approx 20-80

        # --- Final Layout ---
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.addWidget(splitter)
        container.setLayout(container_layout)
        self.setCentralWidget(container)

        self.update_stats()




    def log_status(self, message):
        self.status_label.setText(f"Status: {message}")
        print(message)

    # === START WORKFLOW ===
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

        if not self.workflow:
            QMessageBox.critical(self, "Empty Workflow", "No steps found in the workflow.")
            return

        self.load_data_sources_queue()
        self.load_data_sources_followup()

        self.is_running = True
        self.current_step_queue = 0
        self.current_step_followup = 0
        self.log_status("🚀 Starting workflows...")
        self.run_parallel_workflows()

    def stop_workflows(self):
        self.is_running = False
        self.log_status("🛑 Automation stopped.")

    # === LOAD DATA ===
    def load_data_sources_queue(self):
        new_queue = self.load_json("queue.json")
        if new_queue != self.queue:
            self.queue = new_queue
            print("🔄 Queue updated:", self.queue)
        else:
            print("✅ Queue already up to date.")

    def load_data_sources_followup(self):
        new_followups = self.load_json("completed_queue.json")
        # Filter only 'Pending' followups
        new_followups = [item for item in new_followups if item.get("followup_message") == "Pending"]
        
        if new_followups != self.followups:
            self.followups = new_followups
            print("🔄 Followups updated:", self.followups)
        else:
            print("✅ Followups already up to date.")


    def load_json(self, path):
        try:
            with open(path, "r") as file:
                content = file.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except Exception as e:
            self.log_status(f"⚠️ Failed to load {path}: {e}")
            return []

    # === WORKFLOW FILE ===
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
                except Exception:
                    continue

        if len(active_files) == 1:
            return active_files[0]
        elif len(active_files) > 1:
            return active_files
        return None

    def load_workflow(self, filename):
        folder = "workflows"
        path = os.path.join(folder, filename)
        try:
            with open(path, "r") as file:
                data = json.load(file)
                self.workflow = data.get("actions", [])
        except Exception as e:
            QMessageBox.critical(self, "Workflow Load Error", str(e))
            self.workflow = []

    # === RUN IN THREADS ===
    def run_parallel_workflows(self):
        threading.Thread(target=self.run_workflow_queue, daemon=True).start()
        threading.Thread(target=self.run_workflow_followups, daemon=True).start()

    def run_workflow_queue(self):
        allowed_steps = {"Like_Post", "Comment_Post", "Send_Connection_Request"}
        queue_steps = [step for step in self.workflow if step.get("name") in allowed_steps]

        while self.is_running and self.current_step_queue < len(self.queue):
            record = self.queue[self.current_step_queue]
            self.current_step_queue += 1
            for step in queue_steps:
                if not self.is_running:
                    break
                self.execute_step(step, record)
                time.sleep(random.uniform(1, 3))
        self.log_status("✅ Queue workflow finished.")

    def run_workflow_followups(self):
        allowed_steps = {"Send_Follow_up_Message"}
        followup_steps = [step for step in self.workflow if step.get("name") in allowed_steps]

        while self.is_running and self.current_step_followup < len(self.followups):
            record = self.followups[self.current_step_followup]
            self.current_step_followup += 1
            for step in followup_steps:
                if not self.is_running:
                    break
                self.execute_step(step, record)
                time.sleep(random.uniform(30, 60))
        self.log_status("✅ Follow-up workflow finished.")

    # === STEP EXECUTION ===
    def execute_step(self, step, record):
        step_name = step.get("name", "unknown")
        self.log_status(f"⚙️ Executing {step_name} for {record.get('name', 'User')}")
        method = getattr(self, f"Step_{step_name}", None)
        if method:
            method(record)
        else:
            self.log_status(f"❌ No method for step: {step_name}")

    # === DUMMY ACTIONS ===
    def Step_Like_Post(self, record):
        profile_data = {
            "image": record.get("image", ""),
            "link": record.get("link", ""),
            "location": record.get("location", ""),
            "name": record.get("name", ""),
            "title": record.get("title", "")
        }
        # After like action done
        self.update_completed_queue(profile_data, "like_post", "Done")
        self.log_status("👍 Liking post...")


    def Step_Comment_Post(self, record):
        profile_data = {
            "image": record.get("image", ""),
            "link": record.get("link", ""),
            "location": record.get("location", ""),
            "name": record.get("name", ""),
            "title": record.get("title", "")
        }
        # After comment action done
        self.update_completed_queue(profile_data, "comment_post", "Done")
        self.log_status("💬 Commenting post...")

    def Step_Send_Connection_Request(self, record):
        profile_data = {
            "image": record.get("image", ""),
            "link": record.get("link", ""),
            "location": record.get("location", ""),
            "name": record.get("name", ""),
            "title": record.get("title", "")
        }
        # After connection request done
        self.update_completed_queue(profile_data, "connection_request", "Done")
        self.log_status("🔗 Sending connection request...")

    def Step_Send_Follow_up_Message(self, record):
        profile_data = {
            "image": record.get("image", ""),
            "link": record.get("link", ""),
            "location": record.get("location", ""),
            "name": record.get("name", ""),
            "title": record.get("title", "")
        }
        # After follow-up message is done
        self.update_completed_queue(profile_data, "followup_message", "Done")
        self.update_completed_queue(profile_data, "final_status", "Done")
        self.log_status("📨 Sending follow-up message...")

    def update_completed_queue(self, profile_data, field, value):
        """
        profile_data: dict with keys like 'profile_id', 'image', 'name', etc.
        field: 'like_post', 'comment_post', 'connection_request', 'followup_message', 'final_status'
        value: 'Pending' or 'Done'
        """

        updated = False
        for item in self.completed_queue:
            if item.get("link") == profile_data.get("link"):  # Use link as unique key
                item[field] = value
                updated = True
                break

        if not updated:
            # Initialize entry with all fields
            new_entry = {
                "image": profile_data.get("image", ""),
                "link": profile_data.get("link", ""),
                "location": profile_data.get("location", ""),
                "name": profile_data.get("name", ""),
                "title": profile_data.get("title", ""),
                "like_post": "Pending",
                "comment_post": "Pending",
                "connection_request": "Pending",
                "followup_message": "Pending",
                "final_status": "Pending",
            }
            new_entry[field] = value  # Set current field to actual value
            self.completed_queue.append(new_entry)

        self.save_completed_queue()

    def save_completed_queue(self):
        with open("completed_queue.json", "w") as file:
            json.dump(self.completed_queue, file, indent=4)
    def get_file_modification_time(self, path):
        """Get the last modification time of the file."""
        try:
            return os.path.getmtime(path)
        except Exception:
            return 0

    def check_for_updates(self):
        """Check if the completed_queue.json file has been updated."""
        current_modified_time = self.get_file_modification_time("completed_queue.json")
        if current_modified_time > self.last_modified_time:
            self.last_modified_time = current_modified_time
            self.load_data_sources_followup()  # Reload data if file has been updated
            self.log_status("✅ completed_queue.json has been updated.")

    def update_stats(self):
        like_done = sum(1 for i in self.completed_queue if i.get("like_post") == "Done")
        comment_done = sum(1 for i in self.completed_queue if i.get("comment_post") == "Done")
        connection_done = sum(1 for i in self.completed_queue if i.get("connection_request") == "Done")
        followup_done = sum(1 for i in self.completed_queue if i.get("followup_message") == "Done")

        self.total_queue_label.setText(f"📋 Total in Queue: {len(self.queue)}")
        self.total_likes_label.setText(f"👍 Likes Done: {like_done}")
        self.total_comments_label.setText(f"💬 Comments Done: {comment_done}")
        self.total_connections_label.setText(f"🔗 Connections Done: {connection_done}")
        self.total_followups_label.setText(f"📨 Follow-ups Done: {followup_done}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CampaignAuto()
    window.show()
    sys.exit(app.exec())
