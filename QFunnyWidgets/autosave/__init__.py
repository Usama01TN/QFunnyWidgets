# coding=utf-8
"""
autosave package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .autosave import AutosaveSquirrelWidget
except:
    from autosave import AutosaveSquirrelWidget

__all__ = ['AutosaveSquirrelWidget']  # type: list[str]
