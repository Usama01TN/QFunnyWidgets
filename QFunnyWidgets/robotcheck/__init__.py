# coding=utf-8
"""
robotcheck package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .robotcheck import RobotCheckWidget
except:
    from robotcheck import RobotCheckWidget

__all__ = ['RobotCheckWidget']  # type: list[str]
