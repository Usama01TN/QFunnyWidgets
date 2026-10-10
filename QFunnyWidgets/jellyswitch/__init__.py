# coding=utf-8
"""
jellyswitch package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .jellyswitch import JellySwitchWidget
except:
    from jellyswitch import JellySwitchWidget

__all__ = ['JellySwitchWidget']  # type: list[str]
