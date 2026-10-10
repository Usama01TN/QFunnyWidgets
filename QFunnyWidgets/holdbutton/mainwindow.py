# coding=utf-8
"""
Demo window for NervousHoldButtonWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QSpinBox
from ManyQt.QtCore import Qt, pyqtSlot
from ManyQt.QtGui import QIcon
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .holdbutton import NervousHoldButtonWidget
except:
    from holdbutton import NervousHoldButtonWidget


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
        self.setWindowTitle(self.tr('Nervous Hold Button demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(560, 360)
        self.button = NervousHoldButtonWidget(holdDuration=1800, confirmed=self.onConfirmed,
                                              cancelled=self.onCancelled)  # type: NervousHoldButtonWidget
        self.button.setMinimumHeight(120)
        calm = NervousHoldButtonWidget(stages=['Hold to send', 'Sending...', 'Almost...'], doneText='Sent!',
                                       reliefText='Draft saved', color='#5E60CE')  # type: NervousHoldButtonWidget
        self.info = QLabel(self.tr('Press and hold (mouse or Space). Let go early to chicken out.'))  # type: QLabel
        self.info.setAlignment(Qt.AlignCenter)
        dur = QSpinBox()  # type: QSpinBox
        dur.setRange(300, 6000)
        dur.setSingleStep(100)
        dur.setSuffix(' ms')
        dur.setValue(1800)
        dur.valueChanged.connect(self.button.setHoldDuration)
        dur.valueChanged.connect(calm.setHoldDuration)
        row = QHBoxLayout()  # type: QHBoxLayout
        row.addStretch(1)
        row.addWidget(QLabel(self.tr('Hold duration')))
        row.addWidget(dur)
        row.addStretch(1)
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addWidget(self.button, 1)
        layout.addWidget(calm, 1)
        layout.addWidget(self.info)
        layout.addLayout(row)
        self.setCentralWidget(wdg)

    @pyqtSlot()
    def onConfirmed(self):
        """
        :return:
        """
        self.info.setText(self.tr('Confirmed. The button has fainted.'))

    @pyqtSlot('qreal')
    @pyqtSlot(float)
    @pyqtSlot(int)
    def onCancelled(self, progress):
        """
        :param progress: qreal | float | int
        :return:
        """
        self.info.setText(self.tr('Cancelled at {}%. Phew.').format(int(progress * 100)))
