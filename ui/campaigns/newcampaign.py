import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from ui.campaigns.campaign_auto import CampaignAuto
from ui.campaigns.campaign_browser import CampaignBrowser
from ui.campaigns.campaign_scrap_list import CampaignScrapList
from ui.campaigns.campaign_statistics import CampaignStatistics
from ui.campaigns.campaign_workflow import CampaignWorkflow

class NewCampaign(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("LinkedIn Campaign Workflow Manager")
        # self.setGeometry(100, 100, 1200, 700)
        # self.showMaximized()

        self.init_ui()

    def init_ui(self):
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # Initialize all campaign-related tabs
        self.tab_widget.addTab(CampaignWorkflow(), "Workflow")
        self.tab_widget.addTab(CampaignScrapList(), "Lists")
        self.tab_widget.addTab(CampaignBrowser(), "Campaign")
        # self.tab_widget.addTab(CampaignAuto(), "Campaign")
        self.tab_widget.addTab(CampaignStatistics(), "Statistics")

        self.apply_styles()

    def apply_styles(self):
        self.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #c4c4c4;
                background: white;
            }
            QTabBar::tab {
                background: #e0e0e0;
                padding: 10px 20px;
                font-weight: bold;
                border: 1px solid #c4c4c4;
            }
            QTabBar::tab:selected {
                background: #0078d7;
                color: white;
                border-bottom-color: #0078d7;
            }
            QLabel {
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton {
                padding: 8px 15px;
                font-weight: bold;
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #d9d9d9;
            }
            QListWidget {
                background-color: #f9f9f9;
                border: 1px solid #ccc;
            }
            QMainWindow {
                background-color: #f4f4f7;
            }
        """)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = NewCampaign()
    window.show()
    sys.exit(app.exec())
