# coding=utf-8
"""
ducklingpager package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .ducklingpager import DucklingPagerWidget
except:
    from ducklingpager import DucklingPagerWidget

__all__ = ['DucklingPagerWidget']  # type: list[str]
