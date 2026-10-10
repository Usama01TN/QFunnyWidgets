# coding=utf-8
"""
dachshundtabs package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .dachshundtabs import DachshundTabsWidget
except:
    from dachshundtabs import DachshundTabsWidget

__all__ = ['DachshundTabsWidget']  # type: list[str]
