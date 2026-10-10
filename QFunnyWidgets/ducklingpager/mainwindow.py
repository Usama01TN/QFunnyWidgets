# coding=utf-8
"""
Demo window for DucklingPagerWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton, QStackedWidget
from ManyQt.QtGui import QIcon
from ManyQt.QtCore import Qt
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .ducklingpager import DucklingPagerWidget
except:
    from ducklingpager import DucklingPagerWidget

SLIDES = ['Welcome aboard', 'Meet your dashboard', 'Invite your team', 'Set your goals', 'You are ready!']  # type: list[str]


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
        self.setWindowTitle(self.tr('Duckling Pager demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(560, 360)
        self.stack = QStackedWidget()  # type: QStackedWidget
        for title in SLIDES:
            lbl = QLabel(self.tr(title))  # type: QLabel
            lbl.setAlignment(Qt.AlignCenter)
            f = lbl.font()
            f.setPointSize(18)
            f.setBold(True)
            lbl.setFont(f)
            self.stack.addWidget(lbl)
        self.pager = DucklingPagerWidget(count=len(SLIDES), ducklings=3,
                                         currentChanged=self.stack.setCurrentIndex)  # type: DucklingPagerWidget
        prev = QPushButton(self.tr('Back'))  # type: QPushButton
        prev.clicked.connect(self.pager.previous)
        nxt = QPushButton(self.tr('Next'))  # type: QPushButton
        nxt.clicked.connect(self.pager.next)
        row = QHBoxLayout()  # type: QHBoxLayout
        row.addWidget(prev)
        row.addWidget(self.pager, 1)
        row.addWidget(nxt)
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addWidget(self.stack, 1)
        layout.addLayout(row)
        self.setCentralWidget(wdg)
