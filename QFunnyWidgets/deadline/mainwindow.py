# coding=utf-8
"""
Demo window for DeadlineCountdownWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel
from ManyQt.QtCore import pyqtSlot
from ManyQt.QtGui import QIcon
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .deadline import DeadlineCountdownWidget
except:
    from deadline import DeadlineCountdownWidget


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
        self.setWindowTitle(self.tr('Deadline Countdown demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(560, 300)
        self.deadline = DeadlineCountdownWidget(duration=30, title='Quarterly report due',
                                                expired=self.onExpired)  # type: DeadlineCountdownWidget
        self.info = QLabel(self.tr('A 30 second deadline. Watch the calendar cope.'))  # type: QLabel
        row = QHBoxLayout()  # type: QHBoxLayout
        for label, slot in ((self.tr('Restart'), self.deadline.start), (self.tr('Pause'), self.deadline.pause),
                            (self.tr('Resume'), self.deadline.resume)):
            b = QPushButton(label)  # type: QPushButton
            b.clicked.connect(lambda _=False, s=slot: s())
            row.addWidget(b)
        ext = QPushButton(self.tr('Extend +15 s'))  # type: QPushButton
        ext.clicked.connect(lambda: self.deadline.extend(15))
        row.addWidget(ext)
        fast = QPushButton(self.tr('Speed x5'))  # type: QPushButton
        fast.setCheckable(True)
        fast.toggled.connect(lambda on: self.deadline.setTimeScale(5.0 if on else 1.0))
        row.addWidget(fast)
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addWidget(self.deadline, 1)
        layout.addWidget(self.info)
        layout.addLayout(row)
        self.setCentralWidget(wdg)

    @pyqtSlot()
    def onExpired(self):
        """
        :return:
        """
        self.info.setText(self.tr('Deadline missed. The calendar is fine. Everything is fine.'))
