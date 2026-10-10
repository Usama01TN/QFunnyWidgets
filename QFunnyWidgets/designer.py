# -*- coding: utf-8 -*-
"""
Launch Qt Designer with the QFunnyWidgets plugins loaded (also the "funnywidgets-designer" console script).
Usage:
    funnywidgets-designer [form.ui ...]       start Designer (PySide6, PyQt5 or PyQt6 flavour, see QT_API)
    funnywidgets-designer --plugins-path      print the plugins directory
    funnywidgets-designer --print-env         print the environment variables to set by hand
Imports no Qt module, so it works before any binding is chosen (and on Python 2 without one).
"""
from os.path import dirname, abspath, join, exists
from os import environ, pathsep
from sys import argv, stderr
from subprocess import call

try:
    from shutil import which as _which
except:  # Python 2
    from distutils.spawn import find_executable as _which

# Designer executables per binding, most specific first. PySide6 Designer runs register*.py plugin files;
# the PyQt tools' Designer loads *plugin.py files. The plugins directory contains both.
DESIGNERS = {
    'pyside6': (['pyside6-designer'],),
    'pyqt5': (['pyqt5-tools', 'designer'], ['designer-qt5'], ['designer']),
    'pyqt6': (['pyqt6-tools', 'designer'], ['designer6'], ['designer-qt6'], ['designer']),
}  # type: dict
ORDER = ('pyside6', 'pyqt5', 'pyqt6')  # type: tuple


def packageDir():
    """
    :return: (str | unicode | QString) Directory of the QFunnyWidgets package.
    """
    return dirname(abspath(__file__))


def pluginsPath():
    """
    The Designer plugins directory: QFunnyWidgets/plugins when installed, <project>/plugins in a source checkout.

    :return: (str | None)
    """
    for candidate in (join(packageDir(), 'plugins'), join(dirname(packageDir()), 'plugins')):
        if exists(join(candidate, 'funnywidgetsinfo.py')):
            return candidate
    return None


def designerEnvironment(base=None):
    """
    Environment for Designer: plugin search paths for both plugin flavours, and the package's parent on
    PYTHONPATH so Designer's Python can import QFunnyWidgets from a source checkout too.

    :param base: (dict | None) Starting environment (default: os.environ).
    :return: dict
    """
    env = dict(environ if base is None else base)  # type: dict
    plugins = pluginsPath()  # type: str | None
    if plugins is None:
        raise RuntimeError('QFunnyWidgets Designer plugins not found next to {}'.format(packageDir()))
    for var, value in (('PYQTDESIGNERPATH', plugins), ('PYSIDE_DESIGNER_PLUGINS', plugins),
                       ('PYTHONPATH', dirname(packageDir()))):
        parts = [p for p in env.get(var, '').split(pathsep) if p]  # type: list[str]
        if value not in parts:
            env[var] = pathsep.join([value] + parts)
    return env


def findDesigner(api=None):
    """
    :param api: (str | unicode | QString | None) Preferred binding ('pyside6', 'pyqt5', 'pyqt6'); defaults to QT_API, then any.
    :return: (tuple) (command list, api) or (None, None) when no Designer is installed.
    """
    api = (api or environ.get('QT_API') or '').lower()  # type: str
    order = ((api,) if api in DESIGNERS else ()) + tuple(a for a in ORDER if a != api)  # type: tuple
    for name in order:
        for command in DESIGNERS[name]:
            if _which(command[0]):
                return list(command), name
    return None, None


def main(args=None):
    """
    :param args: (list[str] | None) Command line arguments (default: sys.argv[1:]).
    :return: (int) Exit code.
    """
    args = list(argv[1:] if args is None else args)  # type: list[str]
    if '--plugins-path' in args:
        print(pluginsPath())
        return 0 if pluginsPath() else 1
    env = designerEnvironment()  # type: dict
    if '--print-env' in args:
        for var in ('PYQTDESIGNERPATH', 'PYSIDE_DESIGNER_PLUGINS', 'PYTHONPATH'):
            print('{}={}'.format(var, env[var]))
        return 0
    command, api = findDesigner()
    if command is None:
        stderr.write('No Qt Designer found. Install one of: PySide6 (pyside6-designer), pyqt5-tools, pyqt6-tools,\n'
                     'or a system Qt Designer, then run again. Plugins: {}\n'.format(pluginsPath()))
        return 1
    env['QT_API'] = api  # widgets and plugins must use the Designer's own binding
    return call(command + args, env=env)


if __name__ == '__main__':
    from sys import exit

    exit(main())
