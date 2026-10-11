#Pydroid run qt
# ManyQt crash check for Pydroid 3.
# Run it from Pydroid. If it crashes, open "manyqt_crash_log.txt" (path is printed at the start):
# it contains the exact Python line where the native crash happened.
import faulthandler
import os
import sys
import time

try:
    _here = os.path.dirname(os.path.abspath(__file__))
    if not os.access(_here, os.W_OK):
        raise OSError
except Exception:
    _here = os.getcwd()
LOG_PATH = os.path.join(_here, "manyqt_crash_log.txt")
_log = open(LOG_PATH, "w")


def step(message):
    line = "[%7.3fs] %s" % (time.time() - _t0, message)
    print(line)
    sys.stdout.flush()
    _log.write(line + "\n")
    _log.flush()


_t0 = time.time()
faulthandler.enable(file=_log, all_threads=True)  # a segfault writes its Python traceback into the log
print("log file:", LOG_PATH)
step("python %s" % sys.version.split()[0])

import ManyQt

step("ManyQt %s from %s" % (ManyQt.__version__, os.path.dirname(ManyQt.__file__)))
fixed = os.path.isfile(os.path.join(os.path.dirname(ManyQt.__file__), "_native_helpers.py"))
step("fixed ManyQt installed: %s" % fixed)
if not fixed:
    step("!!! the OLD ManyQt is still installed: reinstall the fixed one (pip install --force-reinstall .)")
step("available bindings on disk: %s" % ManyQt.availableapi())

import ManyQt.QtCore as QtCore

step("selected binding: %s | Qt %s" % (ManyQt.USED_API, QtCore.QT_VERSION_STR))
step("ManyQt folder on sys.path (should be False): %s" % (os.path.dirname(ManyQt.__file__) in sys.path))
step("ctypes imported (should be False): %s" % ("ctypes" in sys.modules))

import ManyQt.QtGui
step("ManyQt.QtGui imported")
from ManyQt.QtWidgets import QApplication, QLabel
step("ManyQt.QtWidgets imported")

app = QApplication([])
step("QApplication created")
label = QLabel("ManyQt works on this device")
label.show()
step("QLabel shown, closing in 3 s")
QtCore.QTimer.singleShot(3000, app.quit)
app.exec()
step("SUCCESS: event loop finished normally")
