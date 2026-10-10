# -*- coding: utf-8 -*-
"""
Qt Designer registration for PySide6 (through ManyQt).
PySide6 Designer executes every "register*.py" file found in the directories listed in PYSIDE_DESIGNER_PLUGINS.
It runs the file with separate globals and locals, so module-level names are not visible inside functions:
everything lives inside registerAll(), which imports what it needs locally.
"""


def registerAll():
    """
    Register every QFunnyWidgets widget (shared table in funnywidgetsinfo.py) with PySide6 Designer.
    :return: (int) Number of widgets registered.
    """
    from os.path import dirname, abspath, exists, join
    from os import environ, pathsep
    from sys import path
    # Find this directory: __file__ when Designer provides it, else the configured plugin dirs, else sys.path.
    candidates = []  # type: list[str]
    here = globals().get('__file__')  # type: str | None
    if here:
        candidates.append(dirname(abspath(here)))
    candidates.extend(d for d in environ.get('PYSIDE_DESIGNER_PLUGINS', '').split(pathsep) if d)
    candidates.extend(path)
    pluginsDir = next((d for d in candidates if exists(join(d, 'funnywidgetsinfo.py'))), None)  # type: str | None
    if pluginsDir and pluginsDir not in path:
        path.append(pluginsDir)
    try:
        from .funnywidgetsinfo import WIDGETS, selectBinding, ensureImportable, logoPath, widgetClass, debug
    except:
        from funnywidgetsinfo import WIDGETS, selectBinding, ensureImportable, logoPath, widgetClass, debug
    selectBinding('pyside6')  # only PySide6 Designer runs register*.py files
    ensureImportable()
    from ManyQt.QtDesigner import QPyDesignerCustomWidgetCollection
    count = 0  # type: int
    for info in WIDGETS:
        QPyDesignerCustomWidgetCollection.registerCustomWidget(
            widgetClass(info), xml=info.domXml(), tool_tip=info.toolTip, icon=logoPath(info),
            group=info.group, module=info.module(), container=False)
        count += 1
    debug('PySide6 registered {} widgets'.format(count))
    return count


registerAll()
