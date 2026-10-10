# coding=utf-8
"""
presenceavatar package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .presenceavatar import PresenceAvatarWidget
except:
    from presenceavatar import PresenceAvatarWidget

__all__ = ['PresenceAvatarWidget']  # type: list[str]
