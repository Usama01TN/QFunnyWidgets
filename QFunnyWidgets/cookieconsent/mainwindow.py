# coding=utf-8
"""
Demo window for CookieConsentWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton
from ManyQt.QtCore import Qt, pyqtSlot
from ManyQt.QtGui import QIcon
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .cookieconsent import CookieConsentWidget
except:
    from cookieconsent import CookieConsentWidget


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
        self.setWindowTitle(self.tr('Cookie Consent demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(640, 360)
        self.banner = CookieConsentWidget(accepted=self.onAccepted, declined=self.onDeclined)  # type: CookieConsentWidget
        self.banner.setMinimumHeight(170)
        self.info = QLabel(self.tr('Hover the buttons and watch the cookie.'))  # type: QLabel
        self.info.setAlignment(Qt.AlignCenter)
        again = QPushButton(self.tr('Ask again'))  # type: QPushButton
        again.clicked.connect(self.banner.reset)
        wdg = QWidget()  # type: QWidget
        wdg.setStyleSheet('background: #ECEEF3;')
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addStretch(1)
        layout.addWidget(self.banner)
        layout.addWidget(self.info)
        layout.addWidget(again, 0, Qt.AlignCenter)
        self.setCentralWidget(wdg)

    @pyqtSlot()
    def onAccepted(self):
        """
        :return:
        """
        self.info.setText(self.tr('Cookies accepted. The cookie was delicious.'))

    @pyqtSlot()
    def onDeclined(self):
        """
        :return:
        """
        self.info.setText(self.tr('Cookies declined. Somewhere, a cookie weeps.'))
