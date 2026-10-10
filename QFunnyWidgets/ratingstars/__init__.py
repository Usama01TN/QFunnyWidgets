# coding=utf-8
"""
ratingstars package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .ratingstars import StarRatingWidget
except:
    from ratingstars import StarRatingWidget

__all__ = ['StarRatingWidget']  # type: list[str]
