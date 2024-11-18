import sys
import os
from ping3 import ping
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QFrame, QTextEdit, QVBoxLayout, QHBoxLayout, QWidget
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
from datetime import datetime
from PyQt5.QtWidgets import QSizePolicy


class MainWindow(QMainWindow):
    def __init__(self, width, height, voice_ip_to_ping, window_ip_to_ping, logo_path, log_file):
        super().__init__()
        self.setWindowTitle("GCS CONTROL PANEL")
        self.setGeometry(100, 100, width, height)  # Adjust the width and height here

        # Track server states
        self.voice_server_status = False
        self.window_server_status = False

        # Log file
        self.log_file = log_file

        # Main Layout
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        # Top Section: Logo + Title
        self.setup_top_section(logo_path)

        # Middle Section: Server Statuses and Logs
        self.setup_middle_section()

        # Timers
        self.voice_ip_to_ping = voice_ip_to_ping
        self.window_ip_to_ping = window_ip_to_ping
        self.setup_timers()

    def setup_top_section(self, logo_path):
        """Setup the top section with logo and title."""
        top_layout = QHBoxLayout()

        # Logo
        self.logo_label = QLabel(self)
        pixmap = QPixmap(logo_path)
        self.logo_label.setPixmap(pixmap)
        self.logo_label.setScaledContents(True)
        self.logo_label.setFixedSize(80, 50)

        # Title
        self.title_label = QLabel("GCS CONTROL PANEL", self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold;")

        top_layout.addWidget(self.logo_label)
        top_layout.addStretch()
        top_layout.addWidget(self.title_label)
        top_layout.addStretch()

        self.main_layout.addLayout(top_layout)

    def setup_middle_section(self):
        """Setup the middle section with server statuses and logs in the same row."""
        middle_layout = QHBoxLayout()

        # Server Status Section
        server_layout = QHBoxLayout()

        # Voice Server Section
        self.voice_section = self.create_server_section(
            "Voice Server", self.stop_voice_ping
        )
        server_layout.addLayout(self.voice_section)

        # Window Server Section
        self.window_section = self.create_server_section(
            "Window Server", self.stop_window_ping
        )
        server_layout.addLayout(self.window_section)

        # Add Server Layout to Middle Layout
        middle_layout.addLayout(server_layout)

        # Logs Section
        self.setup_logs_section(middle_layout)

        self.main_layout.addLayout(middle_layout)

    def create_server_section(self, server_name, stop_function):
        """Create a section for a server."""
        layout = QVBoxLayout()

        # Server Label
        label = QLabel(server_name, self)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 18px; font-weight: bold;")
        label.setFixedWidth(150)  # Set a fixed width for the label (adjust as needed)
        layout.addWidget(label)

        # Status Bar
        status_bar = QLabel(self)
        status_bar.setFixedSize(150, 20)
        status_bar.setStyleSheet("background-color: red; border: 1px solid black;")
        layout.addWidget(status_bar, alignment=Qt.AlignCenter)

        # Shutdown Button
        shutdown_button = QPushButton("Shutdown", self)
        shutdown_button.setStyleSheet("font-size: 14px;")
        shutdown_button.clicked.connect(stop_function)
        layout.addWidget(shutdown_button, alignment=Qt.AlignCenter)

        layout.addStretch()

        # Save references for updating
        if server_name == "Voice Server":
            self.voice_status_bar = status_bar
        elif server_name == "Window Server":
            self.window_status_bar = status_bar

        # Add Vertical Divider
        vertical_line = QFrame(self)
        vertical_line.setFrameShape(QFrame.VLine)
        vertical_line.setFrameShadow(QFrame.Sunken)
        vertical_line.setStyleSheet("background-color: black;")
        vertical_line.setFixedWidth(2)  # Width of the line
        layout.addWidget(vertical_line, alignment=Qt.AlignCenter)

        return layout

    def setup_logs_section(self, parent_layout):
        """Setup the logs section."""
        log_layout = QVBoxLayout()

        # Logs Label (This remains at its original position)
        log_label = QLabel("Logs", self)
        log_label.setAlignment(Qt.AlignLeft)
        log_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        log_label.setFixedWidth(150)  # Set a fixed width for the label (adjust as needed)
        log_layout.addWidget(log_label)

        # Logs Area (Allow it to expand vertically, remove fixed size)
        self.log_section = QTextEdit(self)
        self.log_section.setReadOnly(True)
        self.log_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Allow expansion
        self.log_section.setStyleSheet("font-size: 12px;")
        self.log_section.setFixedWidth(400)  # Optionally, set a fixed width for the log section
        log_layout.addWidget(self.log_section)

        # Add the log layout to the parent layout, ensuring it's added correctly
        parent_layout.addLayout(log_layout)

        # Initialize the log section with a message
        self.log_event("Log Section Initialized.")

    def setup_timers(self):
        """Setup the timers for server monitoring."""
        self.voice_timer = QTimer(self)
        self.voice_timer.timeout.connect(self.ping_voice_server)
        self.voice_timer.start(5000)

        self.window_timer = QTimer(self)
        self.window_timer.timeout.connect(self.ping_window_server)
        self.window_timer.start(5000)

    def log_event(self, message):
        """Add an event to the log section and write to the log file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"{timestamp} - {message}"

        # Update the QTextEdit log section
        self.log_section.append(log_message)

        # Write to the log file
        with open(self.log_file, 'a') as log_file:
            log_file.write(log_message + "\n")

    def update_status_bar(self, status_bar, status):
        """Update the color of a status bar."""
        status_bar.setStyleSheet(f"background-color: {status}; border: 1px solid black;")

    def ping_voice_server(self):
        try:
            response = ping(self.voice_ip_to_ping, timeout=2)
            if response:
                if not self.voice_server_status:
                    self.log_event("Voice Server became reachable.")
                self.voice_server_status = True
                self.update_status_bar(self.voice_status_bar, "green")
            else:
                if self.voice_server_status:
                    self.log_event("Voice Server became unreachable.")
                self.voice_server_status = False
                self.update_status_bar(self.voice_status_bar, "red")
        except Exception as e:
            self.update_status_bar(self.voice_status_bar, "red")
            print(f"Voice Ping Error: {e}")

    def ping_window_server(self):
        try:
            response = ping(self.window_ip_to_ping, timeout=2)
            if response:
                if not self.window_server_status:
                    self.log_event("Window Server became reachable.")
                self.window_server_status = True
                self.update_status_bar(self.window_status_bar, "green")
            else:
                if self.window_server_status:
                    self.log_event("Window Server became unreachable.")
                self.window_server_status = False
                self.update_status_bar(self.window_status_bar, "red")
        except Exception as e:
            self.update_status_bar(self.window_status_bar, "red")
            print(f"Window Ping Error: {e}")

    def stop_voice_ping(self):
        self.voice_timer.stop()
        self.update_status_bar(self.voice_status_bar, "red")
        self.log_event("Voice Server monitoring stopped.")

    def stop_window_ping(self):
        self.window_timer.stop()
        self.update_status_bar(self.window_status_bar, "red")
        self.log_event("Window Server monitoring stopped.")


def run_app(width=1200, height=600, voice_ip_to_ping="10.10.10.28", window_ip_to_ping="192.168.10.217", logo_path="gcs_logo.png"):
    # Create log file with current date
    log_file = datetime.now().strftime("%d-%m-%Y") + "_logs.txt"
    
    # Check if log file exists, if not create a new one
    if not os.path.exists(log_file):
        with open(log_file, 'w') as file:
            file.write("Log file created on " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")

    app = QApplication(sys.argv)
    window = MainWindow(width, height, voice_ip_to_ping, window_ip_to_ping, logo_path, log_file)
    window.show()
    sys.exit(app.exec_())


# Run the app with default values
run_app()
