import json
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QLineEdit, QFormLayout, QMessageBox
)

JSON_FILE = "servers.json"

def show_error_popup(message:str) -> None:
    """opens a dialog message box that tells the user that an error has occurred

    :param message: message to display
    :type message: string
    """
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Warning)  # Warning icon
    msg_box.setWindowTitle("Error")
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)  # Only "OK" button
    msg_box.exec()  # Show the popup

class AddServerWindow(QDialog):
    def __init__(self, width:int=400, height:int=600) -> None:
        """opens a dialog that asks the user to input the server name and ip address. Adds both to a json file

        :param width: width of dialog, defaults to 400
        :type width: int, optional
        :param height: height of dialog, defaults to 600
        :type height: int, optional
        """
        super().__init__()
        # initialize popup dialog
        self.setWindowTitle("Add Server")
        self.setGeometry(100, 100, width, height)
        self.layout = QVBoxLayout()
        
        # Create input fields
        self.name_input = QLineEdit(self)
        self.ip_input = QLineEdit(self)

        # Form layout for labels and input fields
        form_layout = QFormLayout()
        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("IP Address:", self.ip_input)

        # Add button
        self.add_button = QPushButton("Add", self)
        self.add_button.clicked.connect(self.add_entry)

        # Main layout
        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(self.add_button)
        self.setLayout(layout)
    
    def add_entry(self):
        """create 2 entry fields, one to take the server name, the other to take the ip address
        """
        name = self.name_input.text().strip()
        ip = self.ip_input.text().strip()

        if name and ip:
            self.save_to_json(name, ip)
            self.accept()
        else:
            print("Error: Both fields must be filled!")

    def save_to_json(self, name:str, ip:str) -> None:
        """saves data entered by user into a json file

        :param name: name of server
        :type name: string
        :param ip: ip address of server
        :type ip: string
        """
        
        data = {}
        
        # if the file does not exist, create it
        if not os.path.exists(JSON_FILE):
            with open(JSON_FILE, "w") as file:
                json.dump({}, file)
        
        # load existing data
        with open(JSON_FILE, "r") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = {}  # Reset if file is corrupted

        # Append new entry
        if name.lower() not in data:
            data[name.lower()] = {"ip": ip}
        else:
            show_error_popup(message="A server by that name already exists, please enter with a different name")

        # Write back to JSON file
        with open(JSON_FILE, "w") as file:
            json.dump(data, file, indent=4)

        print(f"Saved: {name} - {ip}")

