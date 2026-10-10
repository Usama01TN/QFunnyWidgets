# coding=utf-8
"""
Demo window for SearchDetectiveWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QListWidget
from ManyQt.QtGui import QIcon
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .searchdetective import SearchDetectiveWidget
except:
    from searchdetective import SearchDetectiveWidget

SUSPECTS = ['Professor Moriarty', 'Irene Adler', 'Colonel Moran', 'Mrs Hudson', 'Inspector Lestrade',
            'Dr Watson', 'Mycroft Holmes', 'The Hound of the Baskervilles', 'Charles Augustus Milverton']  # type: list[str]


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
        self.setWindowTitle(self.tr('Search Detective demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(560, 440)
        self.results = QListWidget()  # type: QListWidget
        self.search = SearchDetectiveWidget(placeholder=self.tr('Search suspects (try "mo" or "xyz")'),
                                            searchFunction=self.find)  # type: SearchDetectiveWidget
        self.search.setMinimumHeight(170)
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addWidget(self.search)
        layout.addWidget(self.results, 1)
        self.setCentralWidget(wdg)

    def find(self, text):
        """
        :param text: str | unicode | QString
        :return: (int) Number of matches.
        """
        hits = [s for s in SUSPECTS if text.lower() in s.lower()]  # type: list[str]
        self.results.clear()
        self.results.addItems(hits)
        return len(hits)
