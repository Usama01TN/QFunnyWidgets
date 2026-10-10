# coding=utf-8
"""
Demo window for RocketBackToTop.
"""
from ManyQt.QtWidgets import QMainWindow, QScrollArea, QLabel
from ManyQt.QtGui import QIcon
from ManyQt.QtCore import Qt
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .rockettop import RocketBackToTop
except:
    from rockettop import RocketBackToTop


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
        self.setWindowTitle(self.tr('Rocket Back To Top demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(520, 520)
        text = '\n\n'.join(self.tr('Chapter {}: In which the reader scrolls a little further, '
                                   'wondering whether the rocket will appear. It will.').format(i + 1) for i in range(40))
        body = QLabel(text)  # type: QLabel
        body.setWordWrap(True)
        body.setAlignment(Qt.AlignTop)
        body.setContentsMargins(16, 16, 90, 16)
        area = QScrollArea()  # type: QScrollArea
        area.setWidgetResizable(True)
        area.setWidget(body)
        self.setCentralWidget(area)
        self.rocket = RocketBackToTop(area, threshold=250)  # type: RocketBackToTop
