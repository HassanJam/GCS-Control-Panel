import json
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QLineEdit, QFormLayout
)

JSON_FILE = "servers.json"

class AddServerWindow(QDialog):
    def __init__(self, width=400, height=600):
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
        name = self.name_input.text().strip()
        ip = self.ip_input.text().strip()

        if name and ip:
            self.save_to_json(name, ip)
            self.accept()
        else:
            print("Error: Both fields must be filled!")

    def save_to_json(self, name, ip):
        data = []
        
        # Load existing data if file exists
        if os.path.exists(JSON_FILE):
            with open(JSON_FILE, "r") as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    data = {}  # Reset if file is corrupted

        # Append new entry
        data[name] = {"ip": ip}

        # Write back to JSON file
        with open(JSON_FILE, "w") as file:
            json.dump(data, file, indent=4)

        print(f"Saved: {name} - {ip}")
