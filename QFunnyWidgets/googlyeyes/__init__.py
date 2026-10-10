# coding=utf-8
"""
googlyeyes package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .googlyeyes import GooglyEyesWidget
except:
    from googlyeyes import GooglyEyesWidget

__all__ = ['GooglyEyesWidget']  # type: list[str]
