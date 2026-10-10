# coding=utf-8
"""
rockettop package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .rockettop import RocketBackToTop
except:
    from rockettop import RocketBackToTop

__all__ = ['RocketBackToTop']  # type: list[str]
