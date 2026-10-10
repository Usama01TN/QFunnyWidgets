# coding=utf-8
"""
Demo window for DropZoneMonsterWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QLabel, QListWidget
from ManyQt.QtCore import Qt, pyqtSlot
from ManyQt.QtGui import QIcon
from os.path import dirname, join, basename
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .dropzone import DropZoneMonsterWidget
except:
    from dropzone import DropZoneMonsterWidget


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
        self.setWindowTitle(self.tr('Drop Zone Monster demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(520, 560)
        self.zone = DropZoneMonsterWidget(acceptedExtensions=['png', 'jpg', 'jpeg', 'pdf', 'txt'],
                                          filesDropped=self.onDropped,
                                          filesRejected=self.onRejected)  # type: DropZoneMonsterWidget
        self.info = QLabel(self.tr('Drag images, PDFs or text files from your file manager onto the monster.'))  # type: QLabel
        self.info.setAlignment(Qt.AlignCenter)
        self.info.setWordWrap(True)
        self.list = QListWidget()  # type: QListWidget
        self.list.setMaximumHeight(120)
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addWidget(self.zone, 1)
        layout.addWidget(self.info)
        layout.addWidget(self.list)
        self.setCentralWidget(wdg)

    @pyqtSlot(list)
    def onDropped(self, paths):
        """
        :param paths: list[str | unicode | QString]
        :return:
        """
        for pth in paths:
            self.list.addItem(self.tr('Eaten: {}').format(basename(pth)))

    @pyqtSlot(list)
    def onRejected(self, paths):
        """
        :param paths: list[str | unicode | QString]
        :return:
        """
        self.info.setText(self.tr('Rejected: {}').format(', '.join(basename(pth) for pth in paths)))
