import sys
import typing
from typing import Any
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtGui import QPixmap, QPainter,QBrush,QColor
from PyQt5.QtCore import QDateTime, pyqtSignal, QTimer, QObject, pyqtSlot, QRunnable,QThreadPool, Qt
from PyQt5.QtWidgets import QWidget, QApplication, QFileDialog, QListWidgetItem, QWidgetItem, QLineEdit, QVBoxLayout,QRadioButton,QMessageBox
import numpy as np
import textwrap
import time
import multiprocessing
from multiprocessing import Process, Queue
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib
import serial
import pyqtgraph as pg
import serial.tools.list_ports
import os
from math import exp
import csv
#import psycopg2
import http.client as httplib
from datetime import datetime, timedelta
matplotlib.use('Qt5Agg')

import time
import serial
import serial.tools.list_ports
import os
import csv
from datetime import datetime, timedelta

import RPi.GPIO as GPIO


class InitWindow(QtWidgets.QMainWindow):
    def __init__(self, app_manager):
        super(InitWindow,self).__init__()
        uic.loadUi(r'init.ui', self)
        self.app_manager = app_manager

        self.toolButton_start.clicked.connect(self.start)
        self.closingProgrammatically = False
    
    def closeEvent(self,event):
        if event.isAccepted() and not self.closingProgrammatically:
            self.app_manager.testToRun = 'exit'
    def start(self):
        arduino_ports = [
        p.device
        for p in serial.tools.list_ports.comports()
        if 'ttyACM0' in p.description]
        if not arduino_ports:
            QMessageBox.about(self, "Warning", "Connect hardware to proceed")
        else:
            self.app_manager.testToRun = 'target'
            self.closingProgrammatically = True
            self.close()

