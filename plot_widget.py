from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QVBoxLayout, QWidget
from qwt import QwtPlot, QwtPlotCurve
import time

class ComboPlot(QWidget):
    def __init__(self, parent=None):
        super(QWidget, self).__init__(parent)
        self.mainLayout = QVBoxLayout()
        self.dataDisplayedCombo = QtWidgets.QComboBox()
        self.dataDisplayedCombo.setCurrentText("")
        self.mainLayout.addWidget(self.dataDisplayedCombo)
        self.dataPlot = QwtPlot()
        self.mainLayout.addWidget(self.dataPlot)
        self.setLayout(self.mainLayout)
        self.dataDisplayedCombo.currentIndexChanged.connect(self.comboChanged)
        self.items = []
        #self.show()
    
    def initPlot(self, title="new plot"):
        self.start_time = time.time()
        self.xData = []
        self.yData = []
        self.dataPlot.detachItems()
        self.curve = QwtPlotCurve(title)
        self.curve.setData(self.xData, self.yData)
        self.curve.attach(self.dataPlot)
        self.dataPlot.replot()
        self.dataPlot.setTitle(title)
    
    def comboUpdate(self, items):
        self.items = items
        self.dataDisplayedCombo.clear()
        self.dataDisplayedCombo.addItems(items)
    
    def comboChanged(self, i):
        self.selection = self.items[i]
        self.initPlot(self.selection)
    
    def updatePlot(self, buffer):
        try:
            if(self.curve):
                self.addDataPoint(buffer.get(self.selection))
        except:
            print("curve not defined yet")

    def addDataPoint(self, newY):
        newX = time.time() - self.start_time
        hist = 1000
        self.xData.append(newX)
        self.xData = self.xData[-hist:]

        self.yData.append(newY)
        self.yData = self.yData[-hist:]

        self.curve.setData(self.xData, self.yData)
        self.dataPlot.replot()
