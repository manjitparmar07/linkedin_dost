import os
import sys
import json
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt

class WorkflowManager:
    def __init__(self):
        self.queue = []
        self.processed = []
        self.active_workflow = None
        self.status = "inactive"


    def add_action(self, name, description, extra=None):
        action = {"name": name, "description": description}
        if extra:
            action.update(extra)
        self.queue.append(action)

    def save_workflow(self, filename):
        folder = "workflows"
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, filename)
        with open(path, "w") as file:
            json.dump({"status": self.status, "actions": self.queue}, file)
        self.active_workflow = filename

    def load_workflow(self, filename):
        folder = "workflows"
        path = os.path.join(folder, filename)
        if os.path.exists(path):
            try:
                with open(path, "r") as file:
                    content = file.read().strip()
                    if not content:
                        raise ValueError("Workflow file is empty.")
                    data = json.loads(content)  # Use json.loads to first read string data
                    self.queue = data.get("actions", [])
                    self.status = data.get("status", "inactive")
            except (json.JSONDecodeError, ValueError) as e:
                QMessageBox.critical(None, "Load Error", f"Failed to load workflow: {e}")
                self.queue = []
                self.status = "inactive"
                self.active_workflow = None

        else:
            QMessageBox.warning(None, "File Not Found", "Selected workflow file does not exist.")
        self.processed = []
        self.active_workflow = filename


    def delete_workflow(self, filename):
        folder = "workflows"
        path = os.path.join(folder, filename)
        if os.path.exists(path):
            os.remove(path)

    def get_saved_workflows(self):
        folder = "workflows"
        os.makedirs(folder, exist_ok=True)
        return [f for f in os.listdir(folder) if f.endswith(".json")]

    def find_active_workflow(self):
        folder = "workflows"
        if not os.path.exists(folder):
            return None

        for filename in os.listdir(folder):
            if filename.endswith(".json"):
                path = os.path.join(folder, filename)
                try:
                    with open(path, "r") as file:
                        data = json.load(file)
                        if data.get("status") == "active":
                            return filename
                except (json.JSONDecodeError, ValueError):
                    continue

        return None  # No active workflow found
