import os
import sys
import json
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath
from PyQt6.QtCore import Qt, QUrl, QRect
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import Qt


class CampaignStatistics(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Campaign Analytics Dashboard")
        self.resize(1280, 800)

        self.current_page = 1
        self.records_per_page = 15  # 5x3 grid
        self.columns = 5

        self.all_leads = []
        self.network_manager = QNetworkAccessManager()
        self.view_mode = 'grid'  # can be 'grid' or 'list'

        self.init_ui()
        self.load_data()

    def init_ui(self):
        container = QWidget()
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

                # Top Bar Layout (toggle + others)
        top_bar = QHBoxLayout()
        top_bar.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.toggle_btn = QPushButton("Switch to List View")
        self.toggle_btn.setFixedWidth(150)
        self.toggle_btn.clicked.connect(self.toggle_view_mode)
        top_bar.addWidget(self.toggle_btn)

        self.main_layout.addLayout(top_bar)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.cards_widget = QWidget()
        self.cards_layout = QGridLayout(self.cards_widget)
        self.cards_layout.setSpacing(12)

        self.scroll_area.setWidget(self.cards_widget)
        self.main_layout.addWidget(self.scroll_area)

        # Pagination
        self.pagination_layout = QHBoxLayout()
        self.pagination_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addLayout(self.pagination_layout)

        self.setCentralWidget(container)
        self.apply_styles()
    
    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI';
                font-size: 11px;
            }
            QPushButton {
                padding: 4px 8px;
                border-radius: 5px;
                background-color: #dbeafe;
                color: #1d4ed8;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #bfdbfe;
            }
            QLabel[role='title'] {
                font-weight: bold;
                font-size: 13px;
            }
            QLabel[role='status'] {
                font-weight: 600;
                padding: 1px 4px;
                border-radius: 4px;
                color: white;
                font-size: 10px;
            }
        """)

    def toggle_view_mode(self):
        if self.view_mode == 'grid':
            self.view_mode = 'list'
            self.columns = 1
            self.records_per_page = 10
            self.toggle_btn.setText("Switch to Grid View")
        else:
            self.view_mode = 'grid'
            self.columns = 5
            self.records_per_page = 15
            self.toggle_btn.setText("Switch to List View")
        self.display_data()

    def load_data(self):
        json_file = "completed_queue.json"
        if os.path.exists(json_file):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    self.all_leads = json.load(f)
            except Exception as e:
                print(f"Error loading data: {e}")
        else:
            print(f"{json_file} not found.")

        self.display_data()

    def display_data(self):
        while self.cards_layout.count():
            child = self.cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        start = (self.current_page - 1) * self.records_per_page
        leads = self.all_leads[start:start + self.records_per_page]

        if self.view_mode == 'list':
            self.display_table_header()
            for i, lead in enumerate(leads):
                self.cards_layout.addWidget(self.create_table_row(lead), i + 1, 0)
        else:
            for i, lead in enumerate(leads):
                row, col = divmod(i, self.columns)
                self.cards_layout.addWidget(self.create_card(lead), row, col)

        self.update_pagination()

    def display_table_header(self):
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(5)

        headers = [
            ("Photo", 50),
            ("Name", 200),
            ("Title", 300),
            ("Like", 60),
            ("Comment", 60),
            ("Connect", 60),
            ("Welcome", 60),
            ("Status", 60),
            ("Action", 60),
        ]

        for text, width in headers:
            label = QLabel(text)
            label.setFixedWidth(width)
            label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            label.setStyleSheet("font-weight: bold;")
            layout.addWidget(label)

        self.cards_layout.addWidget(header, 0, 0)


    def create_table_row(self, lead):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(5)

        def make_label(text, width, align=Qt.AlignmentFlag.AlignCenter, bold=False):
            label = QLabel(text)
            label.setFixedWidth(width)
            label.setAlignment(align)
            if bold:
                label.setStyleSheet("font-weight: bold;")
            return label

        # Photo
        image_label = QLabel()
        image_label.setFixedSize(36, 36)
        image_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.load_image(lead["imageUrl"], image_label)
        layout.addWidget(image_label)

        # Text fields
        layout.addWidget(make_label(lead.get("name", "N/A"), 200, Qt.AlignmentFlag.AlignVCenter))
        layout.addWidget(make_label(lead.get("title", "N/A"), 300, Qt.AlignmentFlag.AlignVCenter))

        # Status fields with color
        def status_label(value, width, color):
            lbl = QLabel(value)
            lbl.setFixedWidth(width)
            lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            lbl.setStyleSheet(f"background-color: {color}; padding: 2px 6px; border-radius: 4px; color: white;")
            return lbl

        layout.addWidget(status_label(lead.get("like_done", "No"), 60, "#22c55e"))
        layout.addWidget(status_label(lead.get("comment_done", "No"), 60, "#3b82f6"))
        layout.addWidget(status_label(lead.get("connection_sent", "No"), 60, "#6366f1"))

        welcome_color = "#f59e0b" if lead.get("welcome_sent") == "Pending" else "#10b981"
        layout.addWidget(status_label(lead.get("welcome_sent", "Pending"), 60, welcome_color))

        final_color = "#16a34a" if lead.get("final_status", "").lower() == "done" else "#f97316"
        layout.addWidget(status_label(lead.get("final_status", "Pending"), 60, final_color))

        # Action Button
        view_btn = QPushButton("View")
        view_btn.setFixedWidth(60)
        view_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(lead.get("link", "#"))))
        layout.addWidget(view_btn)

        return row


    def create_card(self, lead):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 2px;
                padding: 2px;
            }
        """)
        if self.view_mode == 'grid':
            card.setFixedSize(320, 280)
        else:
            card.setFixedHeight(140)
            card.setMinimumWidth(950)
        layout = QVBoxLayout(card)
        layout.setSpacing(3)

        # Header
        header = QHBoxLayout()
        image_label = QLabel()
        image_label.setFixedSize(36, 36)
        self.load_image(lead["imageUrl"], image_label)
        header.addWidget(image_label)

        name_title = QVBoxLayout()
        name = QLabel(lead.get("name", "N/A"))
        name.setProperty("role", "title")
        name.setStyleSheet("font-size: 12px;")
        title = QLabel(lead.get("title", "N/A"))
        title.setStyleSheet("font-size: 10px; color: gray;")
        name_title.addWidget(name)
        name_title.addWidget(title)

        header.addLayout(name_title)
        layout.addLayout(header)

        # Status
        tags = QGridLayout()
        tags.setSpacing(4)
        status_data = [
            ("Like", lead.get("like_done", "No"), "#22c55e"),
            ("Comment", lead.get("comment_done", "No"), "#3b82f6"),
            ("Connect", lead.get("connection_sent", "No"), "#6366f1"),
            ("Welcome", lead.get("welcome_sent", "Pending"), "#f59e0b" if lead.get("welcome_sent") == "Pending" else "#10b981"),
            ("Status", lead.get("final_status", "Pending"), "#16a34a" if lead.get("final_status", "").lower() == "done" else "#f97316"),
        ]

        for i, (label, value, color) in enumerate(status_data):
            tags.addWidget(QLabel(label), i, 0)
            status_label = QLabel(value)
            status_label.setProperty("role", "status")
            status_label.setStyleSheet(f"background-color: {color};")
            tags.addWidget(status_label, i, 1)

        layout.addLayout(tags)

        # View Profile Button
        view_btn = QPushButton("View")
        view_btn.setStyleSheet("font-size: 10px;")
        view_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(lead.get("link", "#"))))
        layout.addWidget(view_btn, alignment=Qt.AlignmentFlag.AlignRight)

        return card

    def load_image(self, url, label):
        request = QNetworkRequest(QUrl(url))
        reply = self.network_manager.get(request)

        def handle_reply():
            if reply.error() == reply.NetworkError.NoError:
                pixmap = QPixmap()
                pixmap.loadFromData(reply.readAll())
                label.setPixmap(self.make_circle(pixmap))
            reply.deleteLater()

        reply.finished.connect(handle_reply)

    def make_circle(self, pixmap):
        size = 36
        source_size = min(pixmap.width(), pixmap.height())
        rect = QRect(
            (pixmap.width() - source_size) // 2,
            (pixmap.height() - source_size) // 2,
            source_size,
            source_size
        )
        square_pixmap = pixmap.copy(rect)
        scaled = square_pixmap.scaled(size, size, Qt.AspectRatioMode.IgnoreAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)

        circle = QPixmap(size, size)
        circle.fill(Qt.GlobalColor.transparent)

        painter = QPainter(circle)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, scaled)
        painter.end()

        return circle

    def update_pagination(self):
        for i in reversed(range(self.pagination_layout.count())):
            widget = self.pagination_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        total_pages = max(1, (len(self.all_leads) + self.records_per_page - 1) // self.records_per_page)

        prev_btn = QPushButton("⬅ Prev")
        prev_btn.setEnabled(self.current_page > 1)
        prev_btn.clicked.connect(self.prev_page)
        self.pagination_layout.addWidget(prev_btn)

        for i in range(1, total_pages + 1):
            btn = QPushButton(str(i))
            if i == self.current_page:
                btn.setStyleSheet("background-color: #1e40af; color: white;")
            btn.clicked.connect(lambda _, x=i: self.go_to_page(x))
            self.pagination_layout.addWidget(btn)

        next_btn = QPushButton("Next ➡")
        next_btn.setEnabled(self.current_page < total_pages)
        next_btn.clicked.connect(self.next_page)
        self.pagination_layout.addWidget(next_btn)

    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.display_data()

    def next_page(self):
        total_pages = (len(self.all_leads) + self.records_per_page - 1) // self.records_per_page
        if self.current_page < total_pages:
            self.current_page += 1
            self.display_data()

    def go_to_page(self, page):
        self.current_page = page
        self.display_data()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CampaignStatistics()
    window.show()
    sys.exit(app.exec())
