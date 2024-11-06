import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton
from PyQt5.QtCore import Qt, QTimer

class MainWindow(QMainWindow):
    def __init__(self, width, height, voice_ip_to_ping, window_ip_to_ping):
        super().__init__()

        # Set window properties
        self.setWindowTitle("GCS CONTROL PANEL")
        self.setGeometry(100, 100, width, height)

        # Create and configure the center label
        self.label = QLabel("GCS CONTROL PANEL", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setGeometry(0, 10, width, 50)  # Centered at top
        self.label.setStyleSheet("font-size: 24px; font-weight: bold;")

        # Create and configure the "Voice Server" label on the left
        self.voice_server_label = QLabel("Voice Server", self)
        self.voice_server_label.setAlignment(Qt.AlignLeft)
        self.voice_server_label.setGeometry(100, 100, 150, 50)  # Position on left side
        self.voice_server_label.setStyleSheet("font-size: 18px;")

        # Create and configure the "Window Server" label on the right
        self.window_server_label = QLabel("Window Server", self)
        self.window_server_label.setAlignment(Qt.AlignRight)
        self.window_server_label.setGeometry(width - 290, 100, 150, 50)  # Position on right side
        self.window_server_label.setStyleSheet("font-size: 18px;")

        # Create the rectangular status bar under "Voice Server"
        self.voice_status_bar = QLabel(self)
        self.voice_status_bar.setGeometry(100, 160, 150, 20)  # Position directly under Voice Server
        self.voice_status_bar.setStyleSheet("background-color: red;")

        # Create the rectangular status bar under "Window Server"
        self.window_status_bar = QLabel(self)
        self.window_status_bar.setGeometry(width - 290, 160, 150, 20)  # Position directly under Window Server
        self.window_status_bar.setStyleSheet("background-color: red;")

        # Create the "Shutdown" button under "Voice Server" status bar
        self.voice_shutdown_button = QPushButton("Shutdown", self)
        self.voice_shutdown_button.setGeometry(100, 190, 150, 30)  # Position under Voice Server status bar
        self.voice_shutdown_button.setStyleSheet("font-size: 16px;")

        # Create the "Shutdown" button under "Window Server" status bar
        self.window_shutdown_button = QPushButton("Shutdown", self)
        self.window_shutdown_button.setGeometry(width - 290, 190, 150, 30)  # Position under Window Server status bar
        self.window_shutdown_button.setStyleSheet("font-size: 16px;")

        # Store the IP addresses to ping
        self.voice_ip_to_ping = voice_ip_to_ping
        self.window_ip_to_ping = window_ip_to_ping

        # Create a timer to ping the voice server every 5 seconds
        self.voice_timer = QTimer(self)
        print('pingign voice server with IP:', self.voice_ip_to_ping)
        self.voice_timer.timeout.connect(self.ping_voice_server)
        self.voice_timer.start(5000)  # 5000 milliseconds = 5 seconds
      

        # Create a timer to ping the window server every 5 seconds
        self.window_timer = QTimer(self)
        self.window_timer.timeout.connect(self.ping_window_server)
        self.window_timer.start(5000)  # 5000 milliseconds = 5 seconds

        # Connect the "Shutdown" buttons to stop the corresponding ping
        self.voice_shutdown_button.clicked.connect(self.stop_voice_ping)
        self.window_shutdown_button.clicked.connect(self.stop_window_ping)

    # Function to update the color of the "Voice Server" status bar
    def update_voice_status_bar(self, status):
        self.voice_status_bar.setStyleSheet(f"background-color: {status};")

    # Function to update the color of the "Window Server" status bar
    def update_window_status_bar(self, status):
        self.window_status_bar.setStyleSheet(f"background-color: {status};")

    def ping_voice_server(self):
        try:
            result = subprocess.run(
                ["ping", "-n", "1", self.voice_ip_to_ping],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                self.update_voice_status_bar("green")
            else:
                self.update_voice_status_bar("red")
        except Exception as e:
            print(f"Error: {e}")
            self.update_voice_status_bar("red")


    def ping_window_server(self):
        try:
            # Run the ping command for the window server
            result = subprocess.run(
                ["ping", "-n", "1", self.window_ip_to_ping], 
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW
            )

            # If the ping was successful (returncode == 0), change the color to green
            if result.returncode == 0:
                self.update_window_status_bar("green")  # Change window server bar to green
            else:
                self.update_window_status_bar("red")  # Change window server bar to red

        except Exception as e:
            # If there is any error (e.g., no network connection), set the status bar to red
            print(f"Error: {e}")
            self.update_window_status_bar("red")

    # Function to stop the voice server ping timer
    def stop_voice_ping(self):
        # Stop the ping timer for voice server
        self.voice_timer.stop()
        # Update the status bar to show red (indicating that ping is stopped)
        self.update_voice_status_bar("red")

    # Function to stop the window server ping timer
    def stop_window_ping(self):
        # Stop the ping timer for window server
        self.window_timer.stop()
        # Update the status bar to show red (indicating that ping is stopped)
        self.update_window_status_bar("red")

# Main function to run the app
def run_app(width=800, height=600, voice_ip_to_ping="192.168.10.212", window_ip_to_ping="192.168.10.60"):
    app = QApplication(sys.argv)
    
    # Set up the main window with specified width, height, and IP addresses for both servers
    main_window = MainWindow(width, height, voice_ip_to_ping, window_ip_to_ping)
    main_window.show()
    
    # Execute the app
    sys.exit(app.exec_())

# Specify your desired width and height here, and IP addresses to ping for both servers
if __name__ == "__main__":
    run_app(width=800, height=600, voice_ip_to_ping="192.168.10.212", window_ip_to_ping="192.168.10.60")  # Change IPs to the ones you want to ping