class CampaignWorkflow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.workflow_manager = WorkflowManager()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        active_workflow = self.workflow_manager.find_active_workflow()
        if active_workflow:
            self.workflow_manager.load_workflow(active_workflow)

        self.selected_workflow_label = QLabel(f"Selected Workflow: {self.workflow_manager.active_workflow or 'None'}")
        layout.addWidget(self.selected_workflow_label)
        self.queue_list = QListWidget()
        layout.addWidget(QLabel("Current Workflow Queue"))
        layout.addWidget(self.queue_list)

        self.status_label = QLabel(f"Workflow Status: {self.workflow_manager.status}")
        layout.addWidget(self.status_label)

        button_layout = QHBoxLayout()

        save_btn = QPushButton("💾 Save Workflow")
        save_btn.clicked.connect(self.save_workflow)

        
        
        delete_btn = QPushButton("🗑 Delete Workflow")
        delete_btn.clicked.connect(self.delete_selected_workflow)
        
        new_btn = QPushButton("✨ New Workflow")
        new_btn.clicked.connect(self.create_new_workflow)

        toggle_status_btn = QPushButton("Toggle Workflow Status")
        toggle_status_btn.clicked.connect(self.toggle_workflow_status)

        for btn in [save_btn, delete_btn, new_btn, toggle_status_btn]:
            button_layout.addWidget(btn)

        layout.addLayout(button_layout)

        self.workflow_list = QListWidget()
        self.workflow_list.itemClicked.connect(self.load_selected_workflow)
        layout.addWidget(QLabel("Saved Workflows"))
        layout.addWidget(self.workflow_list)
        self.refresh_workflow_list()

        if active_workflow:
            self.highlight_selected_workflow(active_workflow)

        self.action_library = self.create_action_library()
        layout.addWidget(self.action_library)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def refresh_queue(self):
        self.queue_list.clear()
        for action in self.workflow_manager.queue:
            self.queue_list.addItem(f"{action['name']} - {action['description']}")
        self.status_label.setText(f"Workflow Status: {self.workflow_manager.status}")
        self.selected_workflow_label.setText(f"Selected Workflow: {self.workflow_manager.active_workflow or 'None'}")

    

    def save_workflow(self):
        if self.workflow_manager.active_workflow:
            filename = self.workflow_manager.active_workflow
        else:
            filename, _ = QFileDialog.getSaveFileName(self, "Save Workflow", "workflows/", "Workflow Files (*.json)")
            filename = os.path.basename(filename) if filename else None
        
        if filename:
            self.workflow_manager.save_workflow(filename)
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
        self.highlight_selected_workflow(item.text())

    def highlight_selected_workflow(self, filename):
        for i in range(self.workflow_list.count()):
            item = self.workflow_list.item(i)
            if item.text() == filename:
                item.setBackground(QColor(173, 216, 230))  # Light blue for selected workflow
            else:
                item.setBackground(QColor(255, 255, 255))  # White for others    
    

    def delete_selected_workflow(self):
        selected_item = self.workflow_list.currentItem()
        if selected_item:
            reply = QMessageBox.question(self, "Delete Workflow", f"Are you sure you want to delete {selected_item.text()}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.workflow_manager.delete_workflow(selected_item.text())
                self.refresh_workflow_list()

    def create_new_workflow(self):
        self.workflow_manager.queue = []
        self.workflow_manager.active_workflow = None
        self.workflow_manager.status = "inactive"
        self.refresh_queue()
        QMessageBox.information(self, "New Workflow", "A new workflow has been created.")
    
    def toggle_workflow_status(self):
        self.workflow_manager.status = "active" if self.workflow_manager.status == "inactive" else "inactive"
        
        # Save the updated status to the JSON file
        if self.workflow_manager.active_workflow:
            self.workflow_manager.save_workflow(self.workflow_manager.active_workflow)
        
        self.refresh_queue()
        QMessageBox.information(self, "Workflow Status", f"Workflow is now {self.workflow_manager.status}.")

    def create_action_library(self):
        action_library_widget = QWidget()
        action_layout = QVBoxLayout()

        action_layout.addWidget(QLabel("Action Library (Double Click to Add)"))
        self.action_grid = QGridLayout()
        self.action_grid.setSpacing(10)

        self.actions = [
            {"name": "Like_Post", "description": "Like a random number of posts."},
            {"name": "Comment_Post", "description": "Comment on a post with AI or manual input."},
            {"name": "Send_Connection_Request", "description": "Send a connection request with AI or manual note."},
            {"name": "Send_Follow_up_Message", "description": "Send a 2nd or 3rd follow-up message."},
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
        return card
    
    def add_preset_action_from_card(self, action):
        if action["name"] == "Like_Post":
            count, ok = QInputDialog.getInt(self, "Like Posts", "Enter number of posts to like:")
            if ok:
                self.workflow_manager.add_action(
                    name=action["name"],
                    description=f"Like {count} posts",
                    extra={"count": count}
                )

        elif action["name"] == "Comment_Post":
            count, ok = QInputDialog.getInt(self, "Comment Posts", "Enter number of comments:")
            if ok:
                comment_type, ok = QInputDialog.getItem(self, "Comment Type", "Select type:", ["AI", "Mannual"], 0, False)
                if ok:
                    if comment_type == "Mannual":
                        text, ok = QInputDialog.getText(self, "Manual Comment", "Enter comment text:")
                        if ok:
                            self.workflow_manager.add_action(
                                name=action["name"],
                                description=f"Comment {count} times with Mannual-generated text",
                                extra={"count": count, "comment_type": "Mannual", "Message": text}
                            )
                    else:
                        self.workflow_manager.add_action(
                            name=action["name"],
                            description=f"Comment {count} times with AI-generated text",
                            extra={"count": count, "comment_type": "AI", "Message": ""}
                        )

        elif action["name"] == "Send_Connection_Request":
            method, ok = QInputDialog.getItem(self, "Connection Note", "Send with note?", ["Without Note", "With Note"], 0, False)
            if ok:
                if method == "With Note":
                    note_type, ok = QInputDialog.getItem(self, "Note Type", "Select note type:", ["AI", "Mannual"], 0, False)
                    if ok:
                        if note_type == "Mannual":
                            text, ok = QInputDialog.getText(self, "Manual Note", "Enter note text:")
                            if ok:
                                self.workflow_manager.add_action(
                                    name=action["name"],
                                    description="Send request with Mannual-generated note",
                                    extra={"send_type": "withnote", "note_type": "Mannual", "Message": text}
                                )
                        else:
                            self.workflow_manager.add_action(
                                name=action["name"],
                                description="Send request with AI-generated note",
                                extra={"send_type": "withnote", "note_type": "AI", "Message": ""}
                            )
                else:
                    self.workflow_manager.add_action(
                        name=action["name"],
                        description="Send request without note",
                        extra={"send_type": "withoutnote"}
                    )

        elif action["name"] == "Send_Follow_up_Message":
            message_type, ok = QInputDialog.getItem(self, "Follow-up Message", "Select message type:", ["AI", "Mannual"], 0, False)
            if ok:
                if message_type == "Mannual":
                    text, ok = QInputDialog.getText(self, "Manual Message", "Enter message text:")
                    if ok:
                        self.workflow_manager.add_action(
                            name=action["name"],
                            description="Send follow-up message with Mannual-generated text",
                            extra={"message_type": "Mannual", "Message": text}
                        )
                else:
                    self.workflow_manager.add_action(
                        name=action["name"],
                        description="Send follow-up message with AI-generated text",
                        extra={"message_type": "AI", "Message": ""}
                    )

        self.refresh_queue()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CampaignWorkflow()
    window.show()
    sys.exit(app.exec())
