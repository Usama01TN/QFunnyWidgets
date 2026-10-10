# coding=utf-8
"""
puffercounter package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .puffercounter import PufferCounterWidget, PufferFooterWidget
except:
    from puffercounter import PufferCounterWidget, PufferFooterWidget

__all__ = ['PufferCounterWidget', 'PufferFooterWidget']  # type: list[str]
