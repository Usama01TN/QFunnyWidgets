# coding=utf-8
"""
Demo window for PresenceAvatarWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QComboBox
from ManyQt.QtGui import QIcon
from ManyQt.QtCore import Qt
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .presenceavatar import PresenceAvatarWidget
except:
    from presenceavatar import PresenceAvatarWidget


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
        self.setWindowTitle(self.tr('Presence Avatar demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(620, 340)
        row = QHBoxLayout()  # type: QHBoxLayout
        team = (('Ada Lovelace', PresenceAvatarWidget.Online), ('Alan Turing', PresenceAvatarWidget.Away),
                ('Grace Hopper', PresenceAvatarWidget.Busy), ('Charles Babbage', PresenceAvatarWidget.Offline))
        for name, st in team:
            row.addWidget(PresenceAvatarWidget(name=name, status=st, clicked=lambda n=name: self.onClicked(n)))
        self.me = PresenceAvatarWidget(name='You Yourself', status=PresenceAvatarWidget.Online)  # type: PresenceAvatarWidget
        self.me.setMinimumSize(140, 160)
        combo = QComboBox()  # type: QComboBox
        combo.addItems([s.name for s in PresenceAvatarWidget.Status])
        combo.currentIndexChanged.connect(self.me.setStatus)
        self.info = QLabel(self.tr('Hover an avatar. Click to wave.'))  # type: QLabel
        self.info.setAlignment(Qt.AlignCenter)
        bottom = QHBoxLayout()  # type: QHBoxLayout
        bottom.addWidget(self.me)
        bottom.addWidget(QLabel(self.tr('My status:')))
        bottom.addWidget(combo)
        bottom.addStretch(1)
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addLayout(row, 1)
        layout.addWidget(self.info)
        layout.addLayout(bottom)
        self.setCentralWidget(wdg)

    def onClicked(self, name):
        """
        :param name: str | unicode | QString
        :return:
        """
        self.info.setText(self.tr('You waved at {}.').format(name))
