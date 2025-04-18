from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QRect
from PyQt6.QtGui import QFont, QPixmap


class OnboardingScreen(QWidget):
    def __init__(self, show_login_callback):
        super().__init__()
        self.setWindowTitle("Welcome - LBM Solutions")
        self.setFixedSize(600, 400)
        self.setStyleSheet("background-color: #f3f6fa;")
        self.show_login_callback = show_login_callback

        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # ✅ ensures content centers in the window

        # Logo/Image
        self.logo = QLabel(self)
        pixmap = QPixmap("assets/linkedinpage.jpg")
        self.logo.setPixmap(pixmap)
        self.logo.setScaledContents(True)
        self.logo.setFixedSize(300, 300)
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)  # ✅ aligns the pixmap inside QLabel

        # Title
        self.title = QLabel("Welcome to LBM Solutions")
        self.title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.title.setStyleSheet("color: #0a66c2;")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Subtitle
        subtitle = QLabel("Connecting you to your LinkedIn productivity")
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #333;")

        # Add widgets to layout
        layout.addStretch()
        layout.addWidget(self.logo, alignment=Qt.AlignmentFlag.AlignHCenter)  # ✅ force center
        layout.addWidget(self.title)
        layout.addWidget(subtitle)
        layout.addStretch()
        self.setLayout(layout)

        # Animate logo bounce and title
       # self.animate_logo()

        # Transition to login screen after 5 seconds
        QTimer.singleShot(5000, self.show_login)

    def animate_logo(self):
        self.bounce = QPropertyAnimation(self.logo, b"geometry")
        self.bounce.setDuration(1000)
        self.bounce.setStartValue(QRect(150, 40, 300, 300))  # position based on fixed size
        self.bounce.setEndValue(QRect(150, 20, 300, 300))
        self.bounce.setLoopCount(2)
        self.bounce.start()

    def show_login(self):
        self.show_login_callback()
        self.close()
