# coding=utf-8
"""
chameleonpicker package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .chameleonpicker import ChameleonColorPickerWidget
except:
    from chameleonpicker import ChameleonColorPickerWidget

__all__ = ['ChameleonColorPickerWidget']  # type: list[str]
