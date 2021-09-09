import csv
import os
import psutil
import time
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import QPropertyAnimation, QRectF, QSize, Qt, pyqtProperty
from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLCDNumber, QSlider, QVBoxLayout)
from matplotlib.figure import Figure
import sys
from PyQt5 import QtGui, QtSerialPort, QtCore
from PyQt5 import QtWidgets
from qtwidgets import AnimatedToggle
from PyQt5.QtCore import QObject, QSize, QPointF, QPropertyAnimation, QEasingCurve, pyqtProperty, pyqtSlot, QThread, pyqtSignal, QRectF, QPoint
from PyQt5.QtGui import QPainter, QPalette, QLinearGradient, QGradient
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QLabel
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import numpy as np
from PyQt5.QtCore import Qt
from datetime import datetime
import folium
from PyQt5.QtWebEngineWidgets import QWebEngineView
import io
import cv2
import matplotlib
matplotlib.use('Qt5Agg')
 
 
tim = []
data = []
 
file = open("data.csv", "w+")
if os.stat("data.csv").st_size == 0:
    file.write("Time,Altitude\n")
 
 
class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
 
    def run(self):
        # capture from web cam
        cap = cv2.VideoCapture(0)
        while True:
            ret, cv_img = cap.read()
            cv_img = cv2.flip(cv_img, 1)
            if ret:
                self.change_pixmap_signal.emit(cv_img)
 
 
class Battery(QtWidgets.QWidget):
    def setBP(self):
        self.progressBar.setProperty("value", psutil.sensors_battery().percent)
 
 
    def setupUi(self, Form):
        # self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        # self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        # self.verticalLayout.setSpacing(0)
        # self.verticalLayout.setAlignment(QtCore.Qt.AlignTop)
        # self.verticalLayout.setObjectName("verticalLayout")
        self.progressBar = QtWidgets.QProgressBar(Form)
        self.progressBar.setMaximumSize(QtCore.QSize(16777215, 20))
        #self.progressBar.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                     #  QtWidgets.QSizePolicy.Fixed)
        self.progressBar.setStyleSheet("QProgressBar{\n"
                                       "background-color:rgba(0,0,0,0);\n"
                                       "border:solid 3px red;\n"
                                       "}\n"
                                       "QProgressBar:chunk{\n"
                                       "background-color:rgba(61,174,233,240);\n"
                                       "}\n"
                                       "")
        self.progressBar.setProperty("value", psutil.sensors_battery().percent)
        self.progressBar.setTextVisible(True)
        self.progressBar.setMaximum(100)
        self.progressBar.setMinimum(0)
        self.progressBar.setObjectName("progressBar")
        #self.verticalLayout.addWidget(self.progressBar)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.setBP)
        self.timer.start(1000)
        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
 
    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
 
 
class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DAS")
        
        
        self.resize(1920, 1080)
        #self.setFixedHeight(1000)
        #self.setFixedWidth(1200)
        # Create a top-level layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        # Create the tab widget with two tabs
        tabs = QTabWidget()
        
        #layout.addWidget(self.battery)
        tabs.addTab(self.DashboardUI(), "Dashboard")
        tabs.addTab(self.networkTabUI(), "Playback")
        layout.addWidget(tabs)
        
    def DashboardUI(self):
        """Create the General page UI."""
        generalTab = QWidget()
        self.battery = Battery()
        self.battery.setupUi(generalTab)
        outerLayout = QVBoxLayout()
        toplayout = QHBoxLayout()
        bottomlayout = QVBoxLayout()
 
        fpvfeed = FpvFeed()
        fpvfeed.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                              QtWidgets.QSizePolicy.MinimumExpanding)
        toplayout.addWidget(fpvfeed)
 
        map = Map()
        bottomlayout.addWidget(map)
 
        altitude = Altitude()
        altitude.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                               QtWidgets.QSizePolicy.MinimumExpanding)
        toplayout.addWidget(altitude)
 
        
        # pybutton.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
        # QtWidgets.QSizePolicy.Fixed)
 
        outerLayout.addLayout(toplayout)
        outerLayout.addLayout(bottomlayout)
        self.setLayout(outerLayout)
        generalTab.setLayout(outerLayout)
        return generalTab
 
    def networkTabUI(self):
        """Create the Network page UI."""
        sc = MPLCanvas(self, width=5, height=4, dpi=100)
        #print(tim,data)
        self.battery = Battery()
        
        sc.axes.plot(tim, data)
        toolbar = NavigationToolbar(sc, self)
        layout = QVBoxLayout()
 
        update_button = QPushButton(text="Update")
        update_button.clicked.connect(self.networkTabUI)
 
        layout.addWidget(toolbar)
        layout.addWidget(sc)
        layout.addWidget(update_button)
 
        widget = QtWidgets.QWidget()
        self.battery.setupUi(widget)
        widget.setLayout(layout)
        return widget
 
    def closeEvent(self, event):
        file.close()
        return super().closeEvent(event)
 
 
class MPLCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MPLCanvas, self).__init__(fig)
 
 
class FpvFeed(QWidget):
    def __init__(self):
        super().__init__()
        self.disply_width = 640
        self.display_height = 480
        # create the label that holds the image
        self.image_label = QLabel(self)
        self.image_label.resize(self.disply_width, self.display_height)
 
        # create a vertical box layout and add the two labels
        vbox = QVBoxLayout()
        vbox.addWidget(self.image_label)
        # set the vbox layout as the widgets layout
        self.setLayout(vbox)
        release = QVBoxLayout()
 
        toggle = ToggleSwitch()
 
        release.addWidget(toggle)
        vbox.addLayout(release)
 
        pybutton = QPushButton('PADA release', self)
        pybutton.styleSheet
        pybutton.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                               QtWidgets.QSizePolicy.MinimumExpanding)
        release.addWidget(pybutton)
        #fpvfeed.setStyleSheet("border: 3px solid red;")
        vbox.addLayout(release)
        # create the video capture thread
        self.thread = VideoThread()
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.thread.start()
 
    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.image_label.setPixmap(qt_img)
 
    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(
            rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(
            640, 480, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)
 
 
class Map(QWidget):
    def __init__(self):
        super().__init__()
 
        layout = QVBoxLayout()
 
        coordinate = (37.8199286, -122.4782551)
        m = folium.Map(
 
            tiles='Stamen Terrain',
            zoom_start=13,
            location=coordinate
        )
        data = io.BytesIO()
        m.save(data, close_file=False)
 
        webView = QWebEngineView()
        webView.setHtml(data.getvalue().decode())
        layout.addWidget(webView)
        self.setLayout(layout)
 
 
class Indic(QWidget):
    def __init__(self):
        super().__init__()
        
 
class Altitude(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        font = QFont()
        font.setPixelSize(72)
 
        self.lab = QLabel()
        self.lab.setText("Altitude (in ft)")
        self.lab.setFont(font)
        self.lab.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.lab.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                               QtWidgets.QSizePolicy.Fixed)
 
        font.setPointSize(96)
        self.output_te = QtWidgets.QTextEdit(readOnly=True)
        self.output_te.setFont(font)  # displays alt
        self.button = QtWidgets.QPushButton(
            text="Connect",
            checkable=True,
            toggled=self.on_toggled
        )
        lay = QtWidgets.QVBoxLayout(self)
        #hlay = QtWidgets.QHBoxLayout()
        # lay.addLayout(hlay)
        lay.addWidget(self.lab)
        # lay.addWidget(self.lcd)
        lay.addWidget(self.output_te)
        lay.addWidget(self.button)
 
        self.serial = QtSerialPort.QSerialPort(
            'COM3',
            baudRate=QtSerialPort.QSerialPort.Baud9600,
            readyRead=self.receive
        )
 
    @QtCore.pyqtSlot()
    def receive(self):
        while self.serial.canReadLine():
            text = self.serial.readLine().data().decode()
            text = text.rstrip('\r\n')
            self.output_te.clear()
            self.output_te.append(text)
            time = datetime.now().strftime('%H:%M:%S')
            file.write(f"{time},{text}\n")
            tim.append(time)
            data.append(text)
 
    @QtCore.pyqtSlot(bool)
    def on_toggled(self, checked):
        self.button.setText("Disconnect" if checked else "Connect")
        if checked:
            if not self.serial.isOpen():
                if not self.serial.open(QtCore.QIODevice.ReadWrite):
                    self.button.setChecked(False)
        else:
            self.serial.close()
 
 
class ToggleSwitch(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        #app = QApplication([])
        tog = QHBoxLayout()
        secondaryToggle = AnimatedToggle(
            checked_color="#00AA00",
 
        )
        tog.addWidget(secondaryToggle)
        self.setLayout(tog)
        # tog.layout().addWidget(secondaryToggle)
 
 
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())