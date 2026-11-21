import sys
import json
import numpy as np
import struct
import pyqtgraph as pg
import serial
from serial.tools import list_ports
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFileDialog, QMainWindow, QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit, QSlider, QCheckBox, QComboBox, QMessageBox, QScrollArea, QDoubleSpinBox, QRadioButton
from PySide6.QtCore import Qt, QThread, Signal

def is_float(s):
    try:
        num = float(s.replace(",", "."))
        return not num != num
    except ValueError:
        return False

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
        self.resize(970, 770)
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
        self.graph_widget.setContentsMargins(13, 0, 13, 7)
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

        self.graphs = {"XYZ": self.graph, "X": self.x_graph, "Y": self.y_graph, "Z": self.z_graph, "M": self.module_graph}

        self.sync_layout = QHBoxLayout()
        self.sync_x_axis_checkbox = QCheckBox("Sync X-axis")
        self.sync_x_axis_checkbox.setChecked(False)
        self.sync_x_axis_checkbox.stateChanged.connect(self.sync_graphs)
        self.sync_layout.addWidget(self.sync_x_axis_checkbox)
        self.sync_y_axis_checkbox = QCheckBox("Sync Y-axis")
        self.sync_y_axis_checkbox.setChecked(False)
        self.sync_y_axis_checkbox.stateChanged.connect(self.sync_graphs)
        self.sync_layout.addWidget(self.sync_y_axis_checkbox)
        
        self.separate_graphs_checkbox = QCheckBox("Separate the projection graphs")
        self.separate_graphs_checkbox.setChecked(False)
        self.separate_graphs_checkbox.stateChanged.connect(self.separate_graphs)
        self.sync_layout.addWidget(self.separate_graphs_checkbox)
        
        self.show_cursors_checkbox = QCheckBox("Show cursors")
        self.show_cursors_checkbox.setChecked(False)
        self.show_cursors_checkbox.stateChanged.connect(self.show_cursors)
        self.sync_layout.addWidget(self.show_cursors_checkbox)
        
        self.sync_layout.addStretch()
        self.graph_container_layout.addLayout(self.sync_layout)
        
        self.sync_layout2 = QHBoxLayout()
        self.sync_cursors_checkbox = QCheckBox("Sync cursors")
        self.sync_cursors_checkbox.setChecked(False)
        self.sync_layout2.addWidget(self.sync_cursors_checkbox)
        
        self.sync_layout2.addStretch()
        self.graph_container_layout.addLayout(self.sync_layout2)
        
        self.cursor_mode = 0
        self.cursor_mode_layout = QHBoxLayout()
        self.cursor_mode_label = QLabel("Choose cursor mode:")
        self.cursor_mode_label.setFont(QFont("Arial", 9))
        self.cursor_mode_label.setStyleSheet("padding: 0px; margin: 0px;")
        self.cursor_mode_layout.addWidget(self.cursor_mode_label)
        self.cursor_mode_none = QRadioButton("None")
        self.cursor_mode_1 = QRadioButton("First cursor")
        self.cursor_mode_2 = QRadioButton("Second cursor")
        self.cursor_mode_lr = QRadioButton("L-R click mode")
        self.cursor_mode_none.toggled.connect(self.cursor_mode_toggled)
        self.cursor_mode_1.toggled.connect(self.cursor_mode_toggled)
        self.cursor_mode_2.toggled.connect(self.cursor_mode_toggled)
        self.cursor_mode_lr.toggled.connect(self.cursor_mode_toggled)
        self.cursor_mode_none.setChecked(True)
        self.cursor_mode_layout.addWidget(self.cursor_mode_none)
        self.cursor_mode_layout.addWidget(self.cursor_mode_1)
        self.cursor_mode_layout.addWidget(self.cursor_mode_2)
        self.cursor_mode_layout.addWidget(self.cursor_mode_lr)
        self.cursor_mode_layout.addStretch()
        
        self.graph_container_layout.addLayout(self.sync_layout)
        self.graph_container_layout.addLayout(self.cursor_mode_layout)
        self.graph_container_layout.addStretch()
        self.graph_layout.addWidget(self.graph_container)

        self.choose_graph_label = QLabel("Select a graph to display cursor values")
        self.choose_graph_label.setFont(QFont("Arial", 9))
        self.choose_graph_label.setStyleSheet("padding: 0px; margin: 0px; padding-left: 5px;")
        self.choose_graph_label.setContentsMargins(0, 5, 0, 0)
        self.choose_graph = QComboBox()
        for text, graph_name in [("Graph of all projections", "XYZ"), ("X axis graph", "X"), ("Y axis graph", "Y"), ("Z axis graph", "Z"), ("Module graph", "M")]:
            self.choose_graph.addItem(text, graph_name)
        self.choose_graph.currentIndexChanged.connect(self.change_cursor_info)
        self.graph_layout.addWidget(self.choose_graph_label)
        self.graph_layout.addWidget(self.choose_graph)
        self.choose_graph_label.hide()
        self.choose_graph.hide()
        
        self.cursor_data_layout = QHBoxLayout()
        
        self.x1 = QLineEdit("0")
        self.x1.returnPressed.connect(self.change_cursor_x1)
        self.x1_label = QLabel(f"X1: ")
        self.x1_label.setFont(QFont("Arial", 9))
        self.x1_label.setStyleSheet("padding: 0px; margin: 0px; padding-left: 5px;")
        self.y1 = QLabel(f"Y1: ")
        self.y1.setFont(QFont("Arial", 9))
        self.y1.setStyleSheet("padding: 0px; margin: 0px; padding-left: 5px;")
        self.cursor_data_layout.addWidget(self.x1_label)
        self.cursor_data_layout.addWidget(self.x1)
        self.cursor_data_layout.addWidget(self.y1)
        self.x1.hide()
        self.x1_label.hide()
        self.y1.hide()

        self.x2 = QLineEdit("0")
        self.x2.returnPressed.connect(self.change_cursor_x2)
        self.x2_label = QLabel(f"X2: ")
        self.x2_label.setFont(QFont("Arial", 9))
        self.x2_label.setStyleSheet("padding: 0px; margin: 0px; padding-left: 5px;")
        self.y2 = QLabel(f"Y2: ")
        self.y2.setFont(QFont("Arial", 9))
        self.y2.setStyleSheet("padding: 0px; margin: 0px; padding-left: 5px;")
        self.cursor_data_layout.addWidget(self.x2_label)
        self.cursor_data_layout.addWidget(self.x2)
        self.cursor_data_layout.addWidget(self.y2)
        self.x2.hide()
        self.x2_label.hide()
        self.y2.hide()
        
        self.delta = QLabel("")
        self.delta.setFont(QFont("Arial", 9))
        self.delta.setStyleSheet("padding: 0px; margin: 0px; padding-left: 5px;")
        self.graph_layout.addWidget(self.delta)
        self.delta.hide()
        
        self.cursor_data_layout.addStretch()
        self.graph_layout.addLayout(self.cursor_data_layout)
        
        self.graph_layout.addStretch()

        file_menu = self.menuBar().addMenu("File")
        open_file = file_menu.addAction("Open")
        save_file = file_menu.addAction("Save")
        open_file.triggered.connect(self.open_file)
        save_file.triggered.connect(self.save_file)

        self.curves = {
            "XYZ": None,
            "X": None,
            "Y": None,
            "Z": None,
            "M": None
        }
        self.cursors = {}
        self.cursor_positions = {
            name: [None, None, None, None]
            for name in self.graphs
        }
        for name, graph in self.graphs.items():
            cursor1 = pg.InfiniteLine(
                angle=90,
                movable=True,
                pen=pg.mkPen("b", width=2)
            )
            cursor2 = pg.InfiniteLine(
                angle=90,
                movable=True,
                pen=pg.mkPen("r", width=2)
            )
            graph.addItem(cursor1)
            graph.addItem(cursor2)
            cursor1.setVisible(False)
            cursor2.setVisible(False)
            cursor1.sigPositionChanged.connect(lambda line=cursor1, n=name: self.cursor_moves(line, n, 0))
            cursor2.sigPositionChanged.connect(lambda line=cursor2, n=name: self.cursor_moves(line, n, 1))
            self.cursors[name] = [cursor1, cursor2]
        for name, cursors in self.cursors.items():
            for i, cursor in enumerate(cursors):
                cursor.sigPositionChanged.connect(lambda line=cursor, n=name, idx=i: self.sync_cursors(line, n, idx))
        for name, graph in self.graphs.items():
            graph.scene().sigMouseClicked.connect(lambda event, n=name: self.on_graph_clicked(event, n))

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
                # self.x2_limit.setText(str(len(self.acceleretion_data[0]) - 1))
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

    def clear_graph(self, graph_name):
        graph = self.graphs[graph_name]
        graph.clear()
        for cursor in self.cursors[graph_name]:
            graph.addItem(cursor)
            cursor.setVisible(False)
        self.cursor_positions[graph_name] = [None, None, None, None]

    def update_graph(self):
        for name in self.graphs:
            self.clear_graph(name)
        
        if len(self.acceleretion_data[0]) > 0 and len(self.acceleretion_data[1]) > 0 and len(self.acceleretion_data[2]) > 0:
            self.graph.plot(self.x[:len(self.acceleretion_data[0])], self.acceleretion_data[0], pen=pg.mkPen(color="red", width=3), name="X-axis")
            self.graph.plot(self.x[:len(self.acceleretion_data[1])], self.acceleretion_data[1], pen=pg.mkPen(color="green", width=3), name="Y-axis")
            self.graph.plot(self.x[:len(self.acceleretion_data[2])], self.acceleretion_data[2], pen=pg.mkPen(color="blue", width=3), name="Z-axis")
            
            curve_x = self.x_graph.plot(self.x[:len(self.acceleretion_data[0])], self.acceleretion_data[0], pen=pg.mkPen(color="red", width=3), name="X-axis")
            curve_y = self.y_graph.plot(self.x[:len(self.acceleretion_data[1])], self.acceleretion_data[1], pen=pg.mkPen(color="green", width=3), name="Y-axis")
            curve_z = self.z_graph.plot(self.x[:len(self.acceleretion_data[2])], self.acceleretion_data[2], pen=pg.mkPen(color="blue", width=3), name="Z-axis")
            
            module = np.sqrt(self.acceleretion_data[0]**2 + self.acceleretion_data[1]**2 + self.acceleretion_data[2]**2)
            curve_m = self.module_graph.plot(self.x[:len(module)], module, pen=pg.mkPen(color="#00a67a", width=3), name="Module")
            # self.a1_limit.setText(str(min(module)))
            # self.a2_limit.setText(str(max(module)))
            
            self.graph.setXRange(0, len(module) - 1)
            self.graph.setYRange(min(min(self.acceleretion_data[0]), min(self.acceleretion_data[1]), min(self.acceleretion_data[2])), max(max(self.acceleretion_data[0]), max(self.acceleretion_data[1]), max(self.acceleretion_data[2])))
            self.module_graph.setXRange(0, len(module) - 1)
            self.module_graph.setYRange(min(module), max(module))
            
            self.curves = {
                "XYZ": [curve_x, curve_y, curve_z],
                "X": [curve_x],
                "Y": [curve_y],
                "Z": [curve_z],
                "M": [curve_m]
            }
    
    def change_cursor_x1(self):
        if is_float(self.x1.text()):
            self.cursor_x_changed(self.choose_graph.currentData(), float(self.x1.text().replace(",", ".")), 0)
    def change_cursor_x2(self):
            if is_float(self.x2.text()):
                self.cursor_x_changed(self.choose_graph.currentData(), float(self.x2.text().replace(",", ".")), 1)

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

    def get_y_text(self, graph_name, cursor_index):
        s = ""
        y_m = []
        if self.curves[graph_name] != None and self.cursor_positions[graph_name][cursor_index] != None:
            if graph_name == "XYZ":
                m = []
                for curve in self.curves[graph_name]:
                    x_data, y_data = curve.getData()
                    if x_data is None or len(x_data) == 0:
                        continue
                    
                    y = np.interp(self.cursor_positions[graph_name][cursor_index], x_data, y_data)
                    y_m.append(y)
                    m.append(round(y, 5))
                s = f"Y{cursor_index + 1}: X-axis: {m[0]}\nY-axis: {m[1]}\nZ-axis: {m[2]}"
            else:
                x_data, y_data = self.curves[graph_name][0].getData()
                if not (x_data is None or len(x_data) == 0):   
                    y = np.interp(self.cursor_positions[graph_name][cursor_index], x_data, y_data)
                    y_m.append(y)
                    s = f"Y{cursor_index + 1}: {round(y, 5)}"
        return s, y_m

    def show_cursor_info(self, graph_name, y1_text, y2_text):
        x1 = self.cursor_positions[graph_name][0]
        y1 = self.cursor_positions[graph_name][2]
        x2 = self.cursor_positions[graph_name][1]
        y2 = self.cursor_positions[graph_name][3]

        index = self.choose_graph.findData(graph_name)
        if index != -1:
            self.choose_graph.setCurrentIndex(index)
        if x1 != None:
            self.x1.show()
            self.x1_label.show()
            self.x1.setText(str(round(x1, 5)))
            self.y1.setText(y1_text)
            self.y1.show()
        else:
            self.x1.hide()
            self.x1_label.hide()
            self.y1.hide()
        if x2 != None:
            self.x2.show()
            self.x2_label.show()
            self.x2.setText(str(round(x2, 5)))
            self.y2.setText(y2_text)
            self.y2.show()
        else:
            self.x2.hide()
            self.x2_label.hide()
            self.y2.hide()
        if x1 != None and x2 != None:
            s = f"Delta X: {abs(round(x1 - x2, 5))} | Delta Y: "
            if len(y1) == 1:
                s += f"{round(abs(y1[0] - y2[0]), 5)}"
            else:
                s += f"x-axis {round(abs(y1[0] - y2[0]), 5)}, y-axis {round(abs(y1[1] - y2[1]), 5)}, z-axis {round(abs(y1[2] - y2[2]), 5)}"
            self.delta.setText(s)
            self.delta.show()
        else:
            self.delta.hide()
                
    def cursor_x_changed(self, graph_name, x, cursor_id):
        self.cursor_positions[graph_name][cursor_id] = x
        y = self.get_y_text(graph_name, cursor_id)[1]
        self.cursor_positions[graph_name][cursor_id + 2] = y
        
        self.cursors[graph_name][cursor_id].setPos(x)
        self.cursors[graph_name][cursor_id].setVisible(True)
        
        self.show_cursor_info(graph_name, self.get_y_text(graph_name, 0)[0], self.get_y_text(graph_name, 1)[0])
    
    def on_graph_clicked(self, event, graph_name):
        if self.cursor_mode != 0 and self.show_cursors_checkbox.isChecked():
            if self.cursor_mode != 3:
                if event.button() != Qt.MouseButton.LeftButton:
                    return
            elif event.button() != Qt.MouseButton.LeftButton and event.button() != Qt.MouseButton.RightButton:
                return

            graph = self.graphs[graph_name]
            view_box = graph.getViewBox()

            mouse_pos = event.scenePos()

            if not view_box.sceneBoundingRect().contains(mouse_pos):
                return

            x = view_box.mapSceneToView(mouse_pos).x()
            
            cursor_id = 0
            if self.cursor_mode != 3:
                cursor_id = self.cursor_mode - 1
            else:
                cursor_id = 0 if event.button() == Qt.MouseButton.LeftButton else 1
            
            self.cursor_x_changed(graph_name, x, cursor_id)
        
    def cursor_mode_toggled(self):
        btn = self.sender()
        if btn.isChecked():
            self.cursor_mode = 0 if btn.text() == "None" else 1 if btn.text() == "First cursor" else 2 if btn.text() == "Second cursor" else 3
            if self.cursor_mode == 3:
                for graph in self.graphs.values():
                    graph.getPlotItem().setMenuEnabled(False)
            else:
                for graph in self.graphs.values():
                    graph.getPlotItem().setMenuEnabled(True)

    def show_cursors(self):
        if self.show_cursors_checkbox.isChecked():
            for name, positions in self.cursor_positions.items():
                if positions[0] != None:
                    self.cursors[name][0].setVisible(True)
                if positions[1] != None:
                    self.cursors[name][1].setVisible(True)
            self.choose_graph_label.show()
            self.choose_graph.show()
            self.show_cursor_info(self.choose_graph.currentData(), self.get_y_text(self.choose_graph.currentData(), 0)[0], self.get_y_text(self.choose_graph.currentData(), 1)[0])
        else:
            for name, cursors in self.cursors.items():
                for i in cursors:
                    i.setVisible(False)
            self.choose_graph_label.hide()
            self.choose_graph.hide()
            self.x1.hide()
            self.x1_label.hide()
            self.y1.hide()
            self.x2.hide()
            self.x2_label.hide()
            self.y2.hide()
            self.delta.hide()

    def change_cursor_info(self):
        self.show_cursor_info(self.choose_graph.currentData(), self.get_y_text(self.choose_graph.currentData(), 0)[0], self.get_y_text(self.choose_graph.currentData(), 1)[0])

    def cursor_moves(self, cursor, graph_name, cursor_id):
        self.cursor_x_changed(graph_name, cursor.value(), cursor_id)
    
    def sync_cursors(self, cursor, graph_name, cursor_id):
        if not self.sync_cursors_checkbox.isChecked():
            return
        x = cursor.value()
        
        for name, cursors in self.cursors.items():
            if name == graph_name:
                continue
            cursors[cursor_id].setValue(x)
    
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
