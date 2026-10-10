# coding=utf-8
"""
Demo window for HelpOwlWidget.
"""
from ManyQt.QtWidgets import QMainWindow, QWidget, QGridLayout, QLabel, QLineEdit, QSpinBox
from ManyQt.QtGui import QIcon
from os.path import dirname, join
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .helpowl import HelpOwlWidget
except:
    from helpowl import HelpOwlWidget


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
        self.setWindowTitle(self.tr('Help Owl demo'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'logo.png')))
        self.resize(480, 260)
        wdg = QWidget()  # type: QWidget
        grid = QGridLayout(wdg)  # type: QGridLayout
        rows = ((self.tr('Workspace name'), QLineEdit('acme-corp'),
                 self.tr('The name everyone in your team will see. You can change it later (we think).')),
                (self.tr('Retention (days)'), QSpinBox(),
                 self.tr('How long we keep deleted items. After that the owl eats them.')),
                (self.tr('Webhook URL'), QLineEdit(),
                 self.tr('We POST a JSON payload here whenever something happens. Hoo!')))
        for r, (label, field, help_) in enumerate(rows):
            grid.addWidget(QLabel(label), r, 0)
            grid.addWidget(field, r, 1)
            grid.addWidget(HelpOwlWidget(helpText=help_, title=label), r, 2)
        grid.setRowStretch(3, 1)
        self.setCentralWidget(wdg)
