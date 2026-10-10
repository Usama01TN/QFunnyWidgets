# coding=utf-8
"""
rubberduck package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .rubberduck import RubberDuckWidget
except:
    from rubberduck import RubberDuckWidget

__all__ = ['RubberDuckWidget']  # type: list[str]
