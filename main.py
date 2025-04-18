import os
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QLabel, QVBoxLayout
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from ui.browser import LinkedInBrowser
from ui.campaigns.newcampaign import NewCampaign
from ui.dashboard import DashboardPage
from ui.linkedinaccount import ProfilePage
from ui.settings import SettingsPage
from ui.sidebar import Sidebar


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Link_In_Dost")
        self.setGeometry(100, 100, 1400, 800)  # Default Window Size

        self.showMaximized()
        self.setStyleSheet("background-color: #2C2F33;")

        # Main Layout
        main_layout = QHBoxLayout()

        # Sidebar
        self.sidebar = Sidebar(self)
        main_layout.addWidget(self.sidebar,1)

        # Page Container
        self.pages = QStackedWidget()
        self.pages.setStyleSheet("""
            background-color: #FFFFFF;
            color: #2C3E50;
            border-radius: 10px;
            border: 0px solid #ccc;
            background-color: #f0f0f0;
        """)
        main_layout.addWidget(self.pages, 9)

        # Add Pages
        self.pages_dict = {
            # "dashboard": DashboardPage(),
            "statistics": self.create_page("📊 Statistics"),
             "new_campaigns": NewCampaign(),
            "linkedInAccount": ProfilePage(),
            "settings": SettingsPage(),
            
             "browser": LinkedInBrowser()
        }

        for page in self.pages_dict.values():
            self.pages.addWidget(page)

        # Default Page
        self.pages.setCurrentWidget(self.pages_dict["linkedInAccount"])

        # Set Main Widget
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def create_page(self, title):
        """Creates a modern page with centered title."""
        page = QWidget()
        layout = QVBoxLayout()
        label = QLabel(title)
        label.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        layout.addStretch()
        page.setLayout(layout)
        return page

    def switch_page(self, page_name):
        """Switches to the selected page."""
        if page_name in self.pages_dict:
            self.pages.setCurrentWidget(self.pages_dict[page_name])

   
if __name__ == "__main__":
    # Suppress all warnings related to Qt style parsing

    sys.stderr = open(os.devnull, 'w')

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
