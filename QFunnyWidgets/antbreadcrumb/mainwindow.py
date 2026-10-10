# coding=utf-8
"""
Demo window for AntBreadcrumbWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QListWidget, QLabel
from ManyQt.QtCore import pyqtSlot
from ManyQt.QtGui import QIcon
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .antbreadcrumb import AntBreadcrumbWidget
except:
    from antbreadcrumb import AntBreadcrumbWidget

TREE = {'Home': ['Projects', 'Photos', 'Recipes'], 'Projects': ['QFunnyWidgets', 'Secret Plan'],
        'QFunnyWidgets': ['src', 'docs'], 'Photos': ['Cats', 'More cats'], 'Recipes': ['Pancakes']}  # type: dict


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
        self.setWindowTitle(self.tr('Ant Breadcrumb demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(560, 360)
        self.crumbs = AntBreadcrumbWidget(path=['Home'], pathChanged=self.onPath)  # type: AntBreadcrumbWidget
        self.list = QListWidget()  # type: QListWidget
        self.list.itemDoubleClicked.connect(lambda it: self.crumbs.push(it.text()))
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addWidget(self.crumbs)
        layout.addWidget(QLabel(self.tr('Double-click a folder to go deeper. Click a crumb to go back.')))
        layout.addWidget(self.list, 1)
        self.setCentralWidget(wdg)
        self.onPath(self.crumbs.getPath())

    @pyqtSlot(list)
    def onPath(self, path):
        """
        :param path: list[str]
        :return:
        """
        self.list.clear()
        self.list.addItems(TREE.get(path[-1], []))
