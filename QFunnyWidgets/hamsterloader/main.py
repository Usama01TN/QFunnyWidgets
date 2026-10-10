# coding=utf-8
"""
Entry point for the HamsterLoaderWidget demo.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .mainwindow import MainWindow
except:
    from mainwindow import MainWindow

if __name__ == '__main__':
    from ManyQt.QtWidgets import QApplication
    from sys import argv, exit

    a = QApplication(argv)  # type: QApplication
    w = MainWindow()  # type: MainWindow
    w.show()
    exit(a.exec_())
