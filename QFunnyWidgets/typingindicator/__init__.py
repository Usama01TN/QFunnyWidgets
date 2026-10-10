# coding=utf-8
"""
typingindicator package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .typingindicator import TypingIndicatorWidget
except:
    from typingindicator import TypingIndicatorWidget

__all__ = ['TypingIndicatorWidget']  # type: list[str]
