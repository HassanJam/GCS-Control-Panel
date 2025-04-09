import sys
import os
import json
from functools import partial
from typing import Dict
from datetime import datetime

from add_server_window import AddServerWindow
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget,
    QTableWidget, QTableWidgetItem, QSizePolicy, QHeaderView, QGridLayout, QStackedWidget, QAbstractScrollArea, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer, QRunnable, QThreadPool, pyqtSignal, QObject
from PyQt5.QtGui import QPixmap
from ping3 import ping

JSON_FILE = "servers.json"

def get_servers() -> Dict:
    """Reads the server names and ips from the JSON_FILE."""
    if not os.path.exists(JSON_FILE):
        with open(JSON_FILE, "w") as file:
            json.dump({}, file)
    with open(JSON_FILE, "r") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return {}
    return {}

# Signal emitter for ping results
class PingSignalEmitter(QObject):
    result_signal = pyqtSignal(str, bool)

# A runnable that pings a server without blocking the UI.
class PingTask(QRunnable):
    def __init__(self, server_name: str, server_ip: str, emitter: PingSignalEmitter):
        super().__init__()
        self.server_name = server_name
        self.server_ip = server_ip
        self.emitter = emitter

    def run(self):
        try:
            response = ping(self.server_ip, timeout=2)
            success = isinstance(response, float)
        except Exception:
            success = False
        self.emitter.result_signal.emit(self.server_name, success)

class MainWindow(QMainWindow):
    def __init__(self, width, height, logo_path, log_file):
        super().__init__()
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                font-size: 14px;
            }
            QLabel {
                font-weight: bold;
                color: #dcdcdc;
            }
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 8px;
                border-radius: 8px;
                background-color: #0078d7;
                color: white;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004080;
            }
            QTableWidget {
                background-color: #1e1e1e;
                border: 1px solid #444;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QHeaderView::section {
                background-color: #444;
                color: white;
                padding: 4px;
                font-weight: bold;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: #333;
                border: none;
                width: 10px;
                height: 10px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: #0078d7;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
                background: #005a9e;
            }
        """)

        self.log_file = log_file
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        
        self.setup_top_section(logo_path)

        self.refresh_servers()
        self.setup_middle_section()

        self.add_server_button = QPushButton("Add Server", self)
        self.add_server_button.setStyleSheet("font-size: 14px;")
        self.add_server_button.clicked.connect(self.open_add_server_popup)
        self.main_layout.addWidget(self.add_server_button, alignment=Qt.AlignCenter)
        
        self.main_layout.addWidget(self.middle_layout)

    def open_add_server_popup(self):
        popup = AddServerWindow()
        if popup.exec_():
            self.refresh_servers()
            self.log_event("Added a new server", add_headers=True)
            self.refresh_middle_section()

    def refresh_servers(self):
        """Reads servers from file and resets their status."""
        self.servers = get_servers()
        for server_name in self.servers:
            self.servers[server_name]["status"] = False

    def refresh_middle_section(self):
        """Rebuilds the tabs to reflect added servers."""
        if hasattr(self, "tabs"):
            self.clear_layout(self.servers_layout)
            self.add_servers_to_grid()
            self.clear_layout(self.logs_layout)
            self.setup_logs_section(self.logs_layout)

    def closeEvent(self, event):
        event.accept()

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    def setup_top_section(self, logo_path):
        top_layout = QHBoxLayout()
        self.logo_label = QLabel(self)
        self.title_label = QLabel("GCS CONTROL PANEL", self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.btn_show_servers = QPushButton("Show Servers")
        self.btn_show_table = QPushButton("Show Table")
        self.btn_show_servers.clicked.connect(lambda: self.switch_view(0))
        self.btn_show_table.clicked.connect(lambda: self.switch_view(1))
        
        top_layout.addWidget(self.logo_label)
        top_layout.addStretch()
        top_layout.addWidget(self.title_label)
        top_layout.addStretch()
        top_layout.addWidget(self.btn_show_servers)
        top_layout.addStretch()
        top_layout.addWidget(self.btn_show_table)
        top_layout.addStretch()
        
        self.main_layout.addLayout(top_layout)

    def setup_middle_section(self):
        self.middle_layout = QStackedWidget()
        self.servers_layout = QVBoxLayout()
        self.add_servers_to_grid()
        self.setup_logs_section(self.middle_layout)

    def create_server_section(self, server_name: str):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        label = QLabel(f"{server_name.title()} Server", self)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 18px; font-weight: bold;")
        label.setWordWrap(True)
        layout.addWidget(label)

        status_bar = QLabel(self)
        status_bar.setFixedSize(200, 20)
        status_bar.setStyleSheet("background-color: red; border: 1px solid black;")
        layout.addWidget(status_bar, alignment=Qt.AlignCenter)

        self.servers[server_name]["status_bar"] = status_bar
        return layout

    def add_servers_to_grid(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        grid_container = QWidget()
        grid_layout = QGridLayout(grid_container)
        grid_layout.setSpacing(20)
        
        for index, server_name in enumerate(self.servers):
            row = index // 3
            col = index % 3
            server_section = self.create_server_section(server_name)
            grid_layout.addLayout(server_section, row, col)

        scroll_area.setWidget(grid_container)
        self.middle_layout.addWidget(scroll_area)

    def setup_logs_section(self, parent_layout):
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_label = QLabel("Logs", self)
        log_label.setAlignment(Qt.AlignLeft)
        log_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        log_label.setFixedWidth(150)
        log_layout.addWidget(log_label)
        parent_layout.addWidget(log_container)
