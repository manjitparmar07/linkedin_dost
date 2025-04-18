from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget
from ui.theme import Theme

class Header(QWidget):
    def __init__(self, parent):
        super().__init__()

        layout = QHBoxLayout(self)
        self.setStyleSheet(Theme.header)

        title = QLabel("Welcome, Manjit Parmar")
        title.setStyleSheet(Theme.header_title)

        btn_notification = QPushButton("🔔")
        btn_profile = QPushButton("👤")
        for btn in [btn_notification, btn_profile]:
            btn.setStyleSheet(Theme.header_button)

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(btn_notification)
        layout.addWidget(btn_profile)

        self.setLayout(layout)
