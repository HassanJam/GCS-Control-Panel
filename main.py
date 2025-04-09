import sys
import os
import json
from functools import partial
from typing import Dict
from add_server_window import AddServerWindow
from ping3 import ping
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget,
    QTableWidget, QTableWidgetItem, QSizePolicy, QHeaderView, QGridLayout, QStackedWidget, QAbstractScrollArea, QScrollArea
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
        
        self.main_layout.addWidget(self.middle_layout)
    
        
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
        # pixmap = QPixmap(logo_path)
        # self.logo_label.setPixmap(pixmap)
        # self.logo_label.setScaledContents(True)
        # self.logo_label.setFixedSize(80, 50)
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
        
        # server_container = QWidget()
        # server_layout = QHBoxLayout(server_container)
        
        self.add_servers_to_grid()
        
        # self.middle_layout.addWidget(server_container)
        self.setup_logs_section(self.middle_layout)
        
        # self.main_layout.addLayout(self.middle_layout)

    def create_server_section(self, server_name: str):
        layout = QVBoxLayout()
        layout.setSpacing(10)  # Add some spacing between elements

        # Server name label
        label = QLabel(f"{server_name.title()} Server", self)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 18px; font-weight: bold;")
        label.setWordWrap(True)  # Enable word wrapping for long names
        layout.addWidget(label)

        # Status bar
        status_bar = QLabel(self)
        status_bar.setFixedSize(200, 20)  # Increased width to accommodate longer names
        status_bar.setStyleSheet("background-color: red; border: 1px solid black;")
        layout.addWidget(status_bar, alignment=Qt.AlignCenter)

        # Store status bar reference
        self.servers[server_name]["status_bar"] = status_bar

        return layout  # Return the layout for adding to the grid


    def add_servers_to_grid(self):
        """Adds server sections to a grid layout with 3 columns"""
        # Create a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Disable horizontal scrolling
        
        # Create the container widget and grid layout
        grid_container = QWidget()
        grid_layout = QGridLayout(grid_container)
        grid_layout.setSpacing(20)  # Add some spacing between server sections
        
        # Add servers to the grid
        for index, server_name in enumerate(self.servers):
            row = index // 3  # Every 3 servers, move to the next row
            col = index % 3   # 0 for first column, 1 for second column, 2 for third column
            
            server_section = self.create_server_section(server_name)
            grid_layout.addLayout(server_section, row, col)  # Place in grid

        # Set the grid container as the scroll area's widget
        scroll_area.setWidget(grid_container)
        
        # Add the scroll area to the middle layout
        self.middle_layout.addWidget(scroll_area)  # Add to the main layout

    def setup_logs_section(self, parent_layout):
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_label = QLabel("Logs", self)
        log_label.setAlignment(Qt.AlignLeft)
        log_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        log_label.setFixedWidth(150)
        log_layout.addWidget(log_label)

        self.log_table = QTableWidget(self)
        self.log_table.setColumnCount(3)  # Only 3 columns: Time, Status, Message
        self.log_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.log_table.setMinimumSize(600, 300)
        self.log_table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.log_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.log_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.log_table.setWordWrap(True)
        self.log_table.setTextElideMode(Qt.ElideNone)
        self.log_table.setShowGrid(True)
        
        # Set column headers
        self.log_table.setHorizontalHeaderLabels(["Time", "Server Status", "Message"])
        
        # Set column widths
        self.log_table.setColumnWidth(0, 150)  # Time
        self.log_table.setColumnWidth(1, 300)  # Server Status
        self.log_table.setColumnWidth(2, 400)  # Message
        
        # Enable word wrapping for all columns
        self.log_table.setWordWrap(True)
        self.log_table.resizeRowsToContents()

        log_layout.addWidget(self.log_table)
        parent_layout.addWidget(log_container)
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

    def log_event(self, message:str, add_headers:bool=False, status_text:str=None) -> None:
        """Logs the current status of servers to the table and log file.

        :param message: message to log
        :type message: str
        :param status_text: optional status text to display, if None will show all server statuses
        :type status_text: str
        """
        print(message, add_headers)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Update log table
        row_position = self.log_table.rowCount()
        self.log_table.insertRow(row_position)
        
        # Add timestamp
        self.log_table.setItem(row_position, 0, QTableWidgetItem(timestamp))
        
        # Use provided status text or get all server statuses
        if status_text is None:
            status_text = ""
            for server_name in self.servers:
                status = self.get_server_status(server_name)
                status_text += f"{server_name.title()}: {status}\n"
        
        self.log_table.setItem(row_position, 1, QTableWidgetItem(status_text.strip()))
        
        # Add message
        self.log_table.setItem(row_position, 2, QTableWidgetItem(message))

        # Ensure headers are written if they are missing
        log_file_exists = os.path.exists(self.log_file)
        if not log_file_exists or add_headers or os.stat(self.log_file).st_size == 0:
            headers = "Timestamp              | Server Statuses | Message"
            divider = "-" * 100
            
            with open(self.log_file, 'a') as log_file:
                log_file.write(f"{headers}\n{divider}\n")

        # Append the log entry
        log_message = f"{timestamp:<22}| {status_text.strip():<50}| {message}"
        
        with open(self.log_file, 'a') as log_file:
            log_file.write(log_message + "\n")
            
        # Scroll to the latest entry
        self.log_table.scrollToBottom()
        # Select the latest row to highlight it
        self.log_table.selectRow(row_position)

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
                if not self.servers[server_name]["status"]:
                    self.servers[server_name]["status"] = True
                    self.update_status_bar(self.servers[server_name]["status_bar"], "green")
                    status_text = f"{server_name.title()}: Online"
                    self.log_event(f"{server_name.title()} Server became reachable.", status_text=status_text)
            else:  # If response is None, server is unreachable
                if self.servers[server_name]["status"]:  # Status changed to unreachable
                    self.servers[server_name]["status"] = False
                    self.update_status_bar(self.servers[server_name]["status_bar"], "red")
                    status_text = f"{server_name.title()}: Offline"
                    self.log_event(f"{server_name.title()} Server became unreachable.", status_text=status_text)
        except Exception as e:
            self.servers[server_name]["status"] = False
            self.update_status_bar(self.servers[server_name]["status_bar"], "red")
            status_text = f"{server_name.title()}: Offline"
            self.log_event(f"Ping failed for {server_name.title()} Server: {e}", status_text=status_text)
    
    def stop_ping(self, server_name:str) -> None:
        self.servers[server_name]["timer"].stop()
        self.update_status_bar(self.servers[server_name]["status_bar"], "red")
        self.servers[server_name]["status"] = None
        self.log_event(f"{server_name.title()} Server monitoring stopped.")
        
    def get_server_status(self, server_name:str):
        if self.servers[server_name]["status"] is None:
            return "Stopped"
        return "Online" if self.servers[server_name]["status"] else "Offline"
    
    def switch_view(self, index):
        """Switches between Server List and Table"""
        self.middle_layout.setCurrentIndex(index)


def run_app(width=1200, height=600, logo_path="gcs_logo.png"):
    log_file = datetime.now().strftime("gcs_control_panel_log_%Y_%m_%d.txt")
    app = QApplication(sys.argv)
    window = MainWindow(width, height, logo_path, log_file)
    window.show()
    sys.exit(app.exec_())


run_app()
