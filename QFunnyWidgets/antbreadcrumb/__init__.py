# coding=utf-8
"""
antbreadcrumb package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .antbreadcrumb import AntBreadcrumbWidget
except:
    from antbreadcrumb import AntBreadcrumbWidget

__all__ = ['AntBreadcrumbWidget']  # type: list[str]
