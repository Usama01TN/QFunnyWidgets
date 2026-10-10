# coding=utf-8
"""
Demo window for MoodSliderWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QLabel
from ManyQt.QtCore import Qt, pyqtSlot
from ManyQt.QtGui import QIcon
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .moodslider import MoodSliderWidget
except:
    from moodslider import MoodSliderWidget


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
        self.setWindowTitle(self.tr('Mood Slider demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(600, 320)
        title = QLabel(self.tr('How do you feel about Mondays?'))  # type: QLabel
        title.setAlignment(Qt.AlignCenter)
        f = title.font()
        f.setPointSize(14)
        f.setBold(True)
        title.setFont(f)
        self.slider = MoodSliderWidget(value=50, valueChanged=self.onValue,
                                       moodChanged=self.onMood)  # type: MoodSliderWidget
        self.slider.setMinimumHeight(120)
        self.info = QLabel(self.tr('Drag, scroll or use the arrow keys.'))  # type: QLabel
        self.info.setAlignment(Qt.AlignCenter)
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.setContentsMargins(30, 20, 30, 20)
        layout.addStretch(1)
        layout.addWidget(title)
        layout.addWidget(self.slider)
        layout.addWidget(self.info)
        layout.addStretch(1)
        self.setCentralWidget(wdg)

    @pyqtSlot(int)
    def onValue(self, value):
        """
        :param value: int
        :return:
        """
        self.info.setText(self.tr('Value: {} - {}').format(value, self.slider.getMood()))

    @pyqtSlot('QString')
    def onMood(self, mood):
        """
        :param mood: str | unicode | QString
        :return:
        """
        print('Mood changed: {}'.format(mood))
