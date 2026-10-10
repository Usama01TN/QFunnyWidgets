# coding=utf-8
"""
runawaybutton package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .runawaybutton import RunawayButtonWidget
except:
    from runawaybutton import RunawayButtonWidget

__all__ = ['RunawayButtonWidget']  # type: list[str]