class TargetWindow(QtWidgets.QMainWindow):
    def __init__(self, app_manager):
        super(TargetWindow,self).__init__()
        uic.loadUi(r'target.ui', self)
        self.app_manager = app_manager
        self.closingProgrammatically = False
        self.date = None
        self.start_time=None
        self.completename=None
        self.timer_temp=None
        self.timer_saveData=None
        self.arduino=None
        self.temp_mortar=None
        self.temp_water=None
        self.target=None
        self.power=None
        self.time=[]
        self.time_ADC=[]
        self.Cell_1_list=[]
        self.Cell_2_list=[]
        #self.Cell_3_list=[]
        #self.Cell_4_list=[]
        self.Cell_1_Temporary_list=[]
        self.Cell_2_Temporary_list=[]
        #self.Cell_3_Temporary_list=[]
        #self.Cell_4_Temporary_list=[]
        self.Cell_1=None
        self.Cell_2=None
        #self.Cell_3=None
        #self.Cell_4=None
        self.Cell_1_avg=None
        self.Cell_2_avg=None
        #self.Cell_3_avg=None
        #self.Cell_4_avg=None
        self.temp_mortar_list=[]
        self.temp_water_list=[]
        self.target_list=[]
        self.current_datetime = None
        self.time_elapsed=None
        self.graph_water.setTitle("Temperatures", size="18pt",color="black")
        self.graph_water.setLabel("left", "Temperature (°C)",color="grey")
        self.graph_water.setLabel("bottom", "Time (hour)",color="grey")
        self.graph_water.addLegend()
        self.graph_water.setBackground("w")
        self.graph_power.setTitle("Heat flux", size="18pt",color="black")
        self.graph_power.setLabel("left", "ADC value",color="grey")
        self.graph_power.setLabel("bottom", "Time (hour)",color="grey")
        self.graph_power.addLegend()
        self.graph_power.setBackground("w")
        pen=pg.mkPen(color=(0, 0, 155))
        self.line_1=self.graph_water.plot(self.time, self.temp_water_list,name="Water",pen=pen)
        pen=pg.mkPen(color=(0, 155, 0))
        self.line_2=self.graph_water.plot(self.time, self.temp_mortar_list,name="Mortar",pen=pen)
        pen=pg.mkPen(color=(255, 0, 0),style=QtCore.Qt.DashLine)
        self.line_3=self.graph_water.plot(self.time, self.target_list,name="Target",pen=pen)
        pen=pg.mkPen(color=(8,199,247)) #blue
        self.line_4=self.graph_power.plot(self.time, self.Cell_1_list,name="Cell 1",pen=pen)
        pen=pg.mkPen(color=(49,193,16)) #green
        self.line_5=self.graph_power.plot(self.time, self.Cell_2_list,name="Cell 2",pen=pen)
       # pen=pg.mkPen(color=(240,78,54)) #red
        #self.line_6=self.graph_power.plot(self.time, self.Cell_3_list,name="Cell 3",pen=pen)
        #pen=pg.mkPen(color=(243,212,48)) #yellow
        #self.line_7=self.graph_power.plot(self.time, self.Cell_4_list,name="Cell 4",pen=pen)
        self.toolButton_start.clicked.connect(self.start)
        self.toolButton_stop.clicked.connect(self.stop)
        self.nameExtension=None
        self.GapOrTarget=None
        self.radioButton_Static.toggled.connect(self.static_test)
        self.radioButton_calibration.toggled.connect(self.calibration)
        self.radioButton_ramp.toggled.connect(self.ramp)
        self.doubleSpinBox_Static.valueChanged.connect(self.static_update)
        self.radioButton_Matching.toggled.connect(self.matching_test)
        self.doubleSpinBox_Matching.valueChanged.connect(self.matching_update)
        #self.toolButton_stop.setEnabled(False)

    def start(self):
        if not self.radioButton_Matching.isChecked() and not self.radioButton_Static.isChecked() and not self.radioButton_calibration.isChecked() and not self.radioButton_ramp.isChecked():
            QMessageBox.about(self, "Warning", "Select test type to proceed")
        else:
            arduino_ports = [
            p.device
            for p in serial.tools.list_ports.comports()
            if 'ttyACM0' in p.description]
            self.arduino = serial.Serial(arduino_ports[0])
            self.arduino.baudrate = 9600  # set Baud rate to 9600
            self.arduino.bytesize = 8   # Number of data bits = 8
            self.arduino.parity  ='N'   # No parity.SerialObj.stopbits = 1
            self.date = time.strftime("%Y-%m-%d-%H-%M-%S")
            self.start_time=time.time() 
            self.completename=os.path.join(self.date+"_"+self.nameExtension+"_"+str(self.GapOrTarget)+".csv")
            self.timer_temp=QTimer()
            self.timer_temp.setInterval(2000)
            self.timer_temp.timeout.connect(self.readTemp)
            self.timer_temp.start()
            self.timer_saveData=QTimer()
            self.timer_saveData.setInterval(20000)
            self.timer_saveData.timeout.connect(self.save_data)
            self.timer_saveData.start()
            time.sleep(1)
            if self.radioButton_Matching.isChecked():
                self.arduino.write(f"M{self.GapOrTarget:.2f}\n".encode('utf-8'))
            elif self.radioButton_Static.isChecked():
                self.arduino.write(f"S{self.GapOrTarget:.2f}\n".encode('utf-8')) 
            elif self.radioButton_calibration.isChecked():
                self.arduino.write(f"C\n".encode('utf-8')) 
            elif self.radioButton_ramp.isChecked():
                self.arduino.write(f"P\n".encode('utf-8')) 

    def stop(self):
        self.timer_temp.stop()
        self.timer_saveData.stop()
        self.toolButton_stop.setEnabled(False)
        self.toolButton_start.setEnabled(True)

    def calibration(self):
        self.date = time.strftime("%Y-%m-%d-%H-%M-%S")
        self.nameExtension="Calibration"
        if self.arduino is not None:
            self.arduino.write(f"C\n".encode('utf-8')) 
        self.doubleSpinBox_Static.setDisabled(True)
        self.doubleSpinBox_Matching.setDisabled(True)

    def ramp(self):
        self.date = time.strftime("%Y-%m-%d-%H-%M-%S")
        self.nameExtension="Ramp"
        if self.arduino is not None:
            self.arduino.write(f"P\n".encode('utf-8')) 
        self.doubleSpinBox_Static.setDisabled(True)
        self.doubleSpinBox_Matching.setDisabled(True)

    def static_test(self):
        self.date = time.strftime("%Y-%m-%d-%H-%M-%S")
        self.nameExtension="Static"
        self.GapOrTarget=self.doubleSpinBox_Static.value()
        if self.arduino is not None:
            self.arduino.write(f"S{self.GapOrTarget:.2f}\n".encode('utf-8')) 
        self.doubleSpinBox_Static.setDisabled(False)
        self.doubleSpinBox_Matching.setDisabled(True)

    def static_update(self):
        self.date = time.strftime("%Y-%m-%d-%H-%M-%S")
        self.GapOrTarget=self.doubleSpinBox_Static.value()
        self.arduino.write(f"S{self.GapOrTarget:.2f}\n".encode('utf-8')) 

    def matching_test(self):
        self.date = time.strftime("%Y-%m-%d-%H-%M-%S")
        self.nameExtension="Matching"
        self.GapOrTarget=self.doubleSpinBox_Matching.value()
        if self.arduino is not None:
            self.arduino.write(f"M{self.GapOrTarget:.2f}\n".encode('utf-8')) 
        self.doubleSpinBox_Static.setDisabled(True)
        self.doubleSpinBox_Matching.setDisabled(False)

    def matching_update(self):
        self.date = time.strftime("%Y-%m-%d-%H-%M-%S")
        self.GapOrTarget=self.doubleSpinBox_Matching.value()
        if self.arduino is not None:
            self.arduino.write(f"M{self.GapOrTarget:.2f}\n".encode('utf-8')) 

    def readTemp(self):
        self.arduino.write(b'R\n') #sends a request
        received_data = self.arduino.readline().decode('utf-8').strip()
        variables = received_data.split(',')
        self.temp_mortar=float(variables[0])
        self.temp_water=float(variables[1])
        self.target=float(variables[2])
        self.power=float(variables[3])
        self.Cell_1=float(variables[4])
        self.Cell_1_Temporary_list.append(self.Cell_1)
        self.Cell_2=float(variables[5])
        self.Cell_2_Temporary_list.append(self.Cell_2)
        if len(self.Cell_1_Temporary_list)>10:
            self.Cell_1_Temporary_list=self.Cell_1_Temporary_list[1:]
            self.Cell_2_Temporary_list=self.Cell_2_Temporary_list[1:]
        print(self.Cell_1_Temporary_list[0])
        print(self.Cell_2_Temporary_list[0])
        print(len(self.Cell_1_Temporary_list))
        self.update_plot_water()
    
    def update_plot_water(self):
        self.label_target.setText('Target = '+str(self.target)+' ºC')
        self.label_mortar.setText('Mortar temperature = '+str(self.temp_mortar)+' ºC')
        self.label_power.setText('Water = '+str(self.temp_water)+' ºC')
        if len(self.time)==0:
            self.time.append(2/3600)
        else:
            self.time.append(self.time[-1] + (2/3600))
        self.temp_mortar_list.append(self.temp_mortar)
        self.temp_water_list.append(self.temp_water)
        self.target_list.append(self.target)
        if len(self.time)>=18000:
            self.time = self.time[1:]
            self.temp_mortar_list=self.temp_mortar_list[1:]
            self.temp_water_list=self.temp_water_list[1:]
            self.target_list=self.target_list[1:]
        self.line_1.setData(self.time, self.temp_water_list)
        self.line_2.setData(self.time, self.temp_mortar_list)
        self.line_3.setData(self.time, self.target_list)
        #self.graph.setYRange(20, 105)

    def update_plot_ADC(self):
        if len(self.time)>=18000:
            self.Cell_1_list = self.Cell_1_list[1:]
            self.Cell_2_list=self.Cell_2_list[1:]
        self.time_ADC.append(self.time[-1])
        self.line_4.setData(self.time_ADC, self.Cell_1_list)
        self.line_5.setData(self.time_ADC, self.Cell_2_list)

        #self.line_6.setData(self.time_ADC, self.Cell_3_list)
        # self.line_7.setData(self.time_ADC, self.Cell_4_list)
    
    def save_data(self):
        self.current_datetime = datetime.now()
        self.time_elapsed=time.time()-self.start_time
        self.Cell_1_avg=(np.mean(self.Cell_1_Temporary_list))
        self.Cell_2_avg=(np.mean(self.Cell_2_Temporary_list))
        #self.Cell_3_avg=int(np.mean(self.Cell_3_Temporary_list))
        #self.Cell_4_avg=int(np.mean(self.Cell_4_Temporary_list))
        self.Cell_1_list.append(self.Cell_1_avg)
        self.Cell_2_list.append(self.Cell_2_avg)
        #self.Cell_3_list.append(self.Cell_3_avg)
        #self.Cell_4_list.append(self.Cell_4_avg)
        self.update_plot_ADC()
        with open(self.completename, 'a') as csvFile:
            fieldnames=['Date','elapsed_time', 'Temp_outside','Temp_water','Target', 'Power_supplied','Cell_1', 'Cell_2']
            writer = csv.DictWriter(csvFile, fieldnames=fieldnames)
            writer.writerow({'Date': self.current_datetime,'elapsed_time':self.time_elapsed, 'Temp_outside' : self.temp_mortar,'Temp_water': self.temp_water, 'Target':self.target, 'Power_supplied':self.power,'Cell_1':self.Cell_1_avg, 'Cell_2' : self.Cell_2_avg})
        csvFile.close()
    
    def closeEvent(self,event):
        if event.isAccepted() and not self.closingProgrammatically:
            self.app_manager.testToRun = 'exit'

class ApplicationManager:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.testToRun = 'init'
        self.Init_window=None
        self.target_window=None

    def run(self):
            while True:
                if self.testToRun == 'init':
                    self.Init_window = InitWindow(self)
                    self.Init_window.show()
                    self.app.exec_()
                elif self.testToRun == 'exit':
                    self.app.quit()
                    break
                
                elif self.testToRun == 'target':
                    self.mould_freq_window = TargetWindow(self)
                    self.mould_freq_window.show()
                    self.app.exec_()

if __name__ == "__main__":
    app_manager = ApplicationManager()
    app_manager.run()