# coding=utf-8
"""
errorgremlin package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .errorgremlin import ErrorGremlinWidget
except:
    from errorgremlin import ErrorGremlinWidget

__all__ = ['ErrorGremlinWidget']  # type: list[str]
