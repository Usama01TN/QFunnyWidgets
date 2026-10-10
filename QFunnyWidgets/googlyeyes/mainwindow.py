# coding=utf-8
"""
Demo window for GooglyEyesWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QSlider, QSpinBox, QPushButton
from ManyQt.QtCore import Qt, pyqtSlot
from ManyQt.QtGui import QIcon
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .googlyeyes import GooglyEyesWidget
except:
    from googlyeyes import GooglyEyesWidget


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
        self.setWindowTitle(self.tr('Googly Eyes demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(640, 420)
        self.eyes = GooglyEyesWidget(eyeCount=2, wobble=0.6, gravity=900, blinkInterval=3500,
                                     poked=self.onPoked, gotAngry=self.onAngry)  # type: GooglyEyesWidget
        self.info = QLabel(self.tr('Move the mouse around. Click an eye to poke it (3 quick pokes = angry).'))  # type: QLabel
        self.info.setAlignment(Qt.AlignCenter)
        count = QSpinBox()  # type: QSpinBox
        count.setRange(1, 6)
        count.setValue(2)
        count.valueChanged.connect(self.eyes.setEyeCount)
        wobble = QSlider(Qt.Horizontal)  # type: QSlider
        wobble.setRange(0, 100)
        wobble.setValue(60)
        wobble.valueChanged.connect(lambda v: self.eyes.setWobble(v / 100.0))
        gravity = QSlider(Qt.Horizontal)  # type: QSlider
        gravity.setRange(0, 3000)
        gravity.setValue(900)
        gravity.valueChanged.connect(self.eyes.setGravity)
        blink = QPushButton(self.tr('Blink'))  # type: QPushButton
        blink.clicked.connect(self.eyes.blink)
        dizzy = QPushButton(self.tr('Dizzy!'))  # type: QPushButton
        dizzy.clicked.connect(self.eyes.makeDizzy)
        controls = QHBoxLayout()  # type: QHBoxLayout
        for w in (QLabel(self.tr('Eyes')), count, QLabel(self.tr('Wobble')), wobble,
                  QLabel(self.tr('Gravity')), gravity, blink, dizzy):
            controls.addWidget(w)
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addWidget(self.eyes, 1)
        layout.addWidget(self.info)
        layout.addLayout(controls)
        self.setCentralWidget(wdg)

    @pyqtSlot(int)
    def onPoked(self, count):
        """
        :param count: int
        :return:
        """
        self.info.setText(self.tr('Ouch! Poked {} time(s).').format(count))

    @pyqtSlot()
    def onAngry(self):
        """
        :return:
        """
        self.info.setText(self.tr('HEY! Stop poking me!'))
