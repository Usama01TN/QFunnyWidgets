# coding=utf-8
"""
moodslider package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .moodslider import MoodSliderWidget
except:
    from moodslider import MoodSliderWidget

__all__ = ['MoodSliderWidget']  # type: list[str]
