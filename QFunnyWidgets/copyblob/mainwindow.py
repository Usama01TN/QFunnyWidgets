# coding=utf-8
"""
Demo window for CopyBlobButtonWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit
from ManyQt.QtCore import pyqtSlot
from ManyQt.QtGui import QIcon
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .copyblob import CopyBlobButtonWidget
except:
    from copyblob import CopyBlobButtonWidget


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
        self.setWindowTitle(self.tr('Copy Blob Button demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(480, 400)
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addWidget(QLabel(self.tr('Install:')))
        layout.addWidget(CopyBlobButtonWidget(text='pip install funnywidgets', copied=self.onCopied))
        layout.addWidget(QLabel(self.tr('Your API key (masked):')))
        layout.addWidget(CopyBlobButtonWidget(text='sk-live-8f3a9c2e7b1d4f60', label='sk-live-****************',
                                              prompt='', blobColor='#FF9F1C', copied=self.onCopied))
        layout.addWidget(QLabel(self.tr('Paste here to check:')))
        self.paste = QLineEdit()  # type: QLineEdit
        layout.addWidget(self.paste)
        self.setCentralWidget(wdg)

    @pyqtSlot('QString')
    def onCopied(self, text):
        """
        :param text: str | unicode | QString
        :return:
        """
        self.statusBar().showMessage(self.tr('Copied {} characters').format(len(text)), 2000)
