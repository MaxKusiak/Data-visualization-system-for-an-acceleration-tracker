import sys
import json
import numpy as np
import struct
import pyqtgraph as pg
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFileDialog, QMainWindow, QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit, QSlider, QCheckBox
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
        self.settings.setMinimumWidth(300)
        self.settings.setObjectName("settings")
        self.settings.setProperty("class", "infoBlock")
        self.settings_layout = QVBoxLayout(self.settings)
        self.settings_label = QLabel("Settings")
        self.settings_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.settings_layout.addWidget(self.settings_label)
        self.settings_layout.setAlignment(Qt.AlignCenter)
        self.settings_layout.addStretch()
        self.body_layout.addWidget(self.settings)

        self.graph_widget = QWidget()
        self.graph_widget.setObjectName("graph")
        self.graph_widget.setProperty("class", "infoBlock")
        self.graph_layout = QVBoxLayout(self.graph_widget)
        self.graph_label = QLabel("Graph")
        self.graph_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.graph_layout.addWidget(self.graph_label)
        self.body_layout.addWidget(self.graph_widget)

        self.graph_container = QWidget()
        self.graph_container.setObjectName("graphContainer")
        self.graph_container.setContentsMargins(7, 7, 7, 7)
        self.graph_container_layout = QVBoxLayout(self.graph_container)
        self.graph = pg.PlotWidget()
        self.graph.setMaximumHeight(200)
        self.graph.setBackground("#ffffff")
        self.graph.setLabel("left", "a, m/s²")
        self.graph.setLabel("bottom", "t, s")
        # self.x = np.linspace(0, 10, 11)
        self.axis_label = QLabel("X-axis: <span style='color: red;'>red</span>, Y-axis: <span style='color: green;'>green</span>, Z-axis: <span style='color: blue;'>blue</span>")
        self.graph_container_layout.addWidget(self.axis_label)
        self.graph_container_layout.addWidget(self.graph)

        self.module_graph = pg.PlotWidget()
        self.module_graph.setMaximumHeight(200)
        self.module_graph.setBackground("#ffffff")
        self.module_graph.setLabel("left", "a, m/s²")
        self.module_graph.setLabel("bottom", "t, s")
        self.module_graph_label = QLabel("Module of acceleration vector")
        self.graph_container_layout.addWidget(self.module_graph_label)
        self.graph_container_layout.addWidget(self.module_graph)

        self.module_graph.getViewBox().setXLink(self.graph.getViewBox())
        self.module_graph.getViewBox().setYLink(self.graph.getViewBox())

        self.sync_graphs_checkbox = QCheckBox("Sync graphs")
        self.sync_graphs_checkbox.setChecked(True)
        self.sync_graphs_checkbox.stateChanged.connect(self.sync_graphs)
        self.graph_container_layout.addWidget(self.sync_graphs_checkbox)

        self.graph_container_layout.addStretch()
        self.graph_layout.addWidget(self.graph_container)

        self.x1_slider_layout = QHBoxLayout()
        self.x1_slider = QSlider(Qt.Horizontal)
        self.x1_slider.setMinimum(0)
        self.x1_slider.setMaximum(10)
        self.x1_slider.setValue(0)
        self.x1_slider.valueChanged.connect(self.change_limits)
        self.x1_slider_layout.addWidget(self.x1_slider)
        self.x1_slider_label = QLabel(f" Left limit: {self.x1_slider.value()}")
        self.x1_slider_layout.addWidget(self.x1_slider_label)
        self.graph_layout.addLayout(self.x1_slider_layout)

        self.x2_slider = QSlider(Qt.Horizontal)
        self.x2_slider.setMinimum(0)
        self.x2_slider.setMaximum(10)
        self.x2_slider.setValue(10)
        self.x2_slider.valueChanged.connect(self.change_limits)
        self.x2_slider_layout = QHBoxLayout()
        self.x2_slider_layout.addWidget(self.x2_slider)
        self.x2_slider_label = QLabel(f"Right limit: {self.x2_slider.value()}")
        self.x2_slider_layout.addWidget(self.x2_slider_label)
        self.graph_layout.addLayout(self.x2_slider_layout)
        
        self.graph_layout.addStretch()

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
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*.bin);;Text Files (*.bin)")
        if file_path:
            self.acceleretion_data = [np.array([]), 
                                      np.array([]), 
                                      np.array([])]
            with open(file_path, 'rb') as file:
                i = 0
                while True:
                    bytes_read = file.read(4)
                    if not bytes_read:
                        break
                    value = struct.unpack('f', bytes_read)[0]
                    self.acceleretion_data[i] = np.append(self.acceleretion_data[i], value)
                    i = (i + 1) % 3
            self.x1_slider.setMaximum(len(self.acceleretion_data[0]) - 1)
            self.x2_slider.setMaximum(len(self.acceleretion_data[0]) - 1)
            self.x2_slider.setValue(len(self.acceleretion_data[0]) - 1)
            self.x = np.linspace(0, len(self.acceleretion_data[0]) - 1, len(self.acceleretion_data[0]))
            self.update_graph()

    def save_file(self):
        # Implement file saving logic here
        print("Save file action triggered")

    def connect_port(self):
        # Implement port connection logic here
        print("Connect port action triggered")

    def disconnect_port(self):
        # Implement port disconnection logic here
        print("Disconnect port action triggered")

    def update_graph(self):
        self.graph.clear()
        
        if len(self.acceleretion_data[0]) > 0 and len(self.acceleretion_data[1]) > 0 and len(self.acceleretion_data[2]) > 0:
            self.graph.plot(self.x[:len(self.acceleretion_data[0])], self.acceleretion_data[0], pen=pg.mkPen(color="red", width=3), name="X-axis")
            self.graph.plot(self.x[:len(self.acceleretion_data[1])], self.acceleretion_data[1], pen=pg.mkPen(color="green", width=3), name="Y-axis")
            self.graph.plot(self.x[:len(self.acceleretion_data[2])], self.acceleretion_data[2], pen=pg.mkPen(color="blue", width=3), name="Z-axis")
            module = np.sqrt(self.acceleretion_data[0]**2 + self.acceleretion_data[1]**2 + self.acceleretion_data[2]**2)
            self.module_graph.clear()
            self.module_graph.plot(self.x[:len(module)], module, pen=pg.mkPen(color="#00a67a", width=3), name="Module")
    
    def change_limits(self):
        self.graph.setXRange(self.x1_slider.value(), self.x2_slider.value())
        self.module_graph.setXRange(self.x1_slider.value(), self.x2_slider.value())
        self.x1_slider.setMaximum(self.x2_slider.value())
        self.x2_slider.setMinimum(self.x1_slider.value())
        self.x1_slider_label.setText(f" Left limit: {self.x1_slider.value()}")
        self.x2_slider_label.setText(f"Right limit: {self.x2_slider.value()}")

    def sync_graphs(self):
        if self.sync_graphs_checkbox.isChecked():
            self.module_graph.getViewBox().setXLink(self.graph.getViewBox())
            self.module_graph.getViewBox().setYLink(self.graph.getViewBox())
        else:
            self.module_graph.getViewBox().setXLink(None)
            self.module_graph.getViewBox().setYLink(None)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
