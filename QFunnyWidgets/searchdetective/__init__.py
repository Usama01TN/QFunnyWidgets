# coding=utf-8
"""
searchdetective package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .searchdetective import SearchDetectiveWidget, DetectiveFaceWidget
except:
    from searchdetective import SearchDetectiveWidget, DetectiveFaceWidget

__all__ = ['SearchDetectiveWidget', 'DetectiveFaceWidget']  # type: list[str]
