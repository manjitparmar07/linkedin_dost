import sys
import os
import json
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QDate


class CampaignDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Campaign Analytics Dashboard")
        self.setGeometry(100, 100, 1400, 900)

        self.settings = {}
        self.daily_usage = {}
        self.accounts = []
        self.workflow = []
        self.completed_queue = []

        self.load_data()
        self.init_ui()

    def load_data(self):
        def load_json(file):
            if os.path.exists(file):
                with open(file, 'r') as f:
                    try:
                        data = json.load(f)
                        return data[0] if isinstance(data, list) and data else data
                    except Exception as e:
                        print(f"Error reading {file}: {e}")
                        return {}
            return {}

        self.settings = load_json("settingdata.json")
        self.daily_usage = load_json("dailyusage.json")
        self.accounts = load_json("accounts.json")
        self.workflow = load_json("newworkflow.json")
        self.completed_queue = load_json("completed_queue.json")

    def init_ui(self):
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header with date and title
        header_layout = QHBoxLayout()
        date_label = QLabel(f"Date: {QDate.currentDate().toString('dd MMM yyyy')}")
        date_label.setStyleSheet("font-size: 16px; font-weight: 600;")
        title_label = QLabel("Campaign Analytics Dashboard")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(date_label)
        header_layout.addStretch()
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Summary Cards Section
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)
        stats_layout.addWidget(self.create_stat_card("Likes", self.settings.get("like_limit", 0), self.daily_usage.get("like", 0)))
        stats_layout.addWidget(self.create_stat_card("Comments", self.settings.get("comment_limit", 0), self.daily_usage.get("comment", 0)))
        stats_layout.addWidget(self.create_stat_card("Connections", self.settings.get("connect_limit", 0), self.daily_usage.get("connect", 0)))
        stats_layout.addWidget(self.create_stat_card("Followups", self.settings.get("followup_limit", 0), self.daily_usage.get("followup", 0)))
        main_layout.addLayout(stats_layout)

        # Workflow Info + Account Info + Completed Queue
        info_layout = QHBoxLayout()

        # Workflow Summary
        workflow_box = self.create_info_box("Workflow Summary", self.workflow)
        info_layout.addWidget(workflow_box, 2)

        # Account Info
        account_box = self.create_info_box("Current Account", self.accounts)
        info_layout.addWidget(account_box, 1)

        # Completed Queue
        completed_box = self.create_info_box("Completed Actions", self.completed_queue)
        info_layout.addWidget(completed_box, 2)

        main_layout.addLayout(info_layout)

        self.setCentralWidget(container)
        self.setStyleSheet("""
            QWidget { font-family: 'Segoe UI'; font-size: 12px; }
            QLabel { font-size: 13px; }
            QGroupBox { border: 1px solid #ccc; border-radius: 10px; padding: 10px; background-color: #f9f9f9; }
        """)

    def create_stat_card(self, title, total, used):
        card = QGroupBox(title)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Total: {total}"))
        layout.addWidget(QLabel(f"Used: {used}"))
        layout.addWidget(QLabel(f"Remaining: {max(total - used, 0)}"))
        card.setLayout(layout)
        return card

    def create_info_box(self, title, data):
        group = QGroupBox(title)
        layout = QVBoxLayout()

        if isinstance(data, dict):
            for k, v in data.items():
                layout.addWidget(QLabel(f"{k}: {v}"))
        elif isinstance(data, list):
            for item in data[:10]:  # limit to 10 items
                layout.addWidget(QLabel(str(item)))
        else:
            layout.addWidget(QLabel("No data available."))

        group.setLayout(layout)
        return group


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CampaignDashboard()
    window.show()
    sys.exit(app.exec())
