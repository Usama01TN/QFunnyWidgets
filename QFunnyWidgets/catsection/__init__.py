# coding=utf-8
"""
catsection package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .catsection import SleepyCatSectionWidget, CatHeaderWidget
except:
    from catsection import SleepyCatSectionWidget, CatHeaderWidget

__all__ = ['SleepyCatSectionWidget', 'CatHeaderWidget']  # type: list[str]
