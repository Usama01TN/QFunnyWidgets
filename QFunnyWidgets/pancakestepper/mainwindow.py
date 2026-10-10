# coding=utf-8
"""
Demo window for PancakeStepperWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QLabel
from ManyQt.QtCore import Qt, pyqtSlot
from ManyQt.QtGui import QIcon
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .pancakestepper import PancakeStepperWidget
except:
    from pancakestepper import PancakeStepperWidget


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
        self.setWindowTitle(self.tr('Pancake Stepper demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(360, 440)
        self.stepper = PancakeStepperWidget(value=2, maximum=8, valueChanged=self.onValue)  # type: PancakeStepperWidget
        self.total = QLabel()  # type: QLabel
        self.total.setAlignment(Qt.AlignCenter)
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addWidget(QLabel(self.tr('Breakfast order (+/-, wheel or arrow keys):')))
        layout.addWidget(self.stepper, 1)
        layout.addWidget(self.total)
        self.setCentralWidget(wdg)
        self.onValue(self.stepper.getValue())

    @pyqtSlot(int)
    def onValue(self, value):
        """
        :param value: int
        :return:
        """
        self.total.setText(self.tr('Total: ${:.2f}').format(value * 2.5))
