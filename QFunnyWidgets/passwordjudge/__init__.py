# coding=utf-8
"""
passwordjudge package.
"""
from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .passwordjudge import PasswordJudgeWidget, JudgeFaceWidget, passwordStrength
except:
    from passwordjudge import PasswordJudgeWidget, JudgeFaceWidget, passwordStrength

__all__ = ['PasswordJudgeWidget', 'JudgeFaceWidget', 'passwordStrength']  # type: list[str]
