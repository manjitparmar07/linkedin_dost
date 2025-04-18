# start.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PyQt6.QtWidgets import QApplication
from ui.onboardingscreen import OnboardingScreen
from ui.loginscreen import LoginScreen
from main import MainWindow


class AppController:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.onboarding = None
        self.login = None
        self.main = None

    def show_onboarding(self):
        self.onboarding = OnboardingScreen(self.show_login)
        self.onboarding.show()

    def show_login(self):
        self.login = LoginScreen(self.show_main)
        self.login.show()

    def show_main(self):
        self.main = MainWindow()
        self.main.show()

    def run(self):
        self.show_onboarding()
        sys.exit(self.app.exec())


if __name__ == "__main__":
    controller = AppController()
    controller.run()
