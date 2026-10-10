# coding=utf-8
"""
copyblob package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .copyblob import CopyBlobButtonWidget
except:
    from copyblob import CopyBlobButtonWidget

__all__ = ['CopyBlobButtonWidget']  # type: list[str]
