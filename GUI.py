import matplotlib.pyplot as plt
from numpy import average
#prefined imports
import sys,os,time
from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QPushButton,QWidget,QGridLayout,
                             QSizePolicy,QComboBox,QLineEdit,QTextEdit,
                             QMessageBox,QInputDialog,QMainWindow,QAction
                             ,QDockWidget,QTableWidgetItem,QVBoxLayout,
                             QFileDialog)
from matplotlib.backends.qt_compat import QtWidgets
from matplotlib.backends.backend_qt5agg import (
    FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure

from PyQt5.QtGui import QFont,QIcon, QImage, QPalette, QBrush
from PyQt5.QtCore import Qt

class Monitor(QMainWindow):
    '''GUI for use in monitoring the life a a better cell by 
    means of a RPi 3b and a ADS 1015
    '''
    def __init__(self,*kwargs):
        super().__init__()
        self.size_policy=QSizePolicy.Expanding
        self.font=QFont()
        self.font.setPointSize(12)
        self.showMaximized()
        self.setWindowIcon(QIcon('RSIL_Logo.png'))
        self.setWindowTitle('Battery Monitor')
        self.showMaximized()
        self.init()
        
        self.menu_bar()
    def init(self):
        self.polling_frequency=QComboBox(self)
        self.polling_frequency.setSizePolicy(self.size_policy,self.size_policy)
        self.polling_frequency.setFont(self.font)
        self.polling_frequency.setToolTip(
                'Timing between data samples in seconds')
        self.polling_frequency.addItems(['1','5','10','15','30','60','120'])
        
        self.run_time=QLineEdit(self)
        self.run_time.setSizePolicy(self.size_policy,self.size_policy)
        self.run_time.setFont(self.font)
        self.run_time.setReadOnly(True)
        self.run_time.setToolTip('Total run time')
        
        self.start=QPushButton('Start',self)
        self.start.setSizePolicy(self.size_policy,self.size_policy)
        self.start.setFont(self.font)
        self.start.setToolTip(
                'Starts monitoring the battery\nlife and recoring data')
        self.start.clicked.connect(self.begin_timing)
        self.start.setEnabled(False)
        
        self.pause=QPushButton('Pause',self)
        self.pause.setSizePolicy(self.size_policy,self.size_policy)
        self.pause.setFont(self.font)
        self.pause.setToolTip(
                'Pauses both recording and monitoring of voltage')
        self.pause.clicked.connect(self.pausing)
        self.pause.setEnabled(False)
        
        self.resume=QPushButton('Resume',self)
        self.resume.setSizePolicy(self.size_policy,self.size_policy)
        self.resume.setFont(self.font)
        self.resume.setToolTip('Resumes monitoring and recording of voltage')
        self.resume.clicked.connect(self.resuming)
        self.resume.setEnabled(False)
        
        self.browse=QPushButton('Browse',self)
        self.browse.setSizePolicy(self.size_policy,self.size_policy)
        self.browse.setFont(self.font)
        self.browse.setToolTip('Browse for the file to store data in')
        self.browse.clicked.connect(self.file_location)
        
        self.layout=QGridLayout()
        self.layout.addWidget(self.polling_frequency,0,0)
        self.layout.addWidget(self.browse,1,0)
        self.layout.addWidget(self.run_time,0,1)
        self.layout.addWidget(self.start,2,0)
        self.layout.addWidget(self.pause,1,1)
        self.layout.addWidget(self.resume,2,1)
        self.setLayout(self.layout)
        
        layout=QWidget()
        layout.setLayout(self.layout)
        self.setCentralWidget(layout)
        self.show()
        
    def menu_bar(self):
        '''Create the menu bar for the main window will include
                Name:       Shortcut:         Function called:
            File:
                New         CTRL+N            new_invoice_begin
                Open        CTRL+O            existing_invoice_open
                Save        CTRL+S            save_invoice
                Print       CTRL+P            print_invoice
                Quit        ALT+F4            exit_system
        '''        
        self.menuFile = self.menuBar().addMenu("&File")
        self.actionNew=QAction('&New',self)
        self.actionNew.setShortcut('Ctrl+N')
#        self.actionNew.triggered.connect(self.new_invoice_begin)        
        self.actionQuit=QAction('&Exit',self)
#        self.actionQuit.triggered.connect(self.exit_system)
        self.actionQuit.setShortcut('Alt+F4')
        self.menuFile.addActions([self.actionNew,
                                  self.actionQuit])
    def begin_timing(self):
        '''Start collectign data from the ADC and start the timer'''
        self.start.setDisabled(True)
        self.pause.setEnabled(True)
        delay=int(self.polling_frequency.currentText())
        self.acquisition=Data_Acquisition(delay,time.time(),self.file_path)
        self.acquisition.start()
#        self.acquisition.value.connect(self.value)
        self.acquisition.timing.connect(self.run_time.setText)
        
    def pausing(self):
        self.pause.setDisabled(True)
        self.resume.setEnabled(True)
        self.acquisition.running=False
        
    def resuming(self):
        self.pause.setDisabled(False)
        self.resume.setEnabled(False)
        prior_delta=self.acquisition.delta
        delay=int(self.polling_frequency.currentText())
        self.acquisition=Data_Acquisition(delay,time.time()-prior_delta-delay,self.file_path)
        self.acquisition.start() 
        self.acquisition.timing.connect(self.run_time.setText)
        
    def file_location(self):
        file_path,name=QFileDialog.getSaveFileName(self,'File name',os.getcwd(),"Text File(*.txt);; Comma Delimited (*.csv)")
        self.file_path=str(Path(file_path))
        self.start.setEnabled(True)
            
class Data_Acquisition(QThread):
#    value=pyqtSignal(str)
    timing=pyqtSignal(str)
    def __init__(self,polling_rate,start_time,file_location,parent=None):
        QThread.__init__(self, parent=parent)
        self.polling_rate=polling_rate
        self.start_time=start_time
        self.file_location=file_location
        self.running=True
        
    def run(self):
        if os.path.exists(self.file_location):
            f=open(self.file_location,'a')
        else:
            f=open(self.file_location,'w')
        moving=5*[5]
        loc=0
        while self.running and average(moving)>4:
            self.delta=time.time()-self.start_time
#            self.value.emit(adc.read_difference(0,2/3))
            self.value=1
            moving[loc]=self.value
            loc+=1
            if loc==4:
                loc=0
            self.timing.emit('{:.4f}'.format(self.delta))
            f.write('{:.4f},{:.4f}\n'.format(self.delta,self.value))
            time.sleep(self.polling_rate)
#            PlotCanvas(self.value, self.delta)
        f.close()
        
        
class PlotCanvas(QtWidgets.QMainWindow):
    def __init__(self,x_point,y_point,x_axis=[],y_axis=[]):
        super(PlotCanvas, self).__init__()
        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)
        layout = QtWidgets.QVBoxLayout(self._main)
        
        static_canvas = FigureCanvas(Figure(figsize=(5, 3)))
        layout.addWidget(static_canvas)
        self.addToolBar(NavigationToolbar(static_canvas, self))
        x_axis.append(x_point)
        y_axis.append(y_point)

        self.plots = static_canvas.figure.subplots()
        self.plots.clear()
        self.plots.plot(x_axis, y_axis, "m")
        self.plots.set_xlabel('Time[s]')
        self.plots.set_ylabel('Voltage')
        self.plots.set_title('Battery Current Voltage')
        self.plots.figure.canvas.draw()
        self.show()
        
if __name__=="__main__":
    app=QApplication(sys.argv)
    ex=Monitor()
    sys.exit(app.exec_())        