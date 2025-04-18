from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTreeWidget, QTreeWidgetItem, QLabel
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt


class Sidebar(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setFixedWidth(200)
        self.setStyleSheet("""
            QWidget {
                background-color: #1E1E2E;
                color: #FFFFFF;
                border-right: 2px solid #282A36;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 12px;
                text-align: left;
                color: #D0D0D0;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #3A3D4D;
                color: white;
            }
            QTreeWidget {
                background-color: transparent;
                color: #D0D0D0;
                border: none;
            }
            QTreeWidget::item {
                padding: 6px;
            }
            QTreeWidget::item:selected {
                background-color: #4E5166;
            }
        """)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # TITLE
        title = QLabel("LINK_IN_DOST")
        title.setFont(QFont("Helvetica", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; background: transparent; border: none;")  # Ensure no background

        layout.addWidget(title)  # Add title

        # Sidebar Buttons
        # self.create_button(layout, "🏠  Dashboard", lambda: self.main_window.switch_page("dashboard"))
        # self.create_button(layout, "📊  Statistics", lambda: self.main_window.switch_page("statistics"))
        self.create_button(layout, "👤  LinkedIn Account", lambda: self.main_window.switch_page("linkedInAccount"))

        # Campaigns Section (Collapsible)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)

        campaigns = QTreeWidgetItem(["📣  Campaigns"])
        new_campaigns = QTreeWidgetItem(campaigns, ["➕  New Campaigns"])


        self.tree.addTopLevelItem(campaigns)
        self.tree.expandItem(campaigns)
        self.tree.itemClicked.connect(self.handle_navigation)
        layout.addWidget(self.tree)

        # Other Sections
        self.create_button(layout, "⚙️  Settings", lambda: self.main_window.switch_page("settings"))
        self.create_button(layout, "🌐  Web Browser", lambda: self.main_window.switch_page("browser"))

        self.setLayout(layout)

    def create_button(self, layout, text, function):
        """Creates a sidebar button with better styling."""
        btn = QPushButton(text)
        btn.setFont(QFont("Arial", 13))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(function)
        layout.addWidget(btn)

    def handle_navigation(self, item, column):
        """Handles page switching when clicking on sidebar items."""
        page_map = {
            "🏠  Dashboard": "dashboard",
            "📊  Statistics": "statistics",
            "➕  New Campaigns": "new_campaigns",

            "👤  Profile": "profile",
            "⚙️  Settings": "settings",
            "🌐  Web Browser": "browser"
        }

        page_name = page_map.get(item.text(column))
        if page_name:
            self.main_window.switch_page(page_name)
