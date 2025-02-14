import sys
import os
import json
from typing import Dict
from add_server_window import AddServerWindow
from ping3 import ping
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QFrame, QVBoxLayout, QHBoxLayout, QWidget,
    QTableWidget, QTableWidgetItem, QSizePolicy, QHeaderView
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
from datetime import datetime

from ping3 import ping

JSON_FILE = "servers.json"

def get_servers() -> Dict:
    """reads the server names and ips from the json file in JSON_FILE

    :return: a dictionary where the key is the server name, and it points to a dictionary where the key 'ip' points to
    the ip address of the server
    :rtype: Dictionary
    """
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r") as file:
            try:
                return json.load(file)  # Return as dictionary
            except json.JSONDecodeError:
                return {}  # Return empty if file is corrupted
    return {}


class MainWindow(QMainWindow):
    def __init__(self, width, height, logo_path, log_file):
        super().__init__()
        self.servers = get_servers()
        
        for server_name in self.servers:
            self.servers[server_name]["status"] = False
        
        self.setWindowTitle("GCS CONTROL PANEL")
        self.setGeometry(100, 100, width, height)
        self.log_file = log_file
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        self.setup_top_section(logo_path)
        self.setup_middle_section()
        self.setup_timers()
        
        self.add_server_button = QPushButton("Add Server", self)
        self.add_server_button.setStyleSheet("font-size: 14px;")
        self.add_server_button.clicked.connect(self.open_add_server_popup)
        self.main_layout.addWidget(self.add_server_button, alignment=Qt.AlignCenter)
        
    def open_add_server_popup(self):
        self.popup = AddServerWindow()
        self.popup.exec_()

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
        middle_layout = QHBoxLayout()
        server_layout = QHBoxLayout()
        
        for server_name in self.servers:
            self.servers[server_name]["server_section"] = self.create_server_section(server_name=server_name)
            server_layout.addLayout(self.servers[server_name]["server_section"])
        
        middle_layout.addLayout(server_layout)
        self.setup_logs_section(middle_layout)
        self.main_layout.addLayout(middle_layout)

    def create_server_section(self, server_name:str):
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
        shutdown_button.clicked.connect(lambda: self.stop_ping(server_name))
        layout.addWidget(shutdown_button, alignment=Qt.AlignCenter)
        layout.addStretch()
        self.servers[server_name]["status_bar"] = status_bar
        # if server_name == "Voice Server":
        #     self.voice_status_bar = status_bar
        # elif server_name == "Window Server":
        #     self.window_status_bar = status_bar
        vertical_line = QFrame(self)
        vertical_line.setFrameShape(QFrame.VLine)
        vertical_line.setFrameShadow(QFrame.Sunken)
        vertical_line.setStyleSheet("background-color: black;")
        vertical_line.setFixedWidth(2)
        layout.addWidget(vertical_line, alignment=Qt.AlignCenter)
        return layout

    def setup_logs_section(self, parent_layout):
        log_layout = QVBoxLayout()
        log_label = QLabel("Logs", self)
        log_label.setAlignment(Qt.AlignLeft)
        log_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        log_label.setFixedWidth(150)
        log_layout.addWidget(log_label)

        self.log_table = QTableWidget(self)
        self.log_table.setColumnCount(4)
        self.log_table.setHorizontalHeaderLabels(["Date", "Voice Server", "Window Server", "Message"])
        self.log_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.log_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.log_table.setStyleSheet("font-size: 12px;")
        
        # Set the width for each column
        self.log_table.setColumnWidth(0, 100)  # Date (reduced width to 100px)
        self.log_table.setColumnWidth(1, 100)  # Voice Server (reduced width to 100px)
        self.log_table.setColumnWidth(2, 100)  # Window Server (reduced width to 100px)
        self.log_table.setColumnWidth(3, 250)  # Message (unchanged width)

        # Enable word wrapping for the message column
        self.log_table.setWordWrap(True)

        # Set size policy for row height to allow wrapping
        self.log_table.setRowHeight(0, 40)  # Set an initial height; this may need to be adjusted

        # Make sure the row height adjusts automatically for word wrapping
        self.log_table.resizeRowsToContents()

        log_layout.addWidget(self.log_table)
        parent_layout.addLayout(log_layout)
        self.log_event("N/A", "N/A", "Log Section Initialized.")

    def setup_timers(self):
        for server_name in self.servers:
            print(server_name)
            server_ip = self.servers[server_name]["ip"]
            self.servers[server_name]["timer"] = QTimer(self)
            self.servers[server_name]["timer"].timeout.connect(lambda: self.ping_server(server_name=server_name, server_ip=server_ip))
            self.servers[server_name]["timer"].start(5000)

    def log_event(self, voice_status, window_status, message):
        """Logs the current status of both servers to the table and log file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        headers = "Timestamp              | Voice Server   | Window Server  | Message"
        divider = "-" * 70

        # Update log table
        row_position = self.log_table.rowCount()
        self.log_table.insertRow(row_position)
        self.log_table.setItem(row_position, 0, QTableWidgetItem(timestamp))
        self.log_table.setItem(row_position, 1, QTableWidgetItem(voice_status))
        self.log_table.setItem(row_position, 2, QTableWidgetItem(window_status))
        self.log_table.setItem(row_position, 3, QTableWidgetItem(message))

        # Ensure headers are written if they are missing
        log_file_exists = os.path.exists(self.log_file)
        if not log_file_exists or os.stat(self.log_file).st_size == 0:
            with open(self.log_file, 'w') as log_file:
                log_file.write(f"{headers}\n{divider}\n")  # Write headers with divider

        # Append the log entry
        log_message = f"{timestamp:<22}| {voice_status:<13}| {window_status:<14}| {message}"
        with open(self.log_file, 'a') as log_file:
            log_file.write(log_message + "\n")

    def update_status_bar(self, status_bar, status):
        status_bar.setStyleSheet(f"background-color: {status}; border: 1px solid black;")
        
    def ping_server(self, server_name:str, server_ip:str) -> None:
        """pings the given ip address and updates the status and status bar for the server

        :param name: name of server
        :type name: str
        :param ip: ip address of server
        :type ip: str
        """
        
        print(f"pinging {server_name} with ip {server_ip}")
        try:
            response = ping(server_ip, timeout=2)  # Timeout set to 2 seconds
            if response is not None:  # If response is a valid number, the server is reachable
                # if not self.voice_server_status:  Status changed to reachable
                if not self.servers[server_name]["status"]:
                    self.log_event("Online", self.get_current_server_status(name=server_name), f"{server_name.title()} Server became reachable.")
                    self.servers[server_name]["status"] = True
                    self.update_status_bar(self.servers[server_name]["status_bar"], "green")
            else:  # If response is None, server is unreachable
                if self.servers[server_name]["status"]:  # Status changed to unreachable
                    self.log_event("Offline", self.get_current_server_status(name=server_name), f"{server_name.title()} Server became unreachable.")
                    self.voice_server_status = False
                    self.update_status_bar(self.servers[server_name]["status_bar"], "red")
        except Exception as e:
            self.update_status_bar(self.servers[server_name]["status_bar"], "red")
            self.log_event("Offline", self.get_current_server_status(name=server_name), f"Ping failed for {server_name.title()} Server: {e}")
    
    def stop_ping(self, name:str) -> None:
        self.servers[name]["timer"].stop()
        self.update_status_bar(self.servers[name]["status_bar"], "red")
        self.log_event("Stopped", "N/A", "Voice Server monitoring stopped.")
        
    def get_current_server_status(self, name:str):
        return "Online" if self.servers[name]["status"] else "Offline"


def run_app(width=1200, height=600, logo_path="gcs_logo.png"):
    log_file = datetime.now().strftime("gcs_control_panel_log_%Y_%m_%d.txt")
    app = QApplication(sys.argv)
    window = MainWindow(width, height, logo_path, log_file)
    window.show()
    sys.exit(app.exec_())



run_app()