# coding=utf-8
"""
helpowl package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .helpowl import HelpOwlWidget, HelpBubble
except:
    from helpowl import HelpOwlWidget, HelpBubble

__all__ = ['HelpOwlWidget', 'HelpBubble']  # type: list[str]
