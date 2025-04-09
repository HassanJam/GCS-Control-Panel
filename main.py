import sys
import os
import json
from functools import partial
from typing import Dict
from datetime import datetime

from add_server_window import AddServerWindow
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget,
    QTableWidget, QTableWidgetItem, QSizePolicy, QHeaderView, QGridLayout, QTabWidget
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
            QHeaderView::section {
                background-color: #444;
                color: white;
                padding: 4px;
                font-weight: bold;
            }
            /* Style for QTabWidget and QTabBar */
            QTabWidget::pane {
                border: 1px solid #444;
                top: -1px;
            }
            QTabBar::tab {
                background: #444;
                color: #ffffff;
                padding: 10px;
                border: 1px solid #444;
                border-bottom: none;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background: #0078d7;
                color: #ffffff;
                border-bottom: 1px solid #0078d7;
            }
            QTabBar::tab:hover {
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

        # Add Server button (preserved functionality)
        self.add_server_button = QPushButton("Add Server", self)
        self.add_server_button.setStyleSheet("font-size: 14px;")
        self.add_server_button.clicked.connect(self.open_add_server_popup)
        self.main_layout.addWidget(self.add_server_button, alignment=Qt.AlignCenter)

        # Timer to schedule ping tasks for all servers.
        self.ping_timer = QTimer(self)
        self.ping_timer.setInterval(5000)  # 5-second interval
        self.ping_timer.timeout.connect(self.ping_all_servers)
        self.ping_timer.start()

        # Create signal emitter and global thread pool.
        self.ping_emitter = PingSignalEmitter()
        self.ping_emitter.result_signal.connect(self.handle_ping_result)
        self.thread_pool = QThreadPool.globalInstance()

    def open_add_server_popup(self):
        # Open the add server dialog.
        popup = AddServerWindow()
        if popup.exec_():
            # After the popup closes, refresh servers from file.
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
            # Clear servers tab layout
            self.clear_layout(self.servers_layout)
            self.add_servers_to_grid()
            # Clear logs tab layout and reinitialize log table.
            self.clear_layout(self.logs_layout)
            self.setup_logs_section(self.logs_layout)

    def closeEvent(self, event):
        self.ping_timer.stop()
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
        pixmap = QPixmap(logo_path)
        self.logo_label.setPixmap(pixmap)
        self.logo_label.setScaledContents(True)
        self.logo_label.setFixedSize(80, 50)
        self.title_label = QLabel("GCS CONTROL PANEL", self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        top_layout.addWidget(self.logo_label)
        top_layout.addStretch()
        top_layout.addWidget(self.title_label)
        top_layout.addStretch()
        self.main_layout.addLayout(top_layout)

    def setup_middle_section(self):
        # Create a tab widget with two tabs: Servers and Logs
        self.tabs = QTabWidget()
        self.servers_tab = QWidget()
        self.logs_tab = QWidget()
        self.tabs.addTab(self.servers_tab, "Servers")
        self.tabs.addTab(self.logs_tab, "Logs")
        
        # Layout for the Servers tab
        self.servers_layout = QVBoxLayout(self.servers_tab)
        self.add_servers_to_grid()
        
        # Layout for the Logs tab
        self.logs_layout = QVBoxLayout(self.logs_tab)
        self.setup_logs_section(self.logs_layout)
        
        self.main_layout.addWidget(self.tabs)

    def create_server_section(self, server_name: str):
        layout = QVBoxLayout()
        label = QLabel(f"{server_name.title()} Server", self)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 18px; font-weight: bold;")
        label.setFixedWidth(150)
        layout.addWidget(label)

        status_bar = QLabel(self)
        status_bar.setFixedSize(150, 20)
        status_bar.setStyleSheet("background-color: red; border: 1px solid black;")
        layout.addWidget(status_bar, alignment=Qt.AlignCenter)

        shutdown_button = QPushButton("Shutdown", self)
        shutdown_button.setStyleSheet("font-size: 14px;")
        shutdown_button.clicked.connect(partial(self.stop_ping, server_name=server_name))
        layout.addWidget(shutdown_button, alignment=Qt.AlignCenter)
        layout.addStretch()
        self.servers[server_name]["status_bar"] = status_bar
        return layout

    def add_servers_to_grid(self):
        grid_layout = QGridLayout()
        for index, server_name in enumerate(self.servers):
            row = index // 2
            col = index % 2
            server_section = self.create_server_section(server_name)
            grid_layout.addLayout(server_section, row, col)
        self.servers_layout.addLayout(grid_layout)

    def setup_logs_section(self, parent_layout):
        log_label = QLabel("Logs", self)
        log_label.setAlignment(Qt.AlignLeft)
        log_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        log_label.setFixedWidth(150)
        parent_layout.addWidget(log_label)

        self.log_table = QTableWidget(self)
        self.log_table.setColumnCount(len(self.servers) + 2)
        header_labels = ["Date"]
        for server_name in self.servers:
            header_labels.append(f"{server_name.title()} Server")
        header_labels.append("Message")
        self.log_table.setHorizontalHeaderLabels(header_labels)
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.log_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.log_table.setStyleSheet("font-size: 12px;")
        self.log_table.setColumnWidth(0, 100)
        for i in range(len(self.servers)):
            self.log_table.setColumnWidth(i+1, 100)
        self.log_table.setColumnWidth(len(self.servers)+1, 250)
        self.log_table.setWordWrap(True)
        self.log_table.setRowHeight(0, 40)
        self.log_table.resizeRowsToContents()
        parent_layout.addWidget(self.log_table)
        self.log_event("Log Section Initialized.")

    def ping_all_servers(self):
        """Schedules a ping task for each server concurrently."""
        for server_name, server_data in self.servers.items():
            # Skip pinging if server has been stopped.
            if server_data.get("status") is None:
                continue
            server_ip = server_data["ip"]
            task = PingTask(server_name, server_ip, self.ping_emitter)
            self.thread_pool.start(task)

    def handle_ping_result(self, server_name, result):
        """Updates UI based on ping result."""
        if result:
            self.update_status_bar(self.servers[server_name]["status_bar"], "green")
            if not self.servers[server_name].get("status", False):
                self.servers[server_name]["status"] = True
                self.log_event(f"{server_name.title()} Server became reachable.")
        else:
            self.update_status_bar(self.servers[server_name]["status_bar"], "red")
            if self.servers[server_name].get("status", False):
                self.servers[server_name]["status"] = False
                self.log_event(f"{server_name.title()} Server became unreachable.")

    def log_event(self, message: str, add_headers: bool = False) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row_position = self.log_table.rowCount()
        self.log_table.insertRow(row_position)
        self.log_table.setItem(row_position, 0, QTableWidgetItem(timestamp))
        current_row = 1
        for server_name in self.servers:
            self.log_table.setItem(row_position, current_row, QTableWidgetItem(self.get_server_status(server_name)))
            current_row += 1
        self.log_table.setItem(row_position, current_row, QTableWidgetItem(message))
        log_file_exists = os.path.exists(self.log_file)
        if not log_file_exists or add_headers or os.stat(self.log_file).st_size == 0:
            headers = "Timestamp              "
            for server_name in self.servers:
                headers += f"| {server_name.title()} Server   "
            headers += "| Message"
            divider = "-" * 70
            with open(self.log_file, 'a') as log_file:
                log_file.write(f"{headers}\n{divider}\n")
        log_message = f"{timestamp:<22}"
        for server_name in self.servers:
            log_message += f"| {self.get_server_status(server_name):<13}"
        log_message += f"| {message}"
        with open(self.log_file, 'a') as log_file:
            log_file.write(log_message + "\n")

    def update_status_bar(self, status_bar, color: str):
        status_bar.setStyleSheet(f"background-color: {color}; border: 1px solid black;")

    def stop_ping(self, server_name: str) -> None:
        """Stops pinging for a given server by setting its status to None."""
        if server_name in self.servers:
            self.update_status_bar(self.servers[server_name]["status_bar"], "red")
            self.servers[server_name]["status"] = None
            self.log_event(f"{server_name.title()} Server monitoring stopped.")

    def get_server_status(self, server_name: str):
        if self.servers[server_name]["status"] is None:
            return "Stopped"
        return "Online" if self.servers[server_name]["status"] else "Offline"

def run_app(width=1200, height=600, logo_path="gcs_logo.png"):
    log_file = datetime.now().strftime("gcs_control_panel_log_%Y_%m_%d.txt")
    app = QApplication(sys.argv)
    window = MainWindow(width, height, logo_path, log_file)
    window.setWindowTitle("GCS SERVER CONTROL PANEL")
    window.setGeometry(100, 100, width, height)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_app()
