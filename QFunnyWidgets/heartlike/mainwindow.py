# coding=utf-8
"""
Demo window for HeartLikeButtonWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel
from ManyQt.QtCore import Qt, pyqtSlot
from ManyQt.QtGui import QIcon
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .heartlike import HeartLikeButtonWidget
except:
    from heartlike import HeartLikeButtonWidget


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
        self.setWindowTitle(self.tr('Heart Like Button demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(520, 300)
        post = QLabel(self.tr('Just shipped a new feature on a Friday afternoon. What could go wrong?'))  # type: QLabel
        post.setWordWrap(True)
        f = post.font()
        f.setPointSize(12)
        post.setFont(f)
        row = QHBoxLayout()  # type: QHBoxLayout
        self.heart = HeartLikeButtonWidget(count=41, likedChanged=self.onLiked)  # type: HeartLikeButtonWidget
        row.addWidget(self.heart)
        row.addWidget(HeartLikeButtonWidget(count=1203, liked=True, color='#7B5CFF'))
        self.info = QLabel(self.tr('Click to like. Click again to break its heart. Spam it to make it dizzy.'))  # type: QLabel
        self.info.setAlignment(Qt.AlignCenter)
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addWidget(post)
        layout.addLayout(row, 1)
        layout.addWidget(self.info)
        self.setCentralWidget(wdg)

    @pyqtSlot(bool)
    def onLiked(self, liked):
        """
        :param liked: bool
        :return:
        """
        self.info.setText(self.tr('Liked!') if liked else self.tr('Unliked. It will heal.'))
