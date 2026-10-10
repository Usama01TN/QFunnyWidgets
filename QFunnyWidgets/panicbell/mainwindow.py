# coding=utf-8
"""
Demo window for PanicBellWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton
from ManyQt.QtCore import Qt, pyqtSlot
from ManyQt.QtGui import QIcon
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .panicbell import PanicBellWidget
except:
    from panicbell import PanicBellWidget


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
        self.setWindowTitle(self.tr('Panic Bell demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(560, 420)
        self.bell = PanicBellWidget(count=3, countChanged=self.onCount)  # type: PanicBellWidget
        self.info = QLabel(self.tr('Add notifications and watch the stress build. Click the bell to clear.'))  # type: QLabel
        self.info.setAlignment(Qt.AlignCenter)
        row = QHBoxLayout()  # type: QHBoxLayout
        for label, amount in (('+1', 1), ('+10', 10), ('+100', 100)):
            b = QPushButton(label)  # type: QPushButton
            b.clicked.connect(lambda _=False, a=amount: self.bell.setCount(self.bell.getCount() + a))
            row.addWidget(b)
        clear = QPushButton(self.tr('Clear'))  # type: QPushButton
        clear.clicked.connect(self.bell.clear)
        row.addWidget(clear)
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addWidget(self.bell, 1)
        layout.addWidget(self.info)
        layout.addLayout(row)
        self.setCentralWidget(wdg)

    @pyqtSlot(int)
    def onCount(self, count):
        """
        :param count: int
        :return:
        """
        self.info.setText(self.tr('{} unread notification(s)').format(count))
