# coding=utf-8
"""
Demo window for VolumeKnobWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel
from ManyQt.QtCore import Qt, pyqtSlot
from ManyQt.QtGui import QIcon
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .volumeknob import VolumeKnobWidget
except:
    from volumeknob import VolumeKnobWidget


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
        self.setWindowTitle(self.tr('Volume Knob demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(640, 380)
        row = QHBoxLayout()  # type: QHBoxLayout
        self.knobs = []  # type: list[VolumeKnobWidget]
        for v in (0, 25, 55, 80, 100):
            k = VolumeKnobWidget(value=v, valueChanged=self.onValue)  # type: VolumeKnobWidget
            self.knobs.append(k)
            row.addWidget(k)
        self.info = QLabel(
            self.tr('Drag around a knob, scroll, use arrows. Double-click or M to mute.'))  # type: QLabel
        self.info.setAlignment(Qt.AlignCenter)
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addLayout(row, 1)
        layout.addWidget(self.info)
        self.setCentralWidget(wdg)

    @pyqtSlot(int)
    def onValue(self, value):
        """
        :param value: int
        :return:
        """
        self.info.setText(self.tr('Volume: {}%').format(value))
