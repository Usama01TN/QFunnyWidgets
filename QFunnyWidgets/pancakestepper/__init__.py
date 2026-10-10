# coding=utf-8
"""
pancakestepper package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .pancakestepper import PancakeStepperWidget
except:
    from pancakestepper import PancakeStepperWidget

__all__ = ['PancakeStepperWidget']  # type: list[str]
