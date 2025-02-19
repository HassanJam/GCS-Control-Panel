import sys
import os
import json
from functools import partial
from typing import Dict
from add_server_window import AddServerWindow
from ping3 import ping
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget,
    QTableWidget, QTableWidgetItem, QSizePolicy, QHeaderView, QGridLayout
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
    
    # if path does not exist, create it
    if not os.path.exists(JSON_FILE):
        with open(JSON_FILE, "w") as file:
            json.dump({}, file)
                
    with open(JSON_FILE, "r") as file:
        try:
            return json.load(file)  # Return as dictionary
        except json.JSONDecodeError:
            return {}  # Return empty if file is corrupted
    return {}


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
        """)

        self.refresh_servers()
        self.setWindowTitle("GCS SERVER CONTROL PANEL")
        self.setGeometry(100, 100, width, height)
        self.log_file = log_file
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        self.setup_top_section(logo_path)
        self.setup_middle_section()
        # self.setup_timers()
        
        self.add_server_button = QPushButton("Add Server", self)
        self.add_server_button.setStyleSheet("font-size: 14px;")
        self.add_server_button.clicked.connect(self.open_add_server_popup)
        self.main_layout.addWidget(self.add_server_button, alignment=Qt.AlignCenter)
        
    def open_add_server_popup(self):
        self.popup = AddServerWindow()
        self.popup.exec_()
        self.stop_all_timers()
        self.refresh_servers()
        self.log_event(message="Added a new server", add_headers=True)
        self.refresh_middle_section()
        
    def refresh_servers(self):
        """reads servers and creates timers for them
        """
        
        self.servers = get_servers()
        
        for server_name in self.servers:
            self.servers[server_name]["status"] = False
        
        self.setup_timers()
        
    def stop_all_timers(self):
        """stops all timers of the servers"""
        for server_name in self.servers:
            self.stop_ping(server_name=server_name)
    
    def refresh_middle_section(self):
        """Removes the middle layout and rebuilds it to reflect added servers."""
        print("Refreshing middle section...")

        # Check if middle_layout exists and remove it from main_layout
        if self.middle_layout:
            while self.middle_layout.count():
                item = self.middle_layout.takeAt(0)
                if item.widget():
                    item.widget().setParent(None)
                elif item.layout():
                    self.clear_layout(item.layout())  # Recursively clear sub-layouts

            self.main_layout.removeItem(self.middle_layout)  # Removes it from main_layout
            self.middle_layout.deleteLater()  # Marks it for deletion

        # Recreate the middle layout
        self.setup_middle_section()

        print("Middle section refreshed successfully!")

    def clear_layout(self, layout):
        """Recursively clears a given layout."""
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
        self.middle_layout = QHBoxLayout()
        server_layout = QHBoxLayout()
        
        self.add_servers_to_grid()
        
        self.middle_layout.addLayout(server_layout)
        self.setup_logs_section(self.middle_layout)
        self.main_layout.addLayout(self.middle_layout)

    def create_server_section(self, server_name: str):
        layout = QVBoxLayout()

        # Server name label
        label = QLabel(f"{server_name.title()} Server", self)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 18px; font-weight: bold;")
        label.setFixedWidth(150)
        layout.addWidget(label)

        # Status bar
        status_bar = QLabel(self)
        status_bar.setFixedSize(150, 20)
        status_bar.setStyleSheet("background-color: red; border: 1px solid black;")
        layout.addWidget(status_bar, alignment=Qt.AlignCenter)

        # Shutdown button
        shutdown_button = QPushButton("Shutdown", self)
        shutdown_button.setStyleSheet("font-size: 14px;")
        shutdown_button.clicked.connect(partial(self.stop_ping, server_name=server_name))
        layout.addWidget(shutdown_button, alignment=Qt.AlignCenter)

        # Add stretch for spacing
        layout.addStretch()

        # Store status bar reference
        self.servers[server_name]["status_bar"] = status_bar

        return layout  # Return the layout for adding to the grid


    def add_servers_to_grid(self):
        """Adds server sections to a grid layout with 2 columns"""
        grid_layout = QGridLayout()
        
        for index, server_name in enumerate(self.servers):
            row = index // 2  # Every 2 servers, move to the next row
            col = index % 2   # 0 for first column, 1 for second column
            
            server_section = self.create_server_section(server_name)
            grid_layout.addLayout(server_section, row, col)  # Place in grid

        self.middle_layout.addLayout(grid_layout)  # Add to the main layout

    def setup_logs_section(self, parent_layout):
        log_layout = QVBoxLayout()
        log_label = QLabel("Logs", self)
        log_label.setAlignment(Qt.AlignLeft)
        log_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        log_label.setFixedWidth(150)
        log_layout.addWidget(log_label)

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
        
        # Set the width for each column
        self.log_table.setColumnWidth(0, 100)  # Date (reduced width to 100px)
        
        for i in range(len(self.servers)):
            print(i+1)
            self.log_table.setColumnWidth(i+1, 100)
        print(i+2)
        self.log_table.setColumnWidth(i+1, 250)  # Message (unchanged width)

        # Enable word wrapping for the message column
        self.log_table.setWordWrap(True)

        # Set size policy for row height to allow wrapping
        self.log_table.setRowHeight(0, 40)  # Set an initial height; this may need to be adjusted

        # Make sure the row height adjusts automatically for word wrapping
        self.log_table.resizeRowsToContents()

        log_layout.addWidget(self.log_table)
        parent_layout.addLayout(log_layout)
        self.log_event("Log Section Initialized.")

    def setup_timers(self):
        """sets up timers for each server
        """
        for server_name in self.servers:
            print(f"creating timer for {server_name}")
            server_ip = self.servers[server_name]["ip"]
            self.servers[server_name]["timer"] = QTimer(self)
            self.servers[server_name]["timer"].timeout.connect(partial(self.ping_server, server_name=server_name, server_ip=server_ip))
            self.servers[server_name]["timer"].start(5000)

    def log_event(self, message:str, add_headers:bool=False) -> None:
        """Logs the current status of both servers to the table and log file.

        :param message: message to log
        :type message: str
        """
        print(message, add_headers)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Update log table
        row_position = self.log_table.rowCount()
        self.log_table.insertRow(row_position)
        self.log_table.setItem(row_position, 0, QTableWidgetItem(timestamp))
        
        current_row = 1
        for server_name in self.servers:
            print(f"{server_name} Server is currently {self.get_server_status(server_name)}")
            self.log_table.setItem(row_position, current_row, QTableWidgetItem(self.get_server_status(server_name)))
            current_row += 1
            
        self.log_table.setItem(row_position, current_row, QTableWidgetItem(message))

        # Ensure headers are written if they are missing
        log_file_exists = os.path.exists(self.log_file)
        if not log_file_exists or add_headers or os.stat(self.log_file).st_size == 0:
            headers = "Timestamp              "
            for server_name in self.servers:
                headers += f"| {server_name.title()} Server   "
            headers += "| Message"
            
            divider = "-" * 70
            
            with open(self.log_file, 'a') as log_file:
                log_file.write(f"{headers}\n{divider}\n")  # Write headers with divider

        # Append the log entry
        log_message = f"{timestamp:<22}"
        
        for server_name in self.servers:
            log_message += f"| {self.get_server_status(server_name):<13}"
        log_message += f"| {message}"
        
        with open(self.log_file, 'a') as log_file:
            log_file.write(log_message + "\n")

    def update_status_bar(self, status_bar, color:str):
        """updates status bar to correct color

        :param status_bar: status bar object
        :type status_bar: status bar object
        :param color: color of bar, green or red
        :type color: str
        """
        status_bar.setStyleSheet(f"background-color: {color}; border: 1px solid black;")
        
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
                self.update_status_bar(self.servers[server_name]["status_bar"], "green")
                if not self.servers[server_name]["status"]:
                    self.servers[server_name]["status"] = True
                    self.log_event(f"{server_name.title()} Server became reachable.")
            else:  # If response is None, server is unreachable
                self.update_status_bar(self.servers[server_name]["status_bar"], "red")
                if self.servers[server_name]["status"]:  # Status changed to unreachable
                    self.voice_server_status = False
                    self.log_event(f"{server_name.title()} Server became unreachable.")
        except Exception as e:
            self.update_status_bar(self.servers[server_name]["status_bar"], "red")
            self.log_event(f"Ping failed for {server_name.title()} Server: {e}")
    
    def stop_ping(self, server_name:str) -> None:
        self.servers[server_name]["timer"].stop()
        self.update_status_bar(self.servers[server_name]["status_bar"], "red")
        self.servers[server_name]["status"] = None
        self.log_event(f"{server_name.title()} Server monitoring stopped.")
        
    def get_server_status(self, server_name:str):
        if self.servers[server_name]["status"] is None:
            return "Stopped"
        return "Online" if self.servers[server_name]["status"] else "Offline"


def run_app(width=1200, height=600, logo_path="gcs_logo.png"):
    log_file = datetime.now().strftime("gcs_control_panel_log_%Y_%m_%d.txt")
    app = QApplication(sys.argv)
    window = MainWindow(width, height, logo_path, log_file)
    window.show()
    sys.exit(app.exec_())


run_app()
