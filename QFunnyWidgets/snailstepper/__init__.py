# coding=utf-8
"""
snailstepper package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .snailstepper import SnailStepperWidget
except:
    from snailstepper import SnailStepperWidget

__all__ = ['SnailStepperWidget']  # type: list[str]
