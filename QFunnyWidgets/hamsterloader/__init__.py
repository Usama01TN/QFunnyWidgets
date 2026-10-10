# coding=utf-8
"""
hamsterloader package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .hamsterloader import HamsterLoaderWidget
except:
    from hamsterloader import HamsterLoaderWidget

__all__ = ['HamsterLoaderWidget']  # type: list[str]
