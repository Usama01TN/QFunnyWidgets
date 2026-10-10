# coding=utf-8
"""
Demo window for DachshundTabsWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QLabel, QStackedWidget
from ManyQt.QtGui import QIcon
from ManyQt.QtCore import Qt
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .dachshundtabs import DachshundTabsWidget
except:
    from dachshundtabs import DachshundTabsWidget


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
        self.setWindowTitle(self.tr('Dachshund Tabs demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(620, 320)
        names = ['Overview', 'Activity', 'Settings', 'Billing', 'Help']  # type: list[str]
        self.pages = QStackedWidget()  # type: QStackedWidget
        for n in names:
            lbl = QLabel(self.tr('{} page').format(n))  # type: QLabel
            lbl.setAlignment(Qt.AlignCenter)
            self.pages.addWidget(lbl)
        self.tabs = DachshundTabsWidget(tabs=names, currentChanged=self.pages.setCurrentIndex)  # type: DachshundTabsWidget
        hint = QLabel(self.tr('Jump from the first tab to the last one. Watch the dog stretch.'))  # type: QLabel
        hint.setAlignment(Qt.AlignCenter)
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addWidget(self.tabs)
        layout.addWidget(self.pages, 1)
        layout.addWidget(hint)
        self.setCentralWidget(wdg)
