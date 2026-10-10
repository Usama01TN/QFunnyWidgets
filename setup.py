# -*- coding: utf-8 -*-
"""
Installation script for QFunnyWidgets (Python 2.x and 3.x).
    pip install .                 # library + mainwindow + Designer plugins
    pip install .[pyqt5]          # ...plus a Qt binding (pyqt5, pyqt6, pyside2 or pyside6)
"""
from setuptools import setup, find_packages
from os.path import abspath, dirname, join
from re import search, M
from io import open

HERE = dirname(abspath(__file__))  # type: str


def readVersion():
    """
    Read __version__ without importing the package (that would need a Qt binding).
    :return: str | unicode | QString
    """
    with open(join(HERE, 'QFunnyWidgets', '__init__.py'), encoding='utf-8') as fh:
        return search(r"^__version__ = '([^']+)'", fh.read(), M).group(1)


def readme():
    """
    :return: (str | unicode | QString) README.md used as the long description.
    """
    with open(join(HERE, 'README.md'), encoding='utf-8') as fh:
        return fh.read()


setup(
    name='QFunnyWidgets',
    version=readVersion(),
    license='MIT',
    description='35 custom-painted, animated Qt widgets with a sense of humour, for PyQt and PySide via ManyQt.',
    long_description=readme(),
    long_description_content_type='text/markdown',
    keywords='qt pyqt pyside manyqt widgets animation designer custom-widgets',
    packages=find_packages(include=['QFunnyWidgets', 'QFunnyWidgets.*']) + ['QFunnyWidgets.plugins'],
    package_dir={'QFunnyWidgets.plugins': 'plugins'},  # the single plugins/ directory ships inside the package
    package_data={'QFunnyWidgets': ['*/logo.png']},
    include_package_data=True,
    zip_safe=False,  # Designer and QIcon need real files on disk
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    install_requires=['ManyQt', 'enum34; python_version < "3.4"'],
    extras_require={
        'pyqt5': ['PyQt5'],
        'pyqt6': ['PyQt6'],
        'pyside2': ['PySide2'],
        'pyside6': ['PySide6'],
    },
    entry_points={
        'console_scripts': [
            'funnywidgets-mainwindow = QFunnyWidgets.main:main',
            'funnywidgets-designer = QFunnyWidgets.designer:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: User Interfaces',
        'Topic :: Software Development :: Widget Sets',
    ],
)
