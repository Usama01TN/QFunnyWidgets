# coding=utf-8
"""
batterybuddy package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .batterybuddy import BatteryBuddyWidget
except:
    from batterybuddy import BatteryBuddyWidget

__all__ = ['BatteryBuddyWidget']  # type: list[str]
