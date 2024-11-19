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
        self.setGeometry(100, 100, width, height)
        self.voice_server_status = False
        self.window_server_status = False
        self.log_file = log_file
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        self.setup_top_section(logo_path)
        self.setup_middle_section()
        self.voice_ip_to_ping = voice_ip_to_ping
        self.window_ip_to_ping = window_ip_to_ping
        self.setup_timers()

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
        self.voice_section = self.create_server_section(
            "Voice Server", self.stop_voice_ping
        )
        server_layout.addLayout(self.voice_section)
        self.window_section = self.create_server_section(
            "Window Server", self.stop_window_ping
        )
        server_layout.addLayout(self.window_section)
        middle_layout.addLayout(server_layout)
        self.setup_logs_section(middle_layout)
        self.main_layout.addLayout(middle_layout)

    def create_server_section(self, server_name, stop_function):
        layout = QVBoxLayout()
        label = QLabel(server_name, self)
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
        shutdown_button.clicked.connect(stop_function)
        layout.addWidget(shutdown_button, alignment=Qt.AlignCenter)
        layout.addStretch()
        if server_name == "Voice Server":
            self.voice_status_bar = status_bar
        elif server_name == "Window Server":
            self.window_status_bar = status_bar
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
        self.log_section = QTextEdit(self)
        self.log_section.setReadOnly(True)
        self.log_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.log_section.setStyleSheet("font-size: 12px;")
        self.log_section.setFixedWidth(400)
        log_layout.addWidget(self.log_section)
        parent_layout.addLayout(log_layout)
        self.log_event("Log Section Initialized.")

    def setup_timers(self):
        self.voice_timer = QTimer(self)
        self.voice_timer.timeout.connect(self.ping_voice_server)
        self.voice_timer.start(5000)
        self.window_timer = QTimer(self)
        self.window_timer.timeout.connect(self.ping_window_server)
        self.window_timer.start(5000)

    def log_event(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"{timestamp} - {message}"
        self.log_section.append(log_message)
        with open(self.log_file, 'a') as log_file:
            log_file.write(log_message + "\n")

    def update_status_bar(self, status_bar, status):
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
    log_file = datetime.now().strftime("%d-%m-%Y") + "_logs.txt"
    if not os.path.exists(log_file):
        with open(log_file, 'w') as file:
            file.write("Log file created on " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
    app = QApplication(sys.argv)
    window = MainWindow(width, height, voice_ip_to_ping, window_ip_to_ping, logo_path, log_file)
    window.show()
    sys.exit(app.exec_())


run_app()
