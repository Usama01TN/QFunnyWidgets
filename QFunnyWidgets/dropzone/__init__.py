# coding=utf-8
"""
dropzone package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .dropzone import DropZoneMonsterWidget
except:
    from dropzone import DropZoneMonsterWidget

__all__ = ['DropZoneMonsterWidget']  # type: list[str]
