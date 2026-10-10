# coding=utf-8
"""
holdbutton package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .holdbutton import NervousHoldButtonWidget
except:
    from holdbutton import NervousHoldButtonWidget

__all__ = ['NervousHoldButtonWidget']  # type: list[str]
