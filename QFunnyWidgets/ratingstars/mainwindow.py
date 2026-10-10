# coding=utf-8
"""
Demo window for StarRatingWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QLabel
from ManyQt.QtCore import Qt, pyqtSlot
from ManyQt.QtGui import QIcon
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .ratingstars import StarRatingWidget
except:
    from ratingstars import StarRatingWidget


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
        self.setWindowTitle(self.tr('Star Rating demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(560, 360)
        title = QLabel(self.tr('How was your experience?'))  # type: QLabel
        title.setAlignment(Qt.AlignCenter)
        f = title.font()
        f.setPointSize(14)
        f.setBold(True)
        title.setFont(f)
        self.stars = StarRatingWidget(rating=0, ratingChanged=self.onRating)  # type: StarRatingWidget
        self.stars.setMinimumHeight(130)
        self.small = StarRatingWidget(rating=3, maxRating=5, starColor='#FF8FA3', showLabel=False)  # type: StarRatingWidget
        self.small.setMaximumHeight(50)
        self.info = QLabel(self.tr('Hover to preview, click to rate (click again to clear). Keys 0-5 work too.'))  # type: QLabel
        self.info.setAlignment(Qt.AlignCenter)
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addWidget(title)
        layout.addWidget(self.stars, 1)
        layout.addWidget(self.info)
        layout.addWidget(self.small)
        self.setCentralWidget(wdg)

    @pyqtSlot(int)
    def onRating(self, rating):
        """
        :param rating: int
        :return:
        """
        self.info.setText(self.tr('You rated {} / 5').format(rating) if rating else self.tr('Rating cleared.'))
