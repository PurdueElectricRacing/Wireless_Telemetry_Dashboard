# import pyqtgraph as pg
import random
import numpy as np
import datetime
import time
import sys
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QVBoxLayout, QMainWindow, QApplication, QWidget, \
                            QTabWidget, QPushButton, QGroupBox, QTextBrowser, \
                            QTableWidget, QTableWidgetItem, QInputDialog
from PyQt5.QtCore import QCoreApplication, QThread, QTimer
import pyqtgraph as pg

import CANWebsocketClient


IS_DEBUG = True
DEFAULT_WS_ADDRESS = 'ws://127.0.0.1:5000'
if IS_DEBUG:
    DEFAULT_WS_ADDRESS = 'ws://192.168.10.1:5000'


class MainWindow(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)

        # Define window constants for initilizations
        self.resize(1200, 900)
        self.setWindowTitle('PER Dashboard')
        self.mainLayout = QVBoxLayout()

        # Initalize window areas & layout
        self.tabWidget = QTabWidget()
        self.graphs = MyGraphArea()
        self.rawData = MyRawData()
        self.tabWidget.addTab(self.graphs, "Graphs")
        self.tabWidget.addTab(self.rawData, "Raw Data")

        self.mainLayout.addWidget(self.tabWidget)

        self.setLayout(self.mainLayout)

        self.show()

    # Is called after a raw data frame was parsed and is ready to be
    # displayed on a graph.
    def parsedDataCallback(self, can_frame_data):
        self.graphs.canDataCallback(can_frame_data)

    # Called whenever a raw data frame is recieved from the websocket.
    def rawDataCallback(self, rawData):
        self.rawData.rawDataCallback(rawData)

    # Called whenever new statistics are ready to be displayed
    def updateStatistics(self, ups, buffer_len, bps):
        self.rawData.statisticsCallback(ups, buffer_len, bps)


# Basic graph manager that updates all of the plots with the repsective
# values after they have been parsed from raw data.
class MyGraphArea(pg.GraphicsWindow):
    def __init__(self, parent=None):
        super(MyGraphArea, self).__init__(parent)

        self.plots = {
            'throttle_1': TimePlot(self.addPlot(), 'Throttle_1'),
            'break_1': TimePlot(self.addPlot(), 'Break_1'),
        }

    # Recieve data from main window and find specific graph to update.
    def canDataCallback(self, data):
        if not data['parsed']:
            return
        m_keys = data.keys()
        found_keys = filter(lambda key: key in self.plots, m_keys)
        for key in found_keys:
            newY = data[key]
            newX = time.time()
            plot = self.plots[key]
            plot.addDataPoint(newX, newY)


# Basic line plot object used to plot values in relation to time
# such as throttle and break values.
class TimePlot():
    def __init__(self, plot, title="new plot"):
        self.xData = []
        self.yData = []
        self.myPlot = plot
        self.myPlotData = plot.plot()

        self.myPlot.setTitle(title)
        self.myPlot.setYRange(0, 5000)

    # Add new data point to graph
    def addDataPoint(self, newX, newY):

        # Limit history to 50 datapoints
        self.xData.append(newX)
        self.xData = self.xData[-50:]

        self.yData.append(newY)
        self.yData = self.yData[-50:]

        self.myPlotData.setData(self.xData, self.yData, clear=True)


# Thread used to communicate with websocket server
class WebocketThread(QThread):
    def __init__(self, address):
        super(WebocketThread, self).__init__()

        global IS_DEBUG

        self.buffer = []
        self.client = CANWebsocketClient.CANWebsocketClient(
            self.appendToBuffer,
            self.on_close,
            IS_DEBUG)
        self.address = address
        self.connected = False

    # Begin weboscket worker and start data collection
    def run(self):
        print('Running worker...')
        self.connected = True
        self.client.start(self.address)

    # Called to add data frame to buffer to be read by main
    def appendToBuffer(self, data):
        self.buffer.extend(data)

    # Clear the buffer every time it is read
    def getDataBuffer(self):
        if(len(self.buffer) > 0):
            temp = self.buffer
            self.buffer = []
            return temp
        else:
            return []

    def on_close(self):
        self.connected = False
        pass


# Widged used to display raw CAN data bits
# and connection status.
class MyRawData(QWidget):
    def __init__(self, parent=None):
        super(MyRawData, self).__init__(parent)
        layout = QVBoxLayout()

        self.rawDataTable = QTableWidget(0, 0)
        self.rawDataList = {}

        self.statisticsDisplay = QTextBrowser()

        layout.addWidget(self.createRawDataGroup())
        layout.addWidget(self.createConnectionGroup())

        self.setLayout(layout)

    # Field to display raw data bytes
    def createRawDataGroup(self):
        layout = QVBoxLayout()
        groupBox = QGroupBox("CAN Data")

        self.rawDataTable.verticalHeader().setVisible(False)

        layout.addWidget(self.rawDataTable)

        groupBox.setLayout(layout)
        return groupBox

    # Update raw data fields
    def rawDataCallback(self, raw_data):
        m_id = int(raw_data['id'], 16)

        self.rawDataList[m_id] = raw_data
        sortedDataList = sorted(self.rawDataList)
        # self.rawDataTable.clearContents()

        self.rawDataTable.setRowCount(len(sortedDataList))

        for row_index, data_key in enumerate(sortedDataList):
            raw_data_point = self.rawDataList[data_key]
            message = raw_data_point['message']

            self.rawDataTable.setItem(row_index, 0,
                                      QTableWidgetItem(
                                          '0x' + raw_data_point['id']))

            byte_length = int(raw_data_point['length'])
            if self.rawDataTable.columnCount() - 1 < byte_length:
                self.rawDataTable.setColumnCount(byte_length + 1)
                col_headers = ['ID']
                for i in range(0, byte_length):
                    col_headers.append('Byte ' + str(i))
                self.rawDataTable.setHorizontalHeaderLabels(col_headers)

            for i in range(0, byte_length):
                table_item = QTableWidgetItem(message[i*2: i*2 + 2])

                self.rawDataTable.setItem(row_index, i+1, table_item)

    def updateRawDataTable(self):
        pass

    def createConnectionGroup(self):
        layout = QVBoxLayout()
        groupBox = QGroupBox("Connection Info")

        layout.addWidget(self.statisticsDisplay)

        groupBox.setLayout(layout)
        return groupBox

    def sizeof_fmt(self, num, suffix='B'):
        for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)

    def statisticsCallback(self, ups, buffer_len, bps):
        text = 'Updates Per Second: ' + str(ups) + '\n'
        text = text + 'Buffer Length: ' + str(buffer_len) + '\n'
        text = text + 'Datarate : ' + self.sizeof_fmt(bps) + '/s\n'
        self.statisticsDisplay.setPlainText(text)

app = QApplication([])
window = MainWindow()

last_update_time = time.time()
update_counter = 0
ups = 0
size_data_rx = 0
bytes_per_second = 0

websocketThread = WebocketThread(DEFAULT_WS_ADDRESS)
websocketThread.start()


def update():
    global websocketThread

    if websocketThread.connected:
        global last_update_time, update_counter, ups, window
        global bytes_per_second, size_data_rx
        update_counter = update_counter + 1

        current_time = time.time()
        delta_time = current_time - last_update_time

        buffer = websocketThread.getDataBuffer()
        buffer_len = len(buffer)

        if delta_time > 1:
            last_update_time = current_time

            ups = update_counter
            update_counter = 0

            bytes_per_second = size_data_rx
            size_data_rx = 0

        window.updateStatistics(ups, buffer_len, bytes_per_second)

        if buffer_len > 0:
            for data in buffer:
                if data:
                    size_of_data = sys.getsizeof(str(data))
                    size_data_rx = size_data_rx + size_of_data
                    window.rawDataCallback(data)

                can_frame_data = CANWebsocketClient.parseRawMessage(data)
                if can_frame_data and can_frame_data['parsed']:
                    window.parsedDataCallback(can_frame_data)
            app.processEvents()  # force complete redraw for every plot
    else:
        address, result = QInputDialog.getText(window, 'Disconnected',
                                               'Enter WS address',
                                               text=DEFAULT_WS_ADDRESS)
        if result:
            websocketThread = WebocketThread(address)
            websocketThread.start()
        else:
            sys.exit()


timer = QTimer()
timer.timeout.connect(update)
timer.start(0)

app.exec_()
