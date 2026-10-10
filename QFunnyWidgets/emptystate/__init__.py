# coding=utf-8
"""
emptystate package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .emptystate import EmptyStateWidget
except:
    from emptystate import EmptyStateWidget

__all__ = ['EmptyStateWidget']  # type: list[str]
