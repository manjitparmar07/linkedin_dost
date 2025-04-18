import sys
import random
import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QComboBox
)
from PyQt6.QtGui import QFont, QColor, QPalette
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        # Title & Filter
        title_layout = QHBoxLayout()
        title = QLabel("📊 Dashboard - Insights")
        title.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Time Range Dropdown (Better Styling)
        self.time_filter = QComboBox()
        self.time_filter.addItems(["Last 7 Days", "Last 14 Days"])
        self.time_filter.setStyleSheet("""
            QComboBox {
                background-color: #EAF2F8;
                color: #2C3E50;
                padding: 8px;
                border-radius: 8px;
                font-size: 14px;
                border: 2px solid #3498DB;
            }
            QComboBox:hover {
                background-color: #D6EAF8;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #3498DB;
                width: 40px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #3498DB;
                selection-background-color: #5DADE2;
                padding: 4px;
            }
        """)
        self.time_filter.currentIndexChanged.connect(self.update_charts)

        title_layout.addWidget(title)
        title_layout.addStretch()
        title_layout.addWidget(self.time_filter)

        layout.addLayout(title_layout)

        # Charts Section
        chart_layout = QHBoxLayout()

        self.canvas_activity = FigureCanvas(plt.Figure(figsize=(4, 3)))
        chart_layout.addWidget(self.create_chart_card("📈 Activity Overview", self.canvas_activity))

        self.canvas_pie = FigureCanvas(plt.Figure(figsize=(4, 3)))
        chart_layout.addWidget(self.create_chart_card("📊 Data Distribution", self.canvas_pie))

        layout.addLayout(chart_layout)

        # Stats Section
        stats_layout = QGridLayout()
        self.stat_cards = {
            "total": self.create_stat_card("🟢 Total Activity", "0"),
            "messages": self.create_stat_card("🟡 Messages Sent", "0"),
            "failed": self.create_stat_card("🔴 Failed Attempts", "0"),
            "success": self.create_stat_card("🎯 Success Rate", "0%")
        }

        stats_layout.addWidget(self.stat_cards["total"], 0, 0)
        stats_layout.addWidget(self.stat_cards["messages"], 0, 1)
        stats_layout.addWidget(self.stat_cards["failed"], 1, 0)
        stats_layout.addWidget(self.stat_cards["success"], 1, 1)

        layout.addLayout(stats_layout)


        self.setLayout(layout)
        self.plot_activity_chart()
        self.plot_pie_chart()

    def create_chart_card(self, title, canvas):
        """Creates a stylish chart card with hover effect"""
        card = QFrame()
        card.setStyleSheet("""
            background-color: #FFFFFF; 
            border-radius: 10px; 
            padding: 15px;
            transition: all 0.3s ease-in-out;
        """)
        card.setGraphicsEffect(None)

        card_layout = QVBoxLayout()
        label = QLabel(title)
        label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addWidget(label)
        card_layout.addWidget(canvas)
        card.setLayout(card_layout)

        return card

    def create_stat_card(self, title, value):
        """Creates a stat card with hover effect"""
        card = QFrame()
        card.setStyleSheet("""
            background-color: #F4F6F7; 
            border-radius: 10px;
            padding: 15px;
            transition: all 0.3s ease-in-out;
        """)
        card_layout = QVBoxLayout()

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #34495E;")

        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        value_label.setStyleSheet("color: #4A90E2;")

        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)
        card.setLayout(card_layout)

        return card

    def plot_activity_chart(self):
        """Plots a bar chart for user activity and ensures proper date visibility."""
        self.canvas_activity.figure.clear()  # Clear previous figure
        ax = self.canvas_activity.figure.add_subplot(111)

        # Determine the number of days based on the selected filter
        days = 7 if self.time_filter.currentIndex() == 0 else 14
        dates = [datetime.date(2025, 2, i) for i in range(1, days + 1)]
        activity_counts = [random.randint(5, 20) for _ in dates]

        ax.bar(dates, activity_counts, color="#4A90E2", label="Activity")

        # Improve X-axis formatting
        ax.set_title("Activity Overview", fontsize=12, fontweight="bold")
        ax.set_ylabel("Actions Count")
        ax.set_xlabel("Date")

        # Use date formatting for better visibility
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))  # Format as 'Feb 01'
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1 if days <= 7 else 2))  # Show every 1-2 days

        ax.tick_params(axis="x", rotation=45, labelsize=10)  # Rotate labels for readability
        ax.grid(axis="y", linestyle="--", alpha=0.6)

        ax.legend()
        self.canvas_activity.draw()

    def plot_pie_chart(self):
        """Plots a pie chart and clears old data before updating."""
        ax = self.canvas_pie.figure.clear()  # Clear previous figure
        ax = self.canvas_pie.figure.add_subplot(111)

        labels = ["Messages Sent", "Failed Attempts", "Successful Actions"]
        values = [random.randint(30, 70), random.randint(5, 15), random.randint(20, 50)]
        colors = ["#4A90E2", "#E74C3C", "#2ECC71"]

        ax.pie(values, labels=labels, autopct="%1.1f%%", colors=colors, startangle=140)
        ax.set_title("Message Distribution", fontsize=12, fontweight="bold")

        self.canvas_pie.draw()  # Redraw with new data

    def update_charts(self):
        """Updates charts dynamically based on time range selection"""
        self.plot_activity_chart()
        self.plot_pie_chart()




class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Link_In_Dost - Dashboard")
        self.showMaximized()
        self.setStyleSheet("background-color: #F0F3F4;")

        main_layout = QVBoxLayout()
        self.dashboard_page = DashboardPage()
        main_layout.addWidget(self.dashboard_page)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
