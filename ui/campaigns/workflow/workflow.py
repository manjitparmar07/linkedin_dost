import os
import sys
import json
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class WorkflowManager:
    def __init__(self):
        self.queue = []
        self.processed = []
        self.running = False
        self.active_workflow = None

    def add_action(self, name, description):
        self.queue.append({"name": name, "description": description})

    def save_workflow(self, filename):
        folder = "workflows"
        os.makedirs(folder, exist_ok=True)
        with open(f"{folder}/{filename}", "w") as file:
            json.dump(self.queue, file)

    def load_workflow(self, filename):
        folder = "workflows"
        path = os.path.join(folder, filename)
        if os.path.exists(path):
            with open(path, "r") as file:
                self.queue = json.load(file)
            self.processed = []
            self.active_workflow = filename

    def get_saved_workflows(self):
        folder = "workflows"
        os.makedirs(folder, exist_ok=True)
        return os.listdir(folder)

class CampaignWorkflow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.workflow_manager = WorkflowManager()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.queue_list = QListWidget()
        layout.addWidget(QLabel("Current Workflow Queue"))
        layout.addWidget(self.queue_list)

        button_layout = QHBoxLayout()
   

        save_btn = QPushButton("💾 Save Workflow")
        save_btn.clicked.connect(self.save_workflow)

        load_btn = QPushButton("📂 Load Workflow")
        load_btn.clicked.connect(self.show_saved_workflows)

        for btn in [save_btn, load_btn]:
            button_layout.addWidget(btn)

        layout.addLayout(button_layout)

        self.workflow_list = QListWidget()
        self.workflow_list.itemClicked.connect(self.load_selected_workflow)
        layout.addWidget(QLabel("Saved Workflows"))
        layout.addWidget(self.workflow_list)
        self.refresh_workflow_list()

        self.action_library = self.create_action_library()
        layout.addWidget(self.action_library)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)



    def refresh_queue(self):
        self.queue_list.clear()
        for action in self.workflow_manager.queue:
            self.queue_list.addItem(f"{action['name']} - {action['description']}")

    def save_workflow(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Workflow", "workflows/", "Workflow Files (*.json)")
        if filename:
            self.workflow_manager.save_workflow(os.path.basename(filename))
            self.refresh_workflow_list()

    def show_saved_workflows(self):
        self.refresh_workflow_list()

    def refresh_workflow_list(self):
        self.workflow_list.clear()
        for workflow in self.workflow_manager.get_saved_workflows():
            self.workflow_list.addItem(workflow)

    def load_selected_workflow(self, item):
        self.workflow_manager.load_workflow(item.text())
        self.refresh_queue()

    def create_action_library(self):
        action_library_widget = QWidget()
        action_layout = QVBoxLayout()

        action_layout.addWidget(QLabel("Action Library (Double Click to Add)"))

        self.action_grid = QGridLayout()
        self.action_grid.setSpacing(10)

        self.actions = [
            {"name": "Like Post", "description": "Like a random number of posts."},
            {"name": "Comment Post", "description": "Comment on a post with AI or manual input."},
            {"name": "Send Connection Request", "description": "Send a connection request with AI or manual note."},
            {"name": "Send Follow-up Message", "description": "Send a 2nd or 3rd follow-up message."},
        ]

        row, col = 0, 0
        for action in self.actions:
            card = self.create_action_card(action)
            self.action_grid.addWidget(card, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1

        action_layout.addLayout(self.action_grid)
        action_library_widget.setLayout(action_layout)
        return action_library_widget

    def create_action_card(self, action):
        card = QWidget()
        card_layout = QVBoxLayout()

        title = QLabel(action["name"])
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))

        description = QLabel(action["description"])
        description.setWordWrap(True)

        add_button = QPushButton("➕ Add")
        add_button.clicked.connect(lambda: self.add_preset_action_from_card(action))

        card_layout.addWidget(title)
        card_layout.addWidget(description)
        card_layout.addWidget(add_button)

        card.setLayout(card_layout)
        card.setStyleSheet("""
            QWidget {
                border: 1px solid #ddd;
                padding: 10px;
                background-color: white;
                border-radius: 8px;
            }
            QLabel {
                font-size: 12px;
            }
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                padding: 5px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #005bb5;
            }
        """)

        return card

    def add_preset_action_from_card(self, action):
        if action["name"] == "Like Post":
            count, ok = QInputDialog.getInt(self, "Like Posts", "Enter number of posts to like:")
            if ok:
                self.workflow_manager.add_action(action["name"], f"Like {count} posts")
        elif action["name"] == "Comment Post":
            count, ok = QInputDialog.getInt(self, "Comment Posts", "Enter number of comments:")
            if ok:
                comment_type, ok = QInputDialog.getItem(self, "Comment Type", "Select type:", ["AI", "Manual"], 0, False)
                if ok:
                    if comment_type == "Manual":
                        text, ok = QInputDialog.getText(self, "Manual Comment", "Enter comment text:")
                        if ok:
                            self.workflow_manager.add_action(action["name"], f"Comment {count} times: {text}")
                    else:
                        self.workflow_manager.add_action(action["name"], f"Comment {count} times with AI-generated text")
        elif action["name"] == "Send Connection Request":
            method, ok = QInputDialog.getItem(self, "Connection Note", "Send with note?", ["Without Note", "With Note"], 0, False)
            if ok:
                if method == "With Note":
                    note_type, ok = QInputDialog.getItem(self, "Note Type", "Select note type:", ["AI", "Manual"], 0, False)
                    if ok:
                        if note_type == "Manual":
                            text, ok = QInputDialog.getText(self, "Manual Note", "Enter note text:")
                            if ok:
                                self.workflow_manager.add_action(action["name"], f"Send request with manual note: {text}")
                        else:
                            self.workflow_manager.add_action(action["name"], "Send request with AI-generated note")
                else:
                    self.workflow_manager.add_action(action["name"], "Send request without note")
        elif action["name"] == "Send Follow-up Message":
            message_type, ok = QInputDialog.getItem(self, "Follow-up Message", "Select message type:", ["AI", "Manual"], 0, False)
            if ok:
                if message_type == "Manual":
                    text, ok = QInputDialog.getText(self, "Manual Message", "Enter message text:")
                    if ok:
                        self.workflow_manager.add_action(action["name"], f"Send follow-up message: {text}")
                else:
                    self.workflow_manager.add_action(action["name"], "Send follow-up message with AI-generated text")
        self.refresh_queue()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CampaignWorkflow()
    window.show()
    sys.exit(app.exec())
