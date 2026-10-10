# coding=utf-8
"""
Demo window for ChameleonColorPickerWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QLabel
from ManyQt.QtGui import QIcon
from ManyQt.QtCore import Qt
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .chameleonpicker import ChameleonColorPickerWidget
except:
    from chameleonpicker import ChameleonColorPickerWidget


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
        self.setWindowTitle(self.tr('Chameleon Color Picker demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(620, 360)
        self.preview = QLabel(self.tr('Your theme color'))  # type: QLabel
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumHeight(50)
        self.picker = ChameleonColorPickerWidget(colorChanged=self.onColor)  # type: ChameleonColorPickerWidget
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addWidget(self.picker, 1)
        layout.addWidget(self.preview)
        self.setCentralWidget(wdg)
        self.onColor(self.picker.getColor())

    def onColor(self, color):
        """
        :param color: QColor
        :return:
        """
        self.preview.setStyleSheet(
            'background: {}; color: white; border-radius: 10px; font-weight: bold;'.format(color.name()))
        self.preview.setText(self.tr('Your theme color: {}').format(color.name().upper()))
