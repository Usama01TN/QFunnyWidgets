# coding=utf-8
"""
Demo window for RunawayButtonWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QSpinBox, QPushButton
from ManyQt.QtCore import Qt, pyqtSlot
from ManyQt.QtGui import QIcon
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .runawaybutton import RunawayButtonWidget
except:
    from runawaybutton import RunawayButtonWidget


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
        self.setWindowTitle(self.tr('Runaway Button demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(720, 460)
        self.button = RunawayButtonWidget(text='Click me!', maxEscapes=7, color='#FF4D6D',
                                          caught=self.onCaught, escaped=self.onEscaped)  # type: RunawayButtonWidget
        self.info = QLabel(self.tr('Try to click the button. Good luck.'))  # type: QLabel
        self.info.setAlignment(Qt.AlignCenter)
        escapes = QSpinBox()  # type: QSpinBox
        escapes.setRange(0, 50)
        escapes.setValue(7)
        escapes.setSpecialValueText(self.tr('Never gives up'))
        escapes.valueChanged.connect(self.button.setMaxEscapes)
        reset = QPushButton(self.tr('Reset'))  # type: QPushButton
        reset.clicked.connect(self.button.reset)
        controls = QHBoxLayout()  # type: QHBoxLayout
        controls.addWidget(QLabel(self.tr('Escapes before giving up')))
        controls.addWidget(escapes)
        controls.addStretch(1)
        controls.addWidget(reset)
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addWidget(self.button, 1)
        layout.addWidget(self.info)
        layout.addLayout(controls)
        self.setCentralWidget(wdg)

    @pyqtSlot(int)
    def onEscaped(self, count):
        """
        :param count: int
        :return:
        """
        self.info.setText(self.tr('It escaped {} time(s)...').format(count))

    @pyqtSlot(int)
    def onCaught(self, escapes):
        """
        :param escapes: int
        :return:
        """
        self.info.setText(self.tr('Caught it after {} escapes!').format(escapes))
