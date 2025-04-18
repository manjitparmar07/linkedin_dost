import os
import json
import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPixmap, QDesktopServices, QPainter, QPainterPath
from PyQt6.QtCore import Qt, QUrl


class CampaignScrapList(QMainWindow):
    def __init__(self):
        super().__init__()

        # self.setWindowTitle("LinkedIn Campaign Scrap List")
        # self.setGeometry(100, 100, 1000, 700)
        #self.showMaximized()
  
        self.current_page = 1
        self.records_per_page = 10
        self.all_leads = []

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

         # Reload Button
        reload_button = QPushButton("🔄 Reload")
        reload_button.clicked.connect(self.refresh_data)
        reload_button.setFixedWidth(100)
        reload_button.setStyleSheet("background-color: #0077b5; color: white;")
        main_layout.addWidget(reload_button, alignment=Qt.AlignmentFlag.AlignRight)

        # List Container
        self.list_container = QVBoxLayout()
        self.list_widget = QWidget()
        self.list_widget.setLayout(self.list_container)
        main_layout.addWidget(self.list_widget)

        # Pagination Bar
        self.pagination_layout = QHBoxLayout()
        self.pagination_layout.setSpacing(8)
        self.pagination_layout.setContentsMargins(0, 10, 0, 0)

        self.prev_button = QPushButton("⬅ Previous")
        self.prev_button.clicked.connect(self.show_previous_page)
        self.pagination_layout.addWidget(self.prev_button)

        self.page_buttons_container = QHBoxLayout()
        self.pagination_layout.addLayout(self.page_buttons_container)

        self.next_button = QPushButton("Next ➡")
        self.next_button.clicked.connect(self.show_next_page)
        self.pagination_layout.addWidget(self.next_button)

        main_layout.addLayout(self.pagination_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.load_queue_data_into_table()
        self.apply_styles()

    def apply_styles(self):
        self.setStyleSheet("""
            QLabel { font-size: 14px; }
            QPushButton { padding: 6px 12px; font-size: 13px; }
        """)

    def refresh_data(self):
        print("Refreshing data from queue.json...")
        self.load_queue_data_into_table()

        
    def load_queue_data_into_table(self):
        print("data load in queue data")
        self.all_leads = []

        if not os.path.exists("queue.json"):
            self.log_status("queue.json not found.")
            self.update_list_ui()  # Show empty in UI
            return

        with open("queue.json", "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
                if not data:
                    self.log_status("queue.json is empty.")
                    self.update_list_ui()  # Show empty in UI
                    return
                self.all_leads = data
            except json.JSONDecodeError:
                self.log_status("queue.json is invalid or corrupted.")
                self.update_list_ui()  # Show empty in UI
                return

        self.current_page = 1
        self.update_list_ui()


    def make_list_item(self, lead, index):
        item_widget = QWidget()
        item_layout = QHBoxLayout()
        item_layout.setContentsMargins(5, 5, 5, 5)
        item_layout.setSpacing(10)

        index_label = QLabel(f"{index}")
        index_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        index_label.setFixedWidth(50)

        image_label = QLabel()
        image_label.setFixedSize(45, 45)

        image_url = lead.get("imageUrl", "")
        if image_url.startswith("http"):
            self.load_image_async(image_url, image_label)
        else:
            pixmap = QPixmap(45, 45)
            pixmap.fill(Qt.GlobalColor.lightGray)
            image_label.setPixmap(self.circular_pixmap(pixmap))

        name_label = QLabel(lead.get('name', 'Unknown'))
        name_label.setFixedWidth(250)

        title_label = QLabel(lead.get('title', 'No Title'))
        title_label.setFixedWidth(700)

        location_label = QLabel(lead.get('location', 'Location not specified'))
        location_label.setFixedWidth(250)

        profile_link = lead.get("link", "#")
        link_button = QPushButton("View Profile")
        link_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(profile_link)))
        link_button.setFixedWidth(100)

        item_layout.addWidget(index_label)
        item_layout.addWidget(image_label)
        item_layout.addWidget(name_label)
        item_layout.addWidget(title_label)
        item_layout.addWidget(location_label)
        item_layout.addStretch()
        item_layout.addWidget(link_button)

        item_widget.setLayout(item_layout)
        item_widget.setStyleSheet("""
            QWidget { 
                background-color: white; 
                border-bottom: 1px solid #e0e0e0;
            }
        """)

        return item_widget

    def load_image_async(self, url, label):
        cache_dir = "profile_images"
        os.makedirs(cache_dir, exist_ok=True)
        filename = os.path.join(cache_dir, os.path.basename(url.split("?")[0]))

        if os.path.exists(filename):
            self.set_circular_image(filename, label)
            return

        from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
        self.network_manager = getattr(self, 'network_manager', QNetworkAccessManager(self))

        request = QNetworkRequest(QUrl(url))
        reply = self.network_manager.get(request)

        def handle_download():
            if reply.error() == reply.NetworkError.NoError:
                with open(filename, "wb") as file:
                    file.write(reply.readAll())
                self.set_circular_image(filename, label)
            else:
                label.setPixmap(self.circular_pixmap(QPixmap(45, 45)))
            reply.deleteLater()

        reply.finished.connect(handle_download)

    def set_circular_image(self, filepath, label):
        pixmap = QPixmap(filepath).scaled(45, 45, Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation)
        label.setPixmap(self.circular_pixmap(pixmap))

    def circular_pixmap(self, pixmap):
        size = 45
        circular = QPixmap(size, size)
        circular.fill(Qt.GlobalColor.transparent)

        painter = QPainter(circular)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        return circular

    def update_list_ui(self):
        while self.list_container.count():
            item = self.list_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        start = (self.current_page - 1) * self.records_per_page
        for i, lead in enumerate(self.all_leads[start:start + self.records_per_page]):
            self.list_container.addWidget(self.make_list_item(lead, start + i + 1))

        self.update_pagination()

    def update_pagination(self):
        while self.page_buttons_container.count():
            item = self.page_buttons_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        total_pages = (len(self.all_leads) + self.records_per_page - 1) // self.records_per_page

        # If 10 or fewer pages, show all page numbers
        if total_pages <= 10:
            pages_to_show = range(1, total_pages + 1)
        else:
            pages_to_show = set()

            # Always show first 2 pages, last 2 pages
            pages_to_show.update({1, 2, total_pages - 1, total_pages})

            # Show 2 pages before and after current page
            pages_to_show.update({self.current_page - 1, self.current_page, self.current_page + 1})

            # Filter only valid pages
            pages_to_show = {p for p in pages_to_show if 1 <= p <= total_pages}

            # Sort for layout order
            pages_to_show = sorted(pages_to_show)

        last_page_shown = 0

        for page_number in pages_to_show:
            if page_number - last_page_shown > 1:
                # Insert ellipsis if there's a gap
                ellipsis = QLabel("...")
                ellipsis.setStyleSheet("font-size: 14px; color: #555; padding: 0 5px;")
                self.page_buttons_container.addWidget(ellipsis)

            page_button = QPushButton(str(page_number))
            page_button.setFixedSize(40, 35)

            if page_number == self.current_page:
                page_button.setStyleSheet("background-color: #0077b5; color: white; font-weight: bold;")
            else:
                page_button.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ccc;")

            page_button.clicked.connect(lambda _, p=page_number: self.go_to_page(p))
            self.page_buttons_container.addWidget(page_button)

            last_page_shown = page_number

        self.prev_button.setEnabled(self.current_page > 1)
        self.next_button.setEnabled(self.current_page < total_pages)

    def go_to_page(self, page_number):
        self.current_page = page_number
        self.update_list_ui()

    def show_previous_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.update_list_ui()

    def show_next_page(self):
        total_pages = (len(self.all_leads) + self.records_per_page - 1) // self.records_per_page
        if self.current_page < total_pages:
            self.current_page += 1
            self.update_list_ui()

    def log_status(self, msg):
        print(f"[STATUS] {msg}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CampaignScrapList()
    window.show()
    sys.exit(app.exec())
