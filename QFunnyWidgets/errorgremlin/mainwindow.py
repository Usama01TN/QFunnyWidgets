# coding=utf-8
"""
Demo window for ErrorGremlinWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QPushButton
from ManyQt.QtGui import QIcon
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .errorgremlin import ErrorGremlinWidget
except:
    from errorgremlin import ErrorGremlinWidget

ALERTS = {0: ('Heads up', 'Scheduled maintenance tonight at 2 am. The gremlin is resting up for it.'),
          1: ('Disk almost full', 'Only 3% space left. Something is hoarding cat pictures.'),
          2: ('Connection lost', 'We could not reach the server. Someone appears to be chewing the cable.'),
          3: ('Production is on fire', 'Literally. Please do not panic. Panic quietly.')}  # type: dict


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
        self.setWindowTitle(self.tr('Error Gremlin demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(640, 520)
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        self.banners = []  # type: list[ErrorGremlinWidget]
        for sev in range(4):
            title, msg = ALERTS[sev]
            b = ErrorGremlinWidget(severity=sev, title=title, message=msg)  # type: ErrorGremlinWidget
            b.setMinimumHeight(100)
            self.banners.append(b)
            layout.addWidget(b)
        again = QPushButton(self.tr('Show all again'))  # type: QPushButton
        again.clicked.connect(lambda: [b.showAlert() for b in self.banners])
        layout.addStretch(1)
        layout.addWidget(again)
        self.setCentralWidget(wdg)
