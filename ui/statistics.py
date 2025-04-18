from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

class Statistics(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Statistics Page (Coming Soon)"))
        self.setStyleSheet("background-color: #2e2e3f; color: white;")
