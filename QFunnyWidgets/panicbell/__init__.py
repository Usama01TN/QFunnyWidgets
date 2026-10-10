# coding=utf-8
"""
panicbell package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .panicbell import PanicBellWidget
except:
    from panicbell import PanicBellWidget

__all__ = ['PanicBellWidget']  # type: list[str]
