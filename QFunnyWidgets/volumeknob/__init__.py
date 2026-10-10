# coding=utf-8
"""
volumeknob package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .volumeknob import VolumeKnobWidget
except:
    from volumeknob import VolumeKnobWidget

__all__ = ['VolumeKnobWidget']  # type: list[str]
