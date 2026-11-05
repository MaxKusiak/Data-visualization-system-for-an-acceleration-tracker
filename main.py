import sys
import json
import numpy as np
import struct
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFileDialog, QMainWindow, QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.acceleretion_data = [np.array([]), 
                                  np.array([]), 
                                  np.array([])] 

        self.setWindowTitle("Data visualization system for an acceleration tracker")
        self.resize(800, 600)
        with open("assets/style.css", "r") as f:
            self.setStyleSheet(f.read())

        # Main layout
        self.layout = QVBoxLayout()

        self.body_layout = QHBoxLayout()
        # self.body_layout.setAlignment(Qt.AlignLeft)
        self.layout.addLayout(self.body_layout)

        # Settings layout
        self.settings = QWidget()
        self.settings.setObjectName("settings")
        self.settings.setProperty("class", "infoBlock")
        self.settings_layout = QVBoxLayout(self.settings)
        self.settings_label = QLabel("Settings")
        self.settings_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.settings_layout.addWidget(self.settings_label)
        self.settings_layout.setAlignment(Qt.AlignCenter)
        self.settings_layout.addStretch()
        self.body_layout.addWidget(self.settings)

        self.graph = QWidget()
        self.graph.setObjectName("graph")
        self.graph.setProperty("class", "infoBlock")
        self.graph_layout = QVBoxLayout(self.graph)
        self.graph_label = QLabel("Graph")
        self.graph_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.graph_layout.addWidget(self.graph_label)
        self.graph_layout.setAlignment(Qt.AlignCenter)
        self.graph_layout.addStretch()
        self.body_layout.addWidget(self.graph)

        # self.layout.addStretch()

        file_menu = self.menuBar().addMenu("File")
        open_file = file_menu.addAction("Open")
        save_file = file_menu.addAction("Save")
        open_file.triggered.connect(self.open_file)
        save_file.triggered.connect(self.save_file)

        port_menu = self.menuBar().addMenu("Port")
        connect_port = port_menu.addAction("Connect")
        disconnect_port = port_menu.addAction("Disconnect")
        connect_port.triggered.connect(self.connect_port)
        disconnect_port.triggered.connect(self.disconnect_port)

        self.centralWidget = QWidget()
        self.centralWidget.setObjectName("centralWidget")
        self.centralWidget.setLayout(self.layout)
        self.setCentralWidget(self.centralWidget)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*.txt);;Text Files (*.txt)")
        if file_path:
            with open(file_path, 'r') as file:
                for line in file.readlines():
                    a = line.strip().split(' ')
                    self.acceleretion_data[0] = np.append(self.acceleretion_data[0], self.binary_to_float(a[0]))
                    self.acceleretion_data[1] = np.append(self.acceleretion_data[1], self.binary_to_float(a[1]))
                    self.acceleretion_data[2] = np.append(self.acceleretion_data[2], self.binary_to_float(a[2]))

    def save_file(self):
        # Implement file saving logic here
        print("Save file action triggered")

    def connect_port(self):
        # Implement port connection logic here
        print("Connect port action triggered")

    def disconnect_port(self):
        # Implement port disconnection logic here
        print("Disconnect port action triggered")

    def binary_to_float(self, bit_string):
        if len(bit_string) == 32:
            fmt = '>f' 
        elif len(bit_string) == 64:
            fmt = '>d'
        else:
            raise ValueError("Рядок повинен містити рівно 32 або 64 біти")
            
        int_val = int(bit_string, 2)
        
        num_bytes = len(bit_string) // 8
        byte_val = int_val.to_bytes(num_bytes, byteorder='big')
        
        return struct.unpack(fmt, byte_val)[0]

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
    