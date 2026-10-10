# -*- coding: utf-8 -*-
"""
Qt Designer plugins for PyQt4 / PyQt5 / PyQt6 (through ManyQt).
Designer's PyQt loader imports every "*plugin.py" module found in the directories listed in PYQTDESIGNERPATH
and instantiates each QPyDesignerCustomWidgetPlugin subclass it finds in the module namespace. One class per
widget is generated below from the shared table in funnywidgetsinfo.py.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .funnywidgetsinfo import WIDGETS, selectBinding, ensureImportable, logoPath, widgetClass, debug
except:
    from funnywidgetsinfo import WIDGETS, selectBinding, ensureImportable, logoPath, widgetClass, debug

selectBinding()  # same binding as the hosting Designer, before ManyQt is imported.
ensureImportable()

from ManyQt.QtDesigner import QPyDesignerCustomWidgetPlugin
from ManyQt.QtGui import QIcon


def makePluginClass(info):
    """
    Build the Designer plugin class for one widget.

    :param info: WidgetInfo
    :return: type
    """

    def __init__(self, parent=None):
        """
        :param parent: QObject | None
        """
        QPyDesignerCustomWidgetPlugin.__init__(self, parent)
        self._initialized = False  # type bool

    def initialize(self, core):
        """
        :param core: QDesignerFormEditorInterface
        :return:
        """
        self._initialized = True  # type bool

    def isInitialized(self):
        """
        :return: bool
        """
        return self._initialized

    def createWidget(self, parent):
        """
        :param parent: QWidget
        :return: QWidget
        """
        return widgetClass(info)(parent)

    def name(self):
        """
        :return: str | unicode | QString
        """
        return info.className

    def group(self):
        """
        :return: str | unicode | QString
        """
        return info.group

    def icon(self):
        """
        :return: QIcon
        """
        return QIcon(logoPath(info))

    def toolTip(self):
        """
        :return: str | unicode | QString
        """
        return info.toolTip

    def whatsThis(self):
        """
        :return: str | unicode | QString
        """
        return '{}: {}'.format(info.title, info.toolTip)

    def isContainer(self):
        """
        :return: bool
        """
        return False

    def domXml(self):
        """
        :return: str | unicode | QString
        """
        return info.domXml()

    def includeFile(self):
        """
        :return: (str | unicode | QString) pyuic turns this into "from QFunnyWidgets.<package> import <ClassName>".
        """
        return info.module()

    members = {'__init__': __init__, 'initialize': initialize, 'isInitialized': isInitialized,
               'createWidget': createWidget, 'name': name, 'group': group, 'icon': icon, 'toolTip': toolTip,
               'whatsThis': whatsThis, 'isContainer': isContainer, 'domXml': domXml, 'includeFile': includeFile,
               '__doc__': 'Qt Designer plugin for {}.'.format(info.className)}  # type: dict
    return type(str(info.className + 'Plugin'), (QPyDesignerCustomWidgetPlugin,), members)


# Expose one plugin class per widget at module level, where Designer looks for them.
PLUGIN_CLASSES = []  # type: list[type]
for _info in WIDGETS:
    _cls = makePluginClass(_info)  # type: type
    globals()[_cls.__name__] = _cls
    PLUGIN_CLASSES.append(_cls)
debug('PyQt plugin module loaded {} widget plugins'.format(len(PLUGIN_CLASSES)))
del _info, _cls
