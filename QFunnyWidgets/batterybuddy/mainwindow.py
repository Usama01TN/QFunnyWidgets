# coding=utf-8
"""
Demo window for BatteryBuddyWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QSlider, QCheckBox, QLabel
from ManyQt.QtCore import Qt, pyqtSlot
from ManyQt.QtGui import QIcon
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .batterybuddy import BatteryBuddyWidget
except:
    from batterybuddy import BatteryBuddyWidget


class MainWindow(QMainWindow):
    """
    MainWindow class.
    """

    def __init__(self, *args, **kwargs):
        """
        :param args: any
        :param kwargs: any
        """
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle(self.tr('Battery Buddy demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(720, 360)
        row = QHBoxLayout()  # type: QHBoxLayout
        for lv, chg in ((95, False), (60, False), (30, False), (12, False), (3, False), (45, True)):
            row.addWidget(BatteryBuddyWidget(level=lv, charging=chg))
        self.battery = BatteryBuddyWidget(level=75, lowBattery=self.onLow)  # type: BatteryBuddyWidget
        self.battery.setMinimumHeight(170)
        slider = QSlider(Qt.Horizontal)  # type: QSlider
        slider.setRange(0, 100)
        slider.setValue(75)
        slider.valueChanged.connect(self.battery.setLevel)
        chg = QCheckBox(self.tr('Charging'))  # type: QCheckBox
        chg.toggled.connect(self.battery.setCharging)
        self.info = QLabel()  # type: QLabel
        ctl = QHBoxLayout()  # type: QHBoxLayout
        ctl.addWidget(QLabel(self.tr('Level')))
        ctl.addWidget(slider, 1)
        ctl.addWidget(chg)
        ctl.addWidget(self.info)
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addLayout(row, 1)
        layout.addWidget(self.battery, 1)
        layout.addLayout(ctl)
        self.setCentralWidget(wdg)

    @pyqtSlot()
    def onLow(self):
        """
        :return:
        """
        self.info.setText(self.tr('Low battery!'))
