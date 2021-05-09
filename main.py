import sys
import time

from PyQt5.QtCore import QCoreApplication, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import *
from PyQt5.QtWidgets import (QApplication, QFrame, QGridLayout, QGroupBox,
                             QHBoxLayout, QInputDialog, QMainWindow,
                             QPushButton, QTableWidgetItem, QTabWidget,
                             QTextBrowser, QVBoxLayout, QWidget)
from qwt import QwtPlot, QwtPlotCurve

from Client import CanSocket
from plot_widget import ComboPlot

host = '10.192.17.199'#'169.254.48.90'
port = 28700#29536
dbc_file = 'per_2021_dbc.dbc'

class Window(QWidget):
    key_sig = pyqtSignal(list)
    data_sig = pyqtSignal(dict)
    keys=[]

    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)
        self.resize(1200, 900)
        self.setWindowTitle('PER Dashboard')
        self.vBox = QVBoxLayout()
        self.buttonHBox = QHBoxLayout()
        self.hBox = QHBoxLayout()
        self.buttonFrame = QFrame()
        self.plotFrame = QFrame()
        self.add_button = QPushButton()
        self.add_button.setText("+")
        self.add_button.clicked.connect(self.addPlot)
        self.sub_button = QPushButton()
        self.sub_button.setText("-")
        self.sub_button.clicked.connect(self.subPlot)
        self.buttonHBox.addWidget(self.add_button)
        self.buttonHBox.addWidget(self.sub_button)
        self.buttonFrame.setLayout(self.buttonHBox)
        self.vBox.addWidget(self.buttonFrame)
        #self.vBox.addWidget(self.add_button)
        self.plots = []
        self.addPlot()
        self.addPlot()
        self.plotFrame.setLayout(self.hBox)
        self.vBox.addWidget(self.plotFrame)
        self.setLayout(self.vBox)
        self.show()
        self.key_sig.connect(self.keyChange)
        self.data_sig.connect(self.updateData)
    
    def addPlot(self):
        self.plots.append(ComboPlot())
        self.plots[-1].comboUpdate(self.keys)
        self.hBox.addWidget(self.plots[-1])
    
    def subPlot(self):
        self.plots[-1].close()
        self.plots.pop()
    
    def keyChangeEmit(self, keys):
        self.key_sig.emit(keys)

    def dataChangeEmit(self, buffer):
        self.data_sig.emit(buffer)

    def keyChange(self, keys):
        self.keys = keys
        for plot in self.plots:
            plot.comboUpdate(keys)
    
    def updateData(self, buffer):
        for plot in self.plots:
            plot.updatePlot(buffer)

class WebsocketThread(QThread):

    def __init__(self, dbc, address, combo_update):
        super(WebsocketThread, self).__init__()
        self.buffer = {}
        self.buffer_len = 0
        self.client = CanSocket(dbc)
        self.address = address
        self.combo_update = combo_update
    
    def on_receive(self, data):
        try:
            self.buffer.update(data)
        except:
            print("Buffer update error")
        if(len(self.buffer) != self.buffer_len):
            self.buffer_len = len(self.buffer)
            self.key_update()
        
    def key_update(self):
        print("New items detected")
        self.combo_update(list(self.buffer.keys()))
    
    def getBuffer(self):
        return self.buffer

    def run(self):
        self.client.connect(self.address)
        self.client.start_receiving(self.on_receive)

app = QApplication([])
window = Window()
#window.show()

last_update_time = time.time()
update_counter = 0
ups = 0
size_data_rx = 0
bytes_per_second = 0



websocketThread = WebsocketThread(dbc_file, (host,port), window.keyChangeEmit)
websocketThread.start()
time.sleep(1)

def update():
    global websocketThread

    if websocketThread.client.connected:
        global last_update_time, update_counter, ups, window
        global bytes_per_second, size_data_rx
        update_counter = update_counter + 1

        current_time = time.time()
        delta_time = current_time - last_update_time

        buffer = websocketThread.getBuffer()
        buffer_len = len(buffer)

        if delta_time > 1:
            last_update_time = current_time

            ups = update_counter
            update_counter = 0

            bytes_per_second = size_data_rx
            size_data_rx = 0

        #window.updateStatistics(ups, buffer_len, bytes_per_second)

        if buffer_len > 0:
             window.dataChangeEmit(buffer)
             for data in buffer:
                 if data:
                    #size_of_data = sys.getsizeof(str(data))
                    #size_data_rx = size_data_rx + size_of_data
                    #print(data)
                    #window.rawDataCallback(data)
                    pass

                    #window.parsedDataCallback(can_frame_data)
            #app.processEvents()  # force complete redraw for every plot
    else:
        address, result = QInputDialog.getText(window, 'Disconnected',
                                               'Enter WS address',
                                               text=host)
        if result:
            websocketThread = WebsocketThread(dbc_file, (address, port), window.keyChangeEmit)
            websocketThread.start()
            time.sleep(1)
        else:
            sys.exit()

timer = QTimer()
timer.timeout.connect(update)
timer.start(10)

app.exec_()

        