# coding=utf-8
"""
Demo window for JellySwitchWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QSlider
from ManyQt.QtCore import Qt, pyqtSlot
from ManyQt.QtGui import QIcon
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .jellyswitch import JellySwitchWidget
except:
    from jellyswitch import JellySwitchWidget


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
        self.setWindowTitle(self.tr('Jelly Switch demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(520, 360)
        row = QHBoxLayout()  # type: QHBoxLayout
        self.switches = []  # type: list[JellySwitchWidget]
        for on, checked in (('#34C759', False), ('#5E60CE', True), ('#FF9F1C', False)):
            sw = JellySwitchWidget(checked=checked, onColor=on, toggled=self.onToggled)  # type: JellySwitchWidget
            sw.setMinimumSize(130, 80)
            self.switches.append(sw)
            row.addWidget(sw)
        self.info = QLabel(self.tr('Click a switch (or focus it and press Space).'))  # type: QLabel
        self.info.setAlignment(Qt.AlignCenter)
        wob = QSlider(Qt.Horizontal)  # type: QSlider
        wob.setRange(0, 100)
        wob.setValue(70)
        wob.valueChanged.connect(self.onWobbliness)
        controls = QHBoxLayout()  # type: QHBoxLayout
        controls.addWidget(QLabel(self.tr('Wobbliness')))
        controls.addWidget(wob)
        big = JellySwitchWidget(checked=True, onColor='#FF4D6D')  # type: JellySwitchWidget
        big.setMinimumHeight(140)
        self.switches.append(big)
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addLayout(row)
        layout.addWidget(big, 1)
        layout.addWidget(self.info)
        layout.addLayout(controls)
        self.setCentralWidget(wdg)

    @pyqtSlot(int)
    def onWobbliness(self, value):
        """
        :param value: (int) 0..100
        :return:
        """
        for sw in self.switches:
            sw.setWobbliness(value / 100.0)

    @pyqtSlot(bool)
    def onToggled(self, checked):
        """
        :param checked: bool
        :return:
        """
        self.info.setText(self.tr('Good morning!') if checked else self.tr('Back to sleep... zzz'))
