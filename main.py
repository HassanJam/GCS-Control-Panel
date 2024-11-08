import sys
from ping3 import ping
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QFrame
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap


class MainWindow(QMainWindow):
    def __init__(self, width, height, voice_ip_to_ping, window_ip_to_ping, logo_path):
        super().__init__()

        self.setWindowTitle("GCS CONTROL PANEL")
        self.setGeometry(100, 100, width, height)

        # Logo
        self.logo_label = QLabel(self)
        pixmap = QPixmap(logo_path)
        self.logo_label.setPixmap(pixmap)
        self.logo_label.setScaledContents(True)
        self.logo_label.setGeometry(10, 5, 70, 50)

        # Main Title
        self.label = QLabel("GCS CONTROL PANEL", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setGeometry(0, 10, width, 50)
        self.label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.label.setContentsMargins(70, 0, 0, 0)

        # Horizontal Line under Title
        self.title_line = QFrame(self)
        self.title_line.setGeometry(0, 60, width, 2)
        self.title_line.setStyleSheet("background-color: black;")

        # Voice Server Label
        self.voice_server_label = QLabel("Voice Server", self)
        self.voice_server_label.setAlignment(Qt.AlignLeft)
        self.voice_server_label.setGeometry(100, 100, 150, 50)
        self.voice_server_label.setStyleSheet("font-size: 18px;")

        # Window Server Label
        self.window_server_label = QLabel("Window Server", self)
        self.window_server_label.setAlignment(Qt.AlignRight)
        self.window_server_label.setGeometry(width - 290, 100, 150, 50)
        self.window_server_label.setStyleSheet("font-size: 18px;")

        # Vertical Line between Servers
        self.server_divider = QFrame(self)
        self.server_divider.setGeometry(width // 2 - 1, 100, 2, 130)
        self.server_divider.setStyleSheet("background-color: black;")

        # Voice Status Bar
        self.voice_status_bar = QLabel(self)
        self.voice_status_bar.setGeometry(100, 160, 150, 20)
        self.voice_status_bar.setStyleSheet("background-color: red;")

        # Window Status Bar
        self.window_status_bar = QLabel(self)
        self.window_status_bar.setGeometry(width - 290, 160, 150, 20)
        self.window_status_bar.setStyleSheet("background-color: red;")

        # Voice Shutdown Button
        self.voice_shutdown_button = QPushButton("Shutdown", self)
        self.voice_shutdown_button.setGeometry(100, 190, 150, 30)
        self.voice_shutdown_button.setStyleSheet("font-size: 16px;")

        # Window Shutdown Button
        self.window_shutdown_button = QPushButton("Shutdown", self)
        self.window_shutdown_button.setGeometry(width - 290, 190, 150, 30)
        self.window_shutdown_button.setStyleSheet("font-size: 16px;")

        # Horizontal Line between Shutdown Buttons
        self.shutdown_line = QFrame(self)
        self.shutdown_line.setGeometry(0, 230, width, 2)
        self.shutdown_line.setStyleSheet("background-color: black;")

        # Server IPs
        self.voice_ip_to_ping = voice_ip_to_ping
        self.window_ip_to_ping = window_ip_to_ping

        # Timers
        self.voice_timer = QTimer(self)
        self.voice_timer.timeout.connect(self.ping_voice_server)
        self.voice_timer.start(5000)

        self.window_timer = QTimer(self)
        self.window_timer.timeout.connect(self.ping_window_server)
        self.window_timer.start(5000)

        # Button Actions
        self.voice_shutdown_button.clicked.connect(self.stop_voice_ping)
        self.window_shutdown_button.clicked.connect(self.stop_window_ping)

    def update_voice_status_bar(self, status):
        self.voice_status_bar.setStyleSheet(f"background-color: {status};")

    def update_window_status_bar(self, status):
        self.window_status_bar.setStyleSheet(f"background-color: {status};")

    def ping_voice_server(self):
        try:
            response = ping(self.voice_ip_to_ping, timeout=2)
            if response:
                self.update_voice_status_bar("green")
            else:
                self.update_voice_status_bar("red")
        except Exception as e:
            print(f"Voice Ping Error: {e}")
            self.update_voice_status_bar("red")

    def ping_window_server(self):
        try:
            response = ping(self.window_ip_to_ping, timeout=2)
            if response:
                self.update_window_status_bar("green")
            else:
                self.update_window_status_bar("red")
        except Exception as e:
            print(f"Window Ping Error: {e}")
            self.update_window_status_bar("red")

    def stop_voice_ping(self):
        self.voice_timer.stop()
        self.update_voice_status_bar("red")

    def stop_window_ping(self):
        self.window_timer.stop()
        self.update_window_status_bar("red")

    def closeEvent(self, event):
        """Handle application close event."""
        self.cleanup_resources()
        event.accept()  # Ensure the application closes

    def cleanup_resources(self):
        """Stop timers and clean up resources."""
        if self.voice_timer.isActive():
            self.voice_timer.stop()
        if self.window_timer.isActive():
            self.window_timer.stop()
        print("Resources cleaned up. Timers stopped.")


def run_app(width=800, height=600, voice_ip_to_ping="192.168.10.212", window_ip_to_ping="192.168.10.60", logo_path="logo.jpeg"):
    app = QApplication(sys.argv)

    main_window = MainWindow(width, height, voice_ip_to_ping, window_ip_to_ping, logo_path)
    main_window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    run_app(width=800, height=600, voice_ip_to_ping="192.168.10.217", window_ip_to_ping="192.168.10.60", logo_path="gcs_logo.png")
