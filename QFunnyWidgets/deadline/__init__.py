# coding=utf-8
"""
deadline package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .deadline import DeadlineCountdownWidget
except:
    from deadline import DeadlineCountdownWidget

__all__ = ['DeadlineCountdownWidget']  # type: list[str]
