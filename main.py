import sys
import json
import numpy as np
import struct
import pyqtgraph as pg
import serial
from serial.tools import list_ports
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFileDialog, QMainWindow, QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit, QSlider, QCheckBox, QComboBox, QMessageBox, QScrollArea
from PySide6.QtCore import Qt, QThread, Signal

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.acceleretion_data = [np.array([]), 
                                  np.array([]), 
                                  np.array([])]
        self.data_file_path = "data.bin"
        with open(self.data_file_path, "wb") as file:
            pass

        self.setWindowTitle("Data visualization system for an acceleration tracker")
        self.resize(920, 720)
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
        self.settings_label = QLabel("Port settings")
        self.settings_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.settings_layout.addWidget(self.settings_label)
        
        self.is_recording = False
        
        self.ports_label = QLabel("Port")
        self.ports_label.setStyleSheet("padding: 0px; margin: 0px; padding-left: 5px;")
        self.ports_label.setContentsMargins(0, 0, 0, 0)
        self.ports_label.setFont(QFont("Arial", 12))
        self.settings_layout.addWidget(self.ports_label)
        self.ports = list_ports.comports()
        self.ports_list = QComboBox()
        if len(self.ports) != 0:
            for port in self.ports:
                self.ports_list.addItem(port.description, port.device)
        else:
            self.ports_list.addItem("Немає COM портів", None)
        # self.ports_list.currentIndexChanged.connect(self.port_changed)
        self.settings_layout.addWidget(self.ports_list)
        
        self.rate_label = QLabel("Baud Rate")
        self.rate_label.setStyleSheet("padding: 0px; margin: 0px; padding-left: 5px;")
        self.rate_label.setContentsMargins(0, 5, 0, 0)
        self.rate_label.setFont(QFont("Arial", 12))
        self.settings_layout.addWidget(self.rate_label)
        self.rate_list = QComboBox()
        for rate in [9600, 19200, 38400, 57600, 115200]:
            self.rate_list.addItem(str(rate), rate)
        self.settings_layout.addWidget(self.rate_list)
        
        self.connect_port_but = QPushButton("Connect port")
        self.connect_port_but.clicked.connect(self.connect_port)
        self.connect_port_but.setObjectName("connect_but")
        self.settings_layout.addWidget(self.connect_port_but)
        
        self.disconnect_port_but = QPushButton("Disconnect port")
        self.disconnect_port_but.clicked.connect(self.disconnect_port)
        self.settings_layout.addWidget(self.disconnect_port_but)
        
        self.receive_data_but = QPushButton("Receive data")
        self.receive_data_but.clicked.connect(self.receive_data)
        self.settings_layout.addWidget(self.receive_data_but)
        self.receive_data_but.hide()
        
        self.connection_status = QLabel("Status: Disconnected!")
        self.connection_status.setContentsMargins(0, 0, 0, 0)
        self.connection_status.setFont(QFont("Arial", 12))
        self.settings_layout.addWidget(self.connection_status)

        self.settings_layout.addStretch()
        self.body_layout.addWidget(self.settings)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        self.graph_widget = QWidget()
        self.graph_widget.setObjectName("graph")
        self.graph_widget.setProperty("class", "infoBlock")
        self.graph_layout = QVBoxLayout(self.graph_widget)
        self.graph_label = QLabel("Graph")
        self.graph_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.graph_layout.addWidget(self.graph_label)
        scroll_area.setWidget(self.graph_widget)
        self.body_layout.addWidget(scroll_area)

        self.graph_container = QWidget()
        self.graph_container.setObjectName("graphContainer")
        self.graph_container.setContentsMargins(7, 7, 7, 7)
        self.graph_container_layout = QVBoxLayout(self.graph_container)
        self.graph = pg.PlotWidget()
        self.graph.setMinimumHeight(200)
        self.graph.setMaximumHeight(200)
        self.graph.setBackground("#ffffff")
        self.graph.setLabel("left", "a, m/s²")
        self.graph.setLabel("bottom", "t, s")
        # self.x = np.linspace(0, 10, 11)
        self.axis_label = QLabel("X-axis: <span style='color: red;'>red</span>, Y-axis: <span style='color: green;'>green</span>, Z-axis: <span style='color: blue;'>blue</span>")
        self.graph_container_layout.addWidget(self.axis_label)
        self.graph_container_layout.addWidget(self.graph)
        
        self.x_graph = pg.PlotWidget()
        self.x_graph.setMinimumHeight(200)
        self.x_graph.setMaximumHeight(200)
        self.x_graph.setBackground("#ffffff")
        self.x_graph.setLabel("left", "a_x, m/s²")
        self.x_graph.setLabel("bottom", "t, s")
        self.graph_container_layout.addWidget(self.x_graph)
        self.x_graph.hide()
        self.y_graph = pg.PlotWidget()
        self.y_graph.setMinimumHeight(200)
        self.y_graph.setMaximumHeight(200)
        self.y_graph.setBackground("#ffffff")
        self.y_graph.setLabel("left", "a_y, m/s²")
        self.y_graph.setLabel("bottom", "t, s")
        self.graph_container_layout.addWidget(self.y_graph)
        self.y_graph.hide()
        self.z_graph = pg.PlotWidget()
        self.z_graph.setMinimumHeight(200)
        self.z_graph.setMaximumHeight(200)
        self.z_graph.setBackground("#ffffff")
        self.z_graph.setLabel("left", "a_z, m/s²")
        self.z_graph.setLabel("bottom", "t, s")
        self.graph_container_layout.addWidget(self.z_graph)
        self.z_graph.hide()

        self.module_graph = pg.PlotWidget()
        self.module_graph.setMinimumHeight(200)
        self.module_graph.setMaximumHeight(200)
        self.module_graph.setBackground("#ffffff")
        self.module_graph.setLabel("left", "a, m/s²")
        self.module_graph.setLabel("bottom", "t, s")
        self.module_graph_label = QLabel("Module of acceleration vector")
        self.graph_container_layout.addWidget(self.module_graph_label)
        self.graph_container_layout.addWidget(self.module_graph)

        self.sync_layout = QHBoxLayout()
        self.sync_x_axis_checkbox = QCheckBox("Sync X-axis")
        self.sync_x_axis_checkbox.setChecked(False)
        self.sync_x_axis_checkbox.stateChanged.connect(self.sync_graphs)
        self.sync_layout.addWidget(self.sync_x_axis_checkbox)
        self.graph_container_layout.addLayout(self.sync_layout)
        self.sync_y_axis_checkbox = QCheckBox("Sync Y-axis")
        self.sync_y_axis_checkbox.setChecked(False)
        self.sync_y_axis_checkbox.stateChanged.connect(self.sync_graphs)
        self.sync_layout.addWidget(self.sync_y_axis_checkbox)
        
        self.separate_graphs_checkbox = QCheckBox("Separate the projection graphs")
        self.separate_graphs_checkbox.setChecked(False)
        self.separate_graphs_checkbox.stateChanged.connect(self.separate_graphs)
        self.sync_layout.addWidget(self.separate_graphs_checkbox)
        
        self.sync_layout.addStretch()
        
        self.graph_container_layout.addLayout(self.sync_layout)
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

        # port_menu = self.menuBar().addMenu("Port")
        # connect_port = port_menu.addAction("Connect")
        # disconnect_port = port_menu.addAction("Disconnect")
        # connect_port.triggered.connect(self.connect_port)
        # disconnect_port.triggered.connect(self.disconnect_port)

        self.centralWidget = QWidget()
        self.centralWidget.setObjectName("centralWidget")
        self.centralWidget.setLayout(self.layout)
        self.setCentralWidget(self.centralWidget)

    def open_file(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*.bin);;Text Files (*.bin)")
            self.load_file(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open the file:\n{e}")
        
    def load_file(self, file_path):
        if file_path:
            self.acceleretion_data = [np.array([]), 
                                      np.array([]), 
                                      np.array([])]
            
            with open(file_path, 'rb') as file:
                data = file.read()
            measurements = list(struct.iter_unpack("<fff", data))
            for measurement in measurements:
                self.acceleretion_data[0] = np.append(self.acceleretion_data[0], measurement[0])
                self.acceleretion_data[1] = np.append(self.acceleretion_data[1], measurement[1])
                self.acceleretion_data[2] = np.append(self.acceleretion_data[2], measurement[2])
            
            if len(measurements) > 0:
                self.x1_slider.setMaximum(len(self.acceleretion_data[0]) - 1)
                self.x2_slider.setMaximum(len(self.acceleretion_data[0]) - 1)
                self.x2_slider.setValue(len(self.acceleretion_data[0]) - 1)
                self.x = np.linspace(0, len(self.acceleretion_data[0]) - 1, len(self.acceleretion_data[0]))
                
            self.update_graph()
        
    def save_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "saved_data.bin", "All Files (*.bin);;Text Files (*.bin)")
        if file_path:
            try:
                with open(file_path, "wb") as file, open(self.data_file_path, "rb") as data:
                    file.write(data.read())
                QMessageBox.information(self, "Success", "File saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save the file:\n{e}")    

    def connect_port(self):
        if not self.is_recording:
            self.serial_reader = SerialReader(port = self.ports_list.currentData(), baudrate=self.rate_list.currentData())
        
            self.serial_reader.connected.connect(self.on_connected)
            self.serial_reader.disconnected.connect(self.on_disconnected)
            self.serial_reader.data_received.connect(self.when_receive_data)
            self.serial_reader.error.connect(self.on_serial_error)
            # self.serial_reader.start()
            self.connection_status.setText("Status: Connected!")
            self.is_recording = True
            self.receive_data_but.show()

    def disconnect_port(self):
        if self.is_recording:
            self.serial_reader.disconnect_port()
            self.connection_status.setText("Status: Disconnected!")
            self.is_recording = False
            self.receive_data_but.hide()

    def on_connected(self):        
        self.binary_file = open(self.data_file_path, "wb")

    def on_disconnected(self):
        if hasattr(self, "binary_file"):
            if not self.binary_file.closed:
                self.binary_file.close()

    def when_receive_data(self, data):
        # print("Received:", data)

        self.binary_file.write(data)
        self.binary_file.flush()
        self.load_file(self.data_file_path)

    def receive_data(self):
        if self.is_recording:
            print("Receiving data")
            self.serial_reader.start()

    def on_serial_error(self, error):
        QMessageBox.critical(self, "Serial error", error)
    
    def refresh_ports_list(self):
        self.ports = list_ports.comports()
        self.ports_list.clear()
        if len(self.ports) != 0:
            for port in self.ports:
                self.ports_list.addItem(port.description, port.device)
        else:
            self.ports_list.addItem("Немає COM портів", None)

    def update_graph(self):
        self.graph.clear()
        self.module_graph.clear()
        
        if len(self.acceleretion_data[0]) > 0 and len(self.acceleretion_data[1]) > 0 and len(self.acceleretion_data[2]) > 0:
            self.graph.plot(self.x[:len(self.acceleretion_data[0])], self.acceleretion_data[0], pen=pg.mkPen(color="red", width=3), name="X-axis")
            self.graph.plot(self.x[:len(self.acceleretion_data[1])], self.acceleretion_data[1], pen=pg.mkPen(color="green", width=3), name="Y-axis")
            self.graph.plot(self.x[:len(self.acceleretion_data[2])], self.acceleretion_data[2], pen=pg.mkPen(color="blue", width=3), name="Z-axis")
            
            self.x_graph.plot(self.x[:len(self.acceleretion_data[0])], self.acceleretion_data[0], pen=pg.mkPen(color="red", width=3), name="X-axis")
            self.y_graph.plot(self.x[:len(self.acceleretion_data[1])], self.acceleretion_data[1], pen=pg.mkPen(color="green", width=3), name="Y-axis")
            self.z_graph.plot(self.x[:len(self.acceleretion_data[2])], self.acceleretion_data[2], pen=pg.mkPen(color="blue", width=3), name="Z-axis")
            
            module = np.sqrt(self.acceleretion_data[0]**2 + self.acceleretion_data[1]**2 + self.acceleretion_data[2]**2)
            self.module_graph.plot(self.x[:len(module)], module, pen=pg.mkPen(color="#00a67a", width=3), name="Module")
            
            self.graph.setXRange(0, len(module) - 1)
            self.graph.setYRange(min(min(self.acceleretion_data[0]), min(self.acceleretion_data[1]), min(self.acceleretion_data[2])), max(max(self.acceleretion_data[0]), max(self.acceleretion_data[1]), max(self.acceleretion_data[2])))
            self.module_graph.setXRange(0, len(module) - 1)
            self.module_graph.setYRange(min(module), max(module))
    
    def change_limits(self):
        self.graph.setXRange(self.x1_slider.value(), self.x2_slider.value())
        self.module_graph.setXRange(self.x1_slider.value(), self.x2_slider.value())
        self.x1_slider.setMaximum(self.x2_slider.value())
        self.x2_slider.setMinimum(self.x1_slider.value())
        self.x1_slider_label.setText(f" Left limit: {self.x1_slider.value()}")
        self.x2_slider_label.setText(f"Right limit: {self.x2_slider.value()}")

    def sync_graphs(self):
        self.module_graph.getViewBox().setXLink(self.graph.getViewBox() if self.sync_x_axis_checkbox.isChecked() else None)
        self.module_graph.getViewBox().setYLink(self.graph.getViewBox() if self.sync_y_axis_checkbox.isChecked() else None)
        self.x_graph.getViewBox().setXLink(self.graph.getViewBox() if self.sync_x_axis_checkbox.isChecked() else None)
        self.x_graph.getViewBox().setYLink(self.graph.getViewBox() if self.sync_y_axis_checkbox.isChecked() else None)
        self.y_graph.getViewBox().setXLink(self.graph.getViewBox() if self.sync_x_axis_checkbox.isChecked() else None)
        self.y_graph.getViewBox().setYLink(self.graph.getViewBox() if self.sync_y_axis_checkbox.isChecked() else None)
        self.z_graph.getViewBox().setXLink(self.graph.getViewBox() if self.sync_x_axis_checkbox.isChecked() else None)
        self.z_graph.getViewBox().setYLink(self.graph.getViewBox() if self.sync_y_axis_checkbox.isChecked() else None)

    def separate_graphs(self):
        if self.separate_graphs_checkbox.isChecked():
            self.graph.hide()
            self.x_graph.show()
            self.y_graph.show()
            self.z_graph.show()
        else:
            self.graph.show()
            self.x_graph.hide()
            self.y_graph.hide()
            self.z_graph.hide()

    def get_frequency(self):
        pass
    
    def set_frequency(self, frequency):
        pass
    
    def clear_data(self):
        pass
    
class SerialReader(QThread):
    data_received = Signal(bytes)
    connected = Signal()
    disconnected = Signal()
    error = Signal(str)
    
    def __init__(self, port, baudrate, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE):
        super().__init__()
        
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits

        self.running = False
        self.ser = None
    
    def run(self):
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=self.bytesize,
                parity=self.parity,
                stopbits=self.stopbits,
                # timeout=0.1
            )

            self.running = True
            self.connected.emit()

            while self.running:
                if self.ser.in_waiting:
                    data = self.ser.read(self.ser.in_waiting)

                    if data:
                        self.data_received.emit(data)

        except serial.SerialException as e:
            self.error.emit(str(e))

        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()

            self.ser = None
            self.running = False
            self.disconnected.emit()

    def disconnect_port(self):
        self.running = False
        self.wait()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
