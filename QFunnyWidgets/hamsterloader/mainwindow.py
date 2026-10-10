# coding=utf-8
"""
Demo window for HamsterLoaderWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QSlider, QPushButton, QCheckBox, QLabel
from ManyQt.QtCore import Qt, QTimer, pyqtSlot
from ManyQt.QtGui import QIcon
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .hamsterloader import HamsterLoaderWidget
except:
    from hamsterloader import HamsterLoaderWidget


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
        self.setWindowTitle(self.tr('Hamster Loader demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(520, 480)
        self.loader = HamsterLoaderWidget(progress=0.0, speed=1.0, finished=self.onFinished)  # type: HamsterLoaderWidget
        self.slider = QSlider(Qt.Horizontal)  # type: QSlider
        self.slider.setRange(0, 100)
        self.slider.setMinimumWidth(140)
        self.slider.valueChanged.connect(lambda v: self.loader.setProgress(v / 100.0))
        self.indet = QCheckBox(self.tr('Indeterminate'))  # type: QCheckBox
        self.indet.toggled.connect(self.onIndeterminate)
        sim = QPushButton(self.tr('Simulate download'))  # type: QPushButton
        sim.clicked.connect(self.simulate)
        self.__m_sim = QTimer(self)  # type: QTimer
        self.__m_sim.timeout.connect(self._step)
        controls = QHBoxLayout()  # type: QHBoxLayout
        controls.addWidget(QLabel(self.tr('Progress')))
        controls.addWidget(self.slider, 1)
        controls.addWidget(self.indet)
        controls.addWidget(sim)
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addWidget(self.loader, 1)
        layout.addLayout(controls)
        self.setCentralWidget(wdg)
        self.simulate()

    @pyqtSlot()
    def simulate(self):
        """
        :return:
        """
        self.indet.setChecked(False)
        self.slider.setValue(0)
        self.loader.reset()
        self.__m_sim.start(90)

    @pyqtSlot()
    def _step(self):
        """
        :return:
        """
        v = self.slider.value() + 1  # type: int
        self.slider.setValue(v)
        if v >= 100:
            self.__m_sim.stop()

    @pyqtSlot(bool)
    def onIndeterminate(self, on):
        """
        :param on: bool
        :return:
        """
        if on:
            self.__m_sim.stop()
            self.loader.setProgress(-1.0)
        else:
            self.loader.setProgress(self.slider.value() / 100.0)

    @pyqtSlot()
    def onFinished(self):
        """
        :return:
        """
        print(self.tr('Loading finished!'))
