# coding=utf-8
"""
heartlike package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .heartlike import HeartLikeButtonWidget
except:
    from heartlike import HeartLikeButtonWidget

__all__ = ['HeartLikeButtonWidget']  # type: list[str]
