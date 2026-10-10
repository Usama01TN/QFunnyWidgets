# coding=utf-8
"""
Demo window for SleepyCatSectionWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QFormLayout, QLineEdit, QCheckBox, QSpinBox, QLabel
from ManyQt.QtGui import QIcon
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .catsection import SleepyCatSectionWidget
except:
    from catsection import SleepyCatSectionWidget


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
        self.setWindowTitle(self.tr('Sleepy Cat Section demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(480, 520)
        form = QWidget()  # type: QWidget
        fl = QFormLayout(form)  # type: QFormLayout
        fl.addRow(self.tr('Server'), QLineEdit('api.example.com'))
        fl.addRow(self.tr('Port'), QSpinBox())
        fl.addRow('', QCheckBox(self.tr('Enable turbo mode')))
        notes = QLabel(self.tr('Nothing to see here. The cat is just resting its eyes.'))  # type: QLabel
        notes.setWordWrap(True)
        wdg = QWidget()  # type: QWidget
        layout = QVBoxLayout(wdg)  # type: QVBoxLayout
        layout.addWidget(SleepyCatSectionWidget(title=self.tr('Advanced settings'), content=form))
        layout.addWidget(SleepyCatSectionWidget(title=self.tr('Release notes'), content=notes, expanded=True,
                                                catColor='#8D99AE'))
        layout.addStretch(1)
        self.setCentralWidget(wdg)
