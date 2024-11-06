import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self, width, height):
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

    # Function to update the color of the status bars
    def update_status_bar(self, voice_status, window_status):
        # Update color based on parameters
        self.voice_status_bar.setStyleSheet(f"background-color: {voice_status};")
        self.window_status_bar.setStyleSheet(f"background-color: {window_status};")

# Main function to run the app
def run_app(width=1024, height=600):
    app = QApplication(sys.argv)
    
    # Set up the main window with specified width and height
    main_window = MainWindow(width, height)
    main_window.show()
    
    # Example of updating status bar colors (e.g., based on backend results)
    # Call main_window.update_status_bar("green", "yellow") when integrating with backend
    main_window.update_status_bar("red", "red")  # Temporary example colors
    
    # Execute the app
    sys.exit(app.exec_())

# Specify your desired width and height here
if __name__ == "__main__":
    run_app(width=1024, height=600)
