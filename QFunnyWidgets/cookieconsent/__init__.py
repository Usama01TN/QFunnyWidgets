# coding=utf-8
"""
cookieconsent package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .cookieconsent import CookieConsentWidget
except:
    from cookieconsent import CookieConsentWidget

__all__ = ['CookieConsentWidget']  # type: list[str]
