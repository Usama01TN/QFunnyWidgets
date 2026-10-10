# -*- coding: utf-8 -*-
"""
AutosaveSquirrelWidget: an autosave status indicator run by a squirrel. Saved: it naps, hugging its
acorn. Unsaved changes: it sits up, alert. Saving: it hops over and stashes the acorn in the tree.
Error: the acorn drops and rolls away while the squirrel facepalms. Built-in debounced autosave:
markDirty() -> (delay) -> saveRequested(); report back with saveFinished(ok).
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty, \
    Q_ENUMS, qVersion
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont
from ManyQt.QtWidgets import QWidget
from enum import IntEnum
from math import sin, pi


def clamp(x, a, b):
    """
    :param x: qreal | float | int
    :param a: qreal | float | int
    :param b: qreal | float | int
    :return: qreal | float | int
    """
    return a if x < a else b if x > b else x


class AutosaveSquirrelWidget(QWidget):
    """
    Autosave status indicator with a hard-working squirrel.
    """

    class Status(IntEnum):
        """
        Status enumeration class.
        """
        Saved = 0  # type: int
        Unsaved = 1  # type: int
        Saving = 2  # type: int
        Error = 3  # type: int

    Saved = Status.Saved  # type: int
    Unsaved = Status.Unsaved  # type: int
    Saving = Status.Saving  # type: int
    Error = Status.Error  # type: int
    COLORS = {0: '#3BCEAC', 1: '#FF9F1C', 2: '#4CC9F0', 3: '#E63946'}  # type: dict
    saveRequested = pyqtSignal()  # type: pyqtSignal
    statusChanged = pyqtSignal(int)  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param status: (Status | int) Initial status.
        :param autosaveDelay: (int) ms after the last markDirty() before saveRequested (0 = manual).
        :param retryDelay: (int) ms before retrying after an error (0 = no retry).
        :param squirrelColor: QColor | Qt.GlobalColor | int | str | QString
        :param saveRequested: callable | None
        :param statusChanged: callable | None
        :param args: any
        :param kwargs: any
        """
        status = kwargs.pop('status', AutosaveSquirrelWidget.Saved)  # type: int
        autosaveDelay = kwargs.pop('autosaveDelay', 1500)  # type: int
        retryDelay = kwargs.pop('retryDelay', 3000)  # type: int
        squirrelColor = kwargs.pop('squirrelColor', '#C1693C')  # type: QColor
        saveRequested = kwargs.pop('saveRequested', None)  # type: callable | None
        statusChanged = kwargs.pop('statusChanged', None)  # type: callable | None
        super(AutosaveSquirrelWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_status = AutosaveSquirrelWidget.Status(int(clamp(int(status), 0, 3)))  # type: AutosaveSquirrelWidget.Status
        self.__m_squirrelColor = QColor(squirrelColor)  # type: QColor
        if callable(saveRequested):
            self.saveRequested.connect(saveRequested)
        if callable(statusChanged):
            self.statusChanged.connect(statusChanged)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        # Debounce / retry timers.
        self.__m_autosave = QTimer(self)  # type: QTimer
        self.__m_autosave.setSingleShot(True)
        self.__m_autosave.setInterval(max(0, int(autosaveDelay)))
        self.__m_autosave.timeout.connect(self.requestSave)
        self.__m_retry = QTimer(self)  # type: QTimer
        self.__m_retry.setSingleShot(True)
        self.__m_retry.setInterval(max(0, int(retryDelay)))
        self.__m_retry.timeout.connect(self.requestSave)
        # State.
        self.__m_statusAt = 0.0  # type: float
        self.__m_savedAt = 0.0  # type: float
        self.__m_dirtyAgain = False  # type: bool
        self.__m_blinkAt = 2.0  # type: float
        # Timing.
        self.__m_clock = QElapsedTimer()  # type: QElapsedTimer
        self.__m_clock.start()
        self.__m_timer = QTimer(self)  # type: QTimer
        self.__m_timer.timeout.connect(self.update)
        self.__m_timer.start(16)

    # ---------- Helpers ----------
    def _now(self):
        """
        :return: qreal | float | int
        """
        return self.__m_clock.elapsed() / 1000.0

    def _setStatus(self, status):
        """
        :param status: int
        :return:
        """
        status = AutosaveSquirrelWidget.Status(int(status))  # type: AutosaveSquirrelWidget.Status
        if status != self.__m_status:
            self.__m_status = status  # type: AutosaveSquirrelWidget.Status
            self.__m_statusAt = self._now()  # type: float
            self.statusChanged.emit(int(status))
            self.update()

    def _ago(self):
        """
        :return: str | unicode | QString
        """
        s = int(self._now() - self.__m_savedAt)  # type: int
        if s < 10:
            return self.tr('just now')
        if s < 60:
            return self.tr('{} s ago').format(s)
        return self.tr('{} min ago').format(s // 60)

    # ---------- Public API ----------
    @pyqtSlot()
    def markDirty(self):
        """
        Tell the squirrel something changed. Starts (or restarts) the autosave countdown.
        :return: None
        """
        if self.__m_status == self.Saving:
            self.__m_dirtyAgain = True  # type: bool
            return
        self.__m_retry.stop()
        self._setStatus(self.Unsaved)
        if self.__m_autosave.interval() > 0:
            self.__m_autosave.start()

    @pyqtSlot()
    def requestSave(self):
        """
        Start saving now: emits saveRequested(). Call saveFinished() when done.
        :return:
        """
        self.__m_autosave.stop()
        self.__m_retry.stop()
        self.__m_dirtyAgain = False  # type: bool
        self._setStatus(self.Saving)
        self.saveRequested.emit()

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def saveFinished(self, ok):
        """
        :param ok: (bool) Whether the save succeeded.
        :return:
        """
        if ok:
            self.__m_savedAt = self._now()  # type: float
            self._setStatus(self.Saved)
            if self.__m_dirtyAgain:
                self.markDirty()
        else:
            self._setStatus(self.Error)
            if self.__m_retry.interval() > 0:
                self.__m_retry.start()

    def getStatus(self):
        """
        :return: AutosaveSquirrelWidget.Status
        """
        return self.__m_status

    @pyqtSlot(Status)
    @pyqtSlot(int)
    def setStatus(self, status):
        """
        :param status: AutosaveSquirrelWidget.Status | int
        :return:
        """
        self._setStatus(int(clamp(int(status), 0, 3)))

    def getAutosaveDelay(self):
        """
        :return: int
        """
        return self.__m_autosave.interval()

    @pyqtSlot(int)
    def setAutosaveDelay(self, autosaveDelay):
        """
        :param autosaveDelay: (int) ms; 0 disables autosave.
        :return:
        """
        self.__m_autosave.setInterval(max(0, int(autosaveDelay)))

    def getRetryDelay(self):
        """
        :return: int
        """
        return self.__m_retry.interval()

    @pyqtSlot(int)
    def setRetryDelay(self, retryDelay):
        """
        :param retryDelay: (int) ms; 0 disables retries.
        :return:
        """
        self.__m_retry.setInterval(max(0, int(retryDelay)))

    def getSquirrelColor(self):
        """
        :return: QColor
        """
        return self.__m_squirrelColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setSquirrelColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        self.__m_squirrelColor = color  # type: QColor
        self.update()

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(300, 76)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(180, 56)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(AutosaveSquirrelWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(AutosaveSquirrelWidget, self).hideEvent(event)

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        now = self._now()  # type: float
        h = float(self.height())  # type: float
        s = min(h, 84.0)  # type: float
        icon = QRectF(0, (h - s) / 2.0, s * 1.35, s)  # type: QRectF
        st = int(self.__m_status)  # type: int
        since = now - self.__m_statusAt  # type: float
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        self._drawScene(p, icon, s, st, since, now)
        # Status text.
        tc = QColor(self.palette().text().color())  # type: QColor
        sc = QColor(self.COLORS[st])  # type: QColor
        x0 = icon.right() + 10.0  # type: float
        f = QFont(self.font())  # type: QFont
        f.setBold(True)
        f.setPointSizeF(10.0)
        p.setFont(f)
        p.setPen(sc if st != self.Saved else tc)
        if st == self.Saved:
            main = self.tr('All changes saved')  # type: str
            sub = self.tr('Saved {}. Squirrel is napping.').format(self._ago()) if self.__m_savedAt > 0 else self.tr('Nothing to save. Zzz.')  # type: str
        elif st == self.Unsaved:
            main = self.tr('Unsaved changes')  # type: str
            sub = self.tr('Autosaving shortly...') if self.__m_autosave.isActive() else self.tr('Squirrel is on alert.')  # type: str
        elif st == self.Saving:
            main = self.tr('Saving') + '.' * (1 + int(now * 3.0) % 3)  # type: str
            sub = self.tr('Stashing your changes for winter.')  # type: str
        else:
            main = self.tr("Couldn't save")  # type: str
            sub = self.tr('The acorn got away. Retrying...') if self.__m_retry.isActive() else self.tr('The acorn got away.')  # type: str
        cy = h / 2.0  # type: float
        p.drawText(QRectF(x0, cy - 20.0, self.width() - x0, 20.0), Qt.AlignLeft | Qt.AlignVCenter, main)
        f2 = QFont(self.font())  # type: QFont
        f2.setPointSizeF(8.5)
        p.setFont(f2)
        sub2 = QColor(tc)  # type: QColor
        sub2.setAlpha(160)
        p.setPen(sub2)
        p.drawText(QRectF(x0, cy, self.width() - x0, 18.0), Qt.AlignLeft | Qt.AlignVCenter, sub)
        p.end()

    def _drawScene(self, p, icon, s, st, since, now):
        """
        :param p: QPainter
        :param icon: QRectF
        :param s: (qreal | float | int) scene size
        :param st: int
        :param since: qreal | float | int
        :param now: qreal | float | int
        :return:
        """
        ground = icon.bottom() - s * 0.1  # type: float
        # Tree trunk with a stash hole.
        trunk = QRectF(icon.right() - s * 0.3, icon.top() + s * 0.05, s * 0.24, ground - icon.top() - s * 0.05)  # type: QRectF
        p.setPen(QPen(QColor('#5A3A22'), 1.0))
        p.setBrush(QColor('#7A5232'))
        p.drawRect(trunk)
        hole = QPointF(trunk.center().x(), trunk.top() + trunk.height() * 0.4)  # type: QPointF
        p.setPen(Qt.NoPen)
        p.setBrush(QColor('#2E1C10'))
        p.drawEllipse(hole, s * 0.06, s * 0.08)
        p.setPen(QPen(QColor(0, 0, 0, 40), 1.0))
        p.drawLine(QPointF(icon.left(), ground), QPointF(icon.right(), ground))
        # Squirrel position (hops toward the tree while saving).
        sx = icon.left() + s * 0.42  # type: float
        hop = 0.0  # type: float
        if st == self.Saving:
            ph = (since % 0.9) / 0.9  # type: float
            sx += sin(ph * pi) * s * 0.18
            hop = abs(sin(ph * pi * 2.0)) * s * 0.1  # type: float
        base = QPointF(sx, ground - hop)  # type: QPointF
        self._drawSquirrel(p, base, s, st, since, now)
        # Acorns.
        if st == self.Saving:
            ph = (since % 0.9) / 0.9  # type: float
            if ph > 0.35:
                t = (ph - 0.35) / 0.65  # type: float
                a0 = QPointF(base.x() + s * 0.12, base.y() - s * 0.3)  # type: QPointF
                ax = a0.x() + (hole.x() - a0.x()) * t  # type: float
                ay = a0.y() + (hole.y() - a0.y()) * t - sin(t * pi) * s * 0.25  # type: float
                if t < 0.92:
                    self._drawAcorn(p, QPointF(ax, ay), s * 0.07, t * 540.0)
        elif st == self.Error:
            t = clamp(since / 1.2, 0.0, 1.0)  # type: float
            ax = base.x() + s * 0.12 + t * s * 0.5  # type: float
            ay = min(ground - s * 0.07, base.y() - s * 0.3 + t * t * s * 0.6)  # type: float
            self._drawAcorn(p, QPointF(ax, ay), s * 0.07, t * 720.0)
        elif st == self.Saved:
            # Little check badge.
            bc = QPointF(icon.left() + s * 0.15, icon.top() + s * 0.2)  # type: QPointF
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(self.COLORS[0]))
            p.drawEllipse(bc, s * 0.09, s * 0.09)
            p.setPen(QPen(QColor('#FFFFFF'), max(1.5, s * 0.025), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            ck = QPainterPath()  # type: QPainterPath
            ck.moveTo(bc.x() - s * 0.04, bc.y())
            ck.lineTo(bc.x() - s * 0.01, bc.y() + s * 0.03)
            ck.lineTo(bc.x() + s * 0.045, bc.y() - s * 0.035)
            p.setBrush(Qt.NoBrush)
            p.drawPath(ck)

    def _drawSquirrel(self, p, b, s, st, since, now):
        """
        Squirrel facing right, standing on point b.

        :param p: QPainter
        :param b: (QPointF) feet position
        :param s: qreal | float | int
        :param st: int
        :param since: qreal | float | int
        :param now: qreal | float | int
        :return:
        """
        col = self.__m_squirrelColor  # type: QColor
        ink = QColor('#2B1A10')  # type: QColor
        outline = QPen(col.darker(150), 1.0)  # type: QPen
        sleeping = st == self.Saved  # type: bool
        # Bushy tail.
        twitch = sin(now * (14.0 if st == self.Unsaved else 2.0)) * s * (0.03 if st == self.Unsaved else 0.01)  # type: float
        tail = QPainterPath()  # type: QPainterPath
        if sleeping:
            tail.moveTo(b.x() - s * 0.15, b.y() - s * 0.05)
            tail.cubicTo(b.x() - s * 0.45, b.y() - s * 0.1, b.x() - s * 0.35, b.y() - s * 0.5,
                         b.x() + s * 0.05, b.y() - s * 0.38)
            tail.cubicTo(b.x() - s * 0.18, b.y() - s * 0.32, b.x() - s * 0.25, b.y() - s * 0.15, b.x() - s * 0.1, b.y() - s * 0.08)
        else:
            tail.moveTo(b.x() - s * 0.12, b.y() - s * 0.08)
            tail.cubicTo(b.x() - s * 0.5, b.y() - s * 0.15, b.x() - s * 0.42, b.y() - s * 0.62 + twitch,
                         b.x() - s * 0.2, b.y() - s * 0.72 + twitch)
            tail.cubicTo(b.x() - s * 0.3, b.y() - s * 0.5, b.x() - s * 0.28, b.y() - s * 0.25, b.x() - s * 0.05, b.y() - s * 0.15)
        tail.closeSubpath()
        p.setPen(outline)
        p.setBrush(col.lighter(118))
        p.drawPath(tail)
        # Body.
        p.setBrush(col)
        if sleeping:
            p.drawEllipse(QPointF(b.x(), b.y() - s * 0.12), s * 0.17, s * 0.12)
            hc = QPointF(b.x() + s * 0.14, b.y() - s * 0.13)  # type: QPointF
        else:
            p.drawEllipse(QPointF(b.x(), b.y() - s * 0.18), s * 0.12, s * 0.17)
            p.setBrush(QColor('#F2D2B0'))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(b.x() + s * 0.03, b.y() - s * 0.15), s * 0.06, s * 0.11)
            p.setPen(outline)
            p.setBrush(col)
            hc = QPointF(b.x() + s * 0.05, b.y() - s * 0.4)  # type: QPointF
        # Head.
        p.drawEllipse(hc, s * 0.1, s * 0.09)
        ear = QPainterPath()  # type: QPainterPath
        ear.moveTo(hc.x() - s * 0.03, hc.y() - s * 0.07)
        ear.lineTo(hc.x() - s * 0.01, hc.y() - s * 0.16)
        ear.lineTo(hc.x() + s * 0.04, hc.y() - s * 0.07)
        ear.closeSubpath()
        p.drawPath(ear)
        p.setPen(Qt.NoPen)
        p.setBrush(ink)
        p.drawEllipse(QPointF(hc.x() + s * 0.1, hc.y() + s * 0.01), s * 0.018, s * 0.016)  # nose
        # Eye.
        ex = hc.x() + s * 0.035  # type: float
        ey = hc.y() - s * 0.02  # type: float
        if sleeping:
            p.setPen(QPen(ink, 1.2, Qt.SolidLine, Qt.RoundCap))
            p.setBrush(Qt.NoBrush)
            p.drawArc(QRectF(ex - s * 0.025, ey - s * 0.01, s * 0.05, s * 0.03), 180 * 16, 180 * 16)
            f = QFont(self.font())  # type: QFont
            f.setBold(True)
            ph = (now * 0.5) % 1.0  # type: float
            f.setPixelSize(max(6, int(s * (0.1 + 0.06 * ph))))
            p.setFont(f)
            zc = QColor(self.palette().text().color())  # type: QColor
            zc.setAlpha(int(200 * sin(ph * pi)))
            p.setPen(zc)
            p.drawText(QPointF(hc.x() + s * 0.08 + ph * s * 0.08, hc.y() - s * 0.12 - ph * s * 0.12), 'z')
        elif st == self.Error and since > 0.6:
            # Facepalm.
            p.setPen(QPen(col.darker(130), max(2.0, s * 0.05), Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(b.x() + s * 0.05, b.y() - s * 0.22), QPointF(ex, ey))
        else:
            big = st == self.Unsaved  # type: bool
            p.setBrush(ink)
            p.drawEllipse(QPointF(ex, ey), s * (0.026 if big else 0.02), s * (0.03 if big else 0.022))
            p.setBrush(QColor('#FFFFFF'))
            p.drawEllipse(QPointF(ex - s * 0.006, ey - s * 0.01), s * 0.007, s * 0.007)
        # Acorn held in paws (asleep: hugged; alert: held up).
        if sleeping:
            self._drawAcorn(p, QPointF(b.x() + s * 0.05, b.y() - s * 0.05), s * 0.06, 0.0)
        elif st == self.Unsaved:
            self._drawAcorn(p, QPointF(b.x() + s * 0.12, b.y() - s * 0.27), s * 0.065, sin(now * 3.0) * 10.0)
            f = QFont(self.font())  # type: QFont
            f.setBold(True)
            f.setPixelSize(max(8, int(s * 0.2)))
            p.setFont(f)
            p.setPen(QColor(self.COLORS[1]))
            p.drawText(QPointF(hc.x() + s * 0.12, hc.y() - s * 0.1), '!')

    @staticmethod
    def _drawAcorn(p, c, r, rot):
        """
        :param p: QPainter
        :param c: (QPointF) center
        :param r: (qreal | float | int) size
        :param rot: (qreal | float | int) degrees
        :return:
        """
        p.save()
        p.translate(c)
        p.rotate(rot)
        p.setPen(QPen(QColor('#8A5A2B'), 0.8))
        p.setBrush(QColor('#D9A066'))
        p.drawEllipse(QPointF(0, r * 0.25), r * 0.8, r * 0.95)
        p.setBrush(QColor('#7A5232'))
        p.drawChord(QRectF(-r * 0.95, -r * 0.75, r * 1.9, r * 1.2), 0, 180 * 16)
        p.setPen(QPen(QColor('#5A3A22'), max(1.0, r * 0.2), Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(0, -r * 0.75), QPointF(r * 0.15, -r * 1.05))
        p.restore()

    # ---------- Properties ----------
    Q_ENUMS('Status' if qVersion()[0] == '4' else Status)
    status = pyqtProperty(Status, fget=getStatus, fset=setStatus, notify=statusChanged)  # type: pyqtProperty
    autosaveDelay = pyqtProperty(int, fget=getAutosaveDelay, fset=setAutosaveDelay)  # type: pyqtProperty
    retryDelay = pyqtProperty(int, fget=getRetryDelay, fset=setRetryDelay)  # type: pyqtProperty
    squirrelColor = pyqtProperty(QColor, fget=getSquirrelColor, fset=setSquirrelColor)  # type: pyqtProperty
