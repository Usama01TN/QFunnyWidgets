# -*- coding: utf-8 -*-
"""
Headless smoke tests used by CI (and handy locally): every widget demo runs, resizes and closes without an
exception, and (on PyQt bindings) the Qt Designer plugins load the way Designer loads them.
Select the binding with QT_API (pyqt5, pyqt6, pyside6, ...). Exit code 0 means everything passed.
    QT_API=pyqt5 python tests/smoke.py
"""
from traceback import format_exception, format_exc
from os.path import dirname, abspath, join, exists
from sys import path, modules, argv, exit
from xml.dom.minidom import parseString
from os import environ, listdir

environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
ROOT = dirname(dirname(abspath(__file__)))  # type: str  # project root (setup.py)
PACKAGE = join(ROOT, 'QFunnyWidgets')  # type: str
PLUGINS = join(ROOT, 'plugins')  # type: str
if ROOT not in path:
    path.insert(0, ROOT)

ERRORS = []  # type: list[str]


def excepthook(kind, value, tb):
    """
    Collect exceptions raised inside Qt callbacks (paint events, timers) instead of aborting.
    :param kind: type
    :param value: BaseException
    :param tb: traceback
    :return:
    """
    ERRORS.append(''.join(format_exception(kind, value, tb)))


def spin(app, ms):
    """
    Process events for about ms milliseconds.
    :param app: QApplication
    :param ms: int
    :return:
    """
    from ManyQt.QtCore import QElapsedTimer
    clock = QElapsedTimer()  # type: QElapsedTimer
    clock.start()
    while clock.elapsed() < ms:
        app.processEvents()


def demoPackages():
    """
    :return: (list[str]) Widget packages that have a mainwindow.py demo.
    """
    return sorted(d for d in listdir(PACKAGE) if exists(join(PACKAGE, d, 'mainwindow.py')))


def testDemos(app):
    """
    :param app: QApplication
    :return: (list[str]) Failed package names.
    """
    failed = []  # type: list[str]
    for pkg in demoPackages():
        before = len(ERRORS)  # type: int
        path.insert(0, join(PACKAGE, pkg))
        modules.pop('mainwindow', None)
        try:
            window = __import__('mainwindow').MainWindow()
            window.show()
            spin(app, 300)
            window.resize(window.width() - 60, window.height() - 40)
            spin(app, 200)
            window.close()
            window.deleteLater()
            spin(app, 20)
        except Exception:
            ERRORS.append(format_exc())
        finally:
            path.pop(0)
        ok = len(ERRORS) == before  # type: bool
        print('  {:<18} {}'.format(pkg, 'ok' if ok else 'FAILED'))
        if not ok:
            failed.append(pkg)
    return failed


def testDesignerPlugins(app):
    """
    Load plugins/funnywidgetsplugin.py like PyQt's Designer does and exercise every plugin.
    :param app: QApplication
    :return: (list[str]) Problems found.
    """
    import ManyQt
    from ManyQt.QtWidgets import QWidget
    from ManyQt.QtDesigner import QPyDesignerCustomWidgetPlugin
    if PLUGINS not in path:
        path.insert(0, PLUGINS)
    plugin = __import__('funnywidgetsplugin')
    classes = [v for v in vars(plugin).values() if isinstance(v, type) and
               issubclass(v, QPyDesignerCustomWidgetPlugin) and v is not QPyDesignerCustomWidgetPlugin]
    problems = []  # type: list[str]
    form = QWidget()  # type: QWidget
    for cls in classes:
        try:
            p = cls()
            p.initialize(None)
            w = p.createWidget(form)
            if type(w).__name__ != p.name():
                problems.append('{}: createWidget returned {}'.format(p.name(), type(w).__name__))
            if p.icon().isNull():
                problems.append('{}: missing icon'.format(p.name()))
            parseString(p.domXml())
            module = __import__(p.includeFile(), fromlist=[p.name()])
            if not hasattr(module, p.name()):
                problems.append('{}: includeFile {} does not export it'.format(p.name(), p.includeFile()))
        except Exception:
            problems.append(format_exc())
    if len(classes) != len(plugin.WIDGETS):
        problems.append('expected {} plugin classes, found {}'.format(len(plugin.WIDGETS), len(classes)))
    form.deleteLater()
    print('  {} Designer plugin classes checked on {}'.format(len(classes), ManyQt.USED_API))
    return problems


def main():
    """
    :return: (int) Exit code.
    """
    import sys
    sys.excepthook = excepthook
    from ManyQt.QtWidgets import QApplication
    import ManyQt
    app = QApplication(argv)  # type: QApplication
    print('Qt binding: {}'.format(ManyQt.USED_API))
    print('Widget demos:')
    failed = testDemos(app)  # type: list[str]
    problems = []  # type: list[str]
    if ManyQt.USED_API.startswith('pyqt'):
        print('Designer plugins:')
        problems = testDesignerPlugins(app)
    for e in ERRORS + problems:
        print('-' * 70)
        print(e.strip())
    total = len(demoPackages())  # type: int
    print('Result: {}/{} demos ok, {} plugin problem(s)'.format(total - len(failed), total, len(problems)))
    return 1 if (failed or problems or ERRORS) else 0


if __name__ == '__main__':
    exit(main())
