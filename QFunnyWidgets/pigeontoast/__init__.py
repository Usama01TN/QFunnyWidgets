# coding=utf-8
"""
pigeontoast package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .pigeontoast import PigeonToast
except:
    from pigeontoast import PigeonToast

__all__ = ['PigeonToast']  # type: list[str]
