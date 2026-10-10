# coding=utf-8
"""
Entry point for the QFunnyWidgets MainWindow (also the "funnywidgets-mainwindow" console script).
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .mainwindow import MainWindow
except:
    from mainwindow import MainWindow


def main():
    """
    Launch the MainWindow gallery.
    :return: (int) Exit code of the Qt event loop.
    """
    from ManyQt.QtWidgets import QApplication
    from ManyQt.QtCore import Qt
    from sys import argv

    # HiDPI switches exist (and matter) on Qt 5 only; Qt 6 always scales.
    for attr in ('AA_EnableHighDpiScaling', 'AA_UseHighDpiPixmaps'):
        if hasattr(Qt, attr):
            QApplication.setAttribute(getattr(Qt, attr), True)
    a = QApplication(argv)  # type: QApplication
    a.setStyle('Fusion')
    w = MainWindow()  # type: MainWindow
    w.show()
    return a.exec_()


if __name__ == '__main__':
    from sys import exit

    exit(main())
