# -*- coding: utf-8 -*-
"""
DachshundTabsWidget: a segmented control / tab bar whose selection highlight is a dachshund. Pick
another tab and the front half of the dog runs ahead while the back half lags behind, so its body
stretches across the tabs before the rear catches up. Head, ears and wagging tail included.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QFontMetricsF, QLinearGradient
from ManyQt.QtWidgets import QWidget
from math import sin, pi


def eventPos(e):
    """
    Mouse position of an event as QPointF (Qt 6 position() / Qt 5 localPos() / Qt 4 posF()).

    :param e: QMouseEvent | QDropEvent
    :return: QPointF
    """
    if hasattr(e, 'position'):
        return e.position()
    if hasattr(e, 'localPos'):
        return e.localPos()
    return e.posF()


def clamp(x, a, b):
    """
    :param x: qreal | float | int
    :param a: qreal | float | int
    :param b: qreal | float | int
    :return: qreal | float | int
    """
    return a if x < a else b if x > b else x


DEFAULT_TABS = ['Overview', 'Activity', 'Settings', 'Billing']  # type: list[str]


class DachshundTabsWidget(QWidget):
    """
    Segmented control with a stretchy sausage dog as the selection indicator.
    """
    currentChanged = pyqtSignal(int)  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param tabs: (list[str | unicode | QString]) Segment labels.
        :param current: (int) Selected index.
        :param dogColor: QColor | Qt.GlobalColor | int | str | QString
        :param trackColor: QColor | Qt.GlobalColor | int | str | QString
        :param currentChanged: callable | None
        :param args: any
        :param kwargs: any
        """
        tabs = kwargs.pop('tabs', DEFAULT_TABS)  # type: list[str]
        current = kwargs.pop('current', 0)  # type: int
        dogColor = kwargs.pop('dogColor', '#B5651D')  # type: QColor
        trackColor = kwargs.pop('trackColor', QColor(127, 127, 127, 40))  # type: QColor
        currentChanged = kwargs.pop('currentChanged', None)  # type: callable | None
        super(DachshundTabsWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_tabs = list(tabs) or list(DEFAULT_TABS)  # type: list[str]
        self.__m_current = int(clamp(int(current), 0, len(self.__m_tabs) - 1))  # type: int
        self.__m_dogColor = QColor(dogColor)  # type: QColor
        self.__m_trackColor = QColor(trackColor)  # type: QColor
        if callable(currentChanged):
            self.currentChanged.connect(currentChanged)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.PointingHandCursor)
        # State: the dog's two ends move independently.
        self.__m_left = -1.0  # type: float
        self.__m_right = -1.0  # type: float
        self.__m_vl = 0.0  # type: float
        self.__m_vr = 0.0  # type: float
        self.__m_facing = 1.0  # type: float
        self.__m_changedAt = -10.0  # type: float
        self.__m_hover = -1  # type: int
        self.__m_last = 0.0  # type: float
        # Timing.
        self.__m_clock = QElapsedTimer()  # type: QElapsedTimer
        self.__m_clock.start()
        self.__m_timer = QTimer(self)  # type: QTimer
        self.__m_timer.timeout.connect(self._tick)
        self.__m_timer.start(16)

    # ---------- Helpers ----------
    def _now(self):
        """
        :return: qreal | float | int
        """
        return self.__m_clock.elapsed() / 1000.0

    def _track(self):
        """
        :return: QRectF
        """
        h = float(self.height())  # type: float
        th = clamp(h - 18.0, 30.0, 46.0)  # type: float
        return QRectF(2.0, h - th - 2.0, self.width() - 4.0, th)

    def _segments(self):
        """
        :return: list[QRectF]
        """
        t = self._track()  # type: QRectF
        n = len(self.__m_tabs)  # type: int
        sw = t.width() / n  # type: float
        return [QRectF(t.left() + i * sw, t.top(), sw, t.height()) for i in range(n)]

    # ---------- Public API ----------
    def getCurrent(self):
        """
        :return: int
        """
        return self.__m_current

    @pyqtSlot(int)
    def setCurrent(self, current):
        """
        :param current: int
        :return:
        """
        current = int(clamp(int(current), 0, len(self.__m_tabs) - 1))  # type: int
        if current != self.__m_current:
            self.__m_facing = 1.0 if current > self.__m_current else -1.0  # type: float
            self.__m_current = current  # type: int
            self.__m_changedAt = self._now()  # type: float
            self.currentChanged.emit(current)
            self.update()

    def getTabs(self):
        """
        :return: list[str | unicode | QString]
        """
        return list(self.__m_tabs)

    @pyqtSlot(list)
    def setTabs(self, tabs):
        """
        :param tabs: list[str]
        :return:
        """
        self.__m_tabs = list(tabs) or list(DEFAULT_TABS)  # type: list[str]
        self.__m_current = min(self.__m_current, len(self.__m_tabs) - 1)  # type: int
        self.__m_left = -1.0  # type: float
        self.update()

    def getDogColor(self):
        """
        :return: QColor
        """
        return self.__m_dogColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setDogColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        self.__m_dogColor = color  # type: QColor
        self.update()

    def getTrackColor(self):
        """
        :return: QColor
        """
        return self.__m_trackColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setTrackColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        self.__m_trackColor = color  # type: QColor
        self.update()

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(120 * len(self.__m_tabs), 64)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(60 * len(self.__m_tabs), 50)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(DachshundTabsWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(DachshundTabsWidget, self).hideEvent(event)

    def resizeEvent(self, event):
        """
        :param event: QResizeEvent
        :return:
        """
        super(DachshundTabsWidget, self).resizeEvent(event)
        self.__m_left = -1.0  # type: float  # snap to the new geometry

    def mouseMoveEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        self.__m_hover = next((i for i, r in enumerate(self._segments()) if r.contains(eventPos(e))), -1)  # type: int
        super(DachshundTabsWidget, self).mouseMoveEvent(e)

    def leaveEvent(self, e):
        """
        :param e: QEvent
        :return:
        """
        self.__m_hover = -1  # type: int
        super(DachshundTabsWidget, self).leaveEvent(e)

    def mouseReleaseEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if e.button() == Qt.LeftButton:
            for i, r in enumerate(self._segments()):
                if r.contains(eventPos(e)):
                    self.setCurrent(i)
                    break
        super(DachshundTabsWidget, self).mouseReleaseEvent(e)

    def keyPressEvent(self, e):
        """
        :param e: QKeyEvent
        :return:
        """
        if e.key() == Qt.Key_Right:
            self.setCurrent(self.__m_current + 1)
        elif e.key() == Qt.Key_Left:
            self.setCurrent(self.__m_current - 1)
        else:
            super(DachshundTabsWidget, self).keyPressEvent(e)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        seg = self._segments()[self.__m_current]  # type: QRectF
        pad = 4.0  # type: float
        tl = seg.left() + pad  # type: float
        tr = seg.right() - pad  # type: float
        if self.__m_left < 0:
            self.__m_left, self.__m_right = tl, tr
        # The end in the direction of travel is the head: it leads. The tail end waits, then follows.
        delay = now - self.__m_changedAt < 0.18  # type: bool
        kFront, cFront = 180.0, 18.0  # type: float
        kBack, cBack = (0.0, 12.0) if delay else (110.0, 16.0)  # type: float
        if self.__m_facing > 0:
            self.__m_vr += ((tr - self.__m_right) * kFront - self.__m_vr * cFront) * dt
            self.__m_vl += ((tl - self.__m_left) * kBack - self.__m_vl * cBack) * dt
        else:
            self.__m_vl += ((tl - self.__m_left) * kFront - self.__m_vl * cFront) * dt
            self.__m_vr += ((tr - self.__m_right) * kBack - self.__m_vr * cBack) * dt
        self.__m_left += self.__m_vl * dt
        self.__m_right += self.__m_vr * dt
        if self.__m_right - self.__m_left < 20.0:
            mid = (self.__m_left + self.__m_right) / 2.0  # type: float
            self.__m_left, self.__m_right = mid - 10.0, mid + 10.0
        self.update()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        now = self._now()  # type: float
        track = self._track()  # type: QRectF
        segs = self._segments()  # type: list[QRectF]
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        p.setPen(Qt.NoPen)
        p.setBrush(self.__m_trackColor)
        p.drawRoundedRect(track, track.height() / 2.0, track.height() / 2.0)
        tc = QColor(self.palette().text().color())  # type: QColor
        if 0 <= self.__m_hover != self.__m_current:
            hc = QColor(tc)  # type: QColor
            hc.setAlpha(18)
            p.setBrush(hc)
            hs = segs[self.__m_hover].adjusted(4, 4, -4, -4)  # type: QRectF
            p.drawRoundedRect(hs, hs.height() / 2.0, hs.height() / 2.0)
        self._drawDog(p, track, now)
        # Labels on top of the dog.
        f = QFont(self.font())  # type: QFont
        f.setPointSizeF(clamp(track.height() * 0.27, 8.5, 11.0))
        fm = QFontMetricsF(f)  # type: QFontMetricsF
        for i, r in enumerate(segs):
            onDog = self.__m_left <= r.center().x() <= self.__m_right  # type: bool
            f.setBold(i == self.__m_current)
            p.setFont(f)
            if onDog:
                p.setPen(QColor('#FFF8EE'))
            else:
                lc = QColor(tc)  # type: QColor
                lc.setAlpha(170)
                p.setPen(lc)
            p.drawText(r, Qt.AlignCenter, fm.elidedText(self.__m_tabs[i], Qt.ElideRight, r.width() - 36.0))
        if self.hasFocus():
            fc = QColor(tc)  # type: QColor
            fc.setAlpha(60)
            p.setPen(QPen(fc, 1.0, Qt.DashLine))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(track.adjusted(-1, -1, 1, 1), track.height() / 2.0, track.height() / 2.0)
        p.end()

    def _drawDog(self, p, track, now):
        """
        :param p: QPainter
        :param track: QRectF
        :param now: qreal | float | int
        :return:
        """
        dc = self.__m_dogColor  # type: QColor
        ink = QColor('#2B1A10')  # type: QColor
        L = self.__m_left  # type: float
        R = self.__m_right  # type: float
        bh = track.height() - 10.0  # type: float
        cy = track.center().y()  # type: float
        moving = abs(self.__m_vl) + abs(self.__m_vr) > 30.0  # type: bool
        face = self.__m_facing  # type: float
        stretch = (R - L) / max(1.0, self._segments()[0].width() - 8.0)  # type: float
        # Legs (4 little stumps, scurrying when moving).
        p.setPen(QPen(dc.darker(130), max(3.0, bh * 0.16), Qt.SolidLine, Qt.RoundCap))
        for k, x in enumerate((L + bh * 0.45, L + bh * 0.85, R - bh * 0.85, R - bh * 0.45)):
            swing = sin(now * 22.0 + k * pi / 2.0) * bh * 0.12 if moving else 0.0  # type: float
            p.drawLine(QPointF(x, cy + bh * 0.3), QPointF(x + swing, cy + bh * 0.55))
        # Tail at the rear end.
        rear = L if face > 0 else R  # type: float
        wag = sin(now * (18.0 if not moving else 10.0)) * 0.6  # type: float
        p.setPen(QPen(dc.darker(115), max(2.5, bh * 0.12), Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        tail = QPainterPath()  # type: QPainterPath
        tail.moveTo(rear, cy - bh * 0.1)
        tail.quadTo(rear - face * bh * 0.45, cy - bh * (0.4 + 0.25 * wag), rear - face * bh * 0.55, cy - bh * (0.75 + 0.3 * wag))
        p.drawPath(tail)
        # Body: the selection pill.
        body = QRectF(L, cy - bh / 2.0, R - L, bh)  # type: QRectF
        grad = QLinearGradient(body.topLeft(), body.bottomLeft())  # type: QLinearGradient
        grad.setColorAt(0.0, dc.lighter(115))
        grad.setColorAt(1.0, dc.darker(110))
        p.setPen(QPen(dc.darker(140), 1.2))
        p.setBrush(grad)
        p.drawRoundedRect(body, bh / 2.0, bh / 2.0)
        # Belly line gets "thinner" the more it stretches.
        bl = QColor(255, 255, 255, int(clamp(60 - (stretch - 1.0) * 20, 15, 60)))  # type: QColor
        p.setPen(QPen(bl, max(1.0, bh * 0.08 / max(1.0, stretch * 0.6)), Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(L + bh * 0.6, cy + bh * 0.28), QPointF(R - bh * 0.6, cy + bh * 0.28))
        # Head at the front end, poking above the track.
        front = R if face > 0 else L  # type: float
        hc = QPointF(front + face * bh * 0.05, cy - bh * 0.45)  # type: QPointF
        hr = bh * 0.48  # type: float
        p.setPen(QPen(dc.darker(140), 1.2))
        p.setBrush(dc)
        p.drawEllipse(hc, hr, hr * 0.9)
        # Snout.
        snout = QRectF(hc.x() + (0 if face > 0 else -hr * 1.1), hc.y() - hr * 0.05, hr * 1.1, hr * 0.62)  # type: QRectF
        p.drawRoundedRect(snout, hr * 0.3, hr * 0.3)
        p.setPen(Qt.NoPen)
        p.setBrush(ink)
        p.drawEllipse(QPointF(hc.x() + face * hr * 1.05, hc.y() + hr * 0.1), hr * 0.16, hr * 0.13)
        # Eye.
        p.drawEllipse(QPointF(hc.x() + face * hr * 0.3, hc.y() - hr * 0.25), hr * 0.12, hr * (0.04 if moving and stretch > 1.6 else 0.13))
        # Floppy ear (flaps when running).
        flap = sin(now * 16.0) * 0.25 if moving else 0.0  # type: float
        ear = QPainterPath()  # type: QPainterPath
        ex = hc.x() - face * hr * 0.25  # type: float
        ear.moveTo(ex, hc.y() - hr * 0.6)
        ear.quadTo(ex - face * hr * (0.7 + flap), hc.y() - hr * 0.1, ex - face * hr * (0.35 + flap), hc.y() + hr * 0.55)
        ear.quadTo(ex + face * hr * 0.1, hc.y() + hr * 0.1, ex, hc.y() - hr * 0.6)
        p.setPen(QPen(dc.darker(150), 1.0))
        p.setBrush(dc.darker(130))
        p.drawPath(ear)
        # Tongue out when it has been running far.
        if moving and stretch > 1.5:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor('#FF7A90'))
            p.drawEllipse(QPointF(hc.x() + face * hr * 0.75, hc.y() + hr * 0.62), hr * 0.14, hr * 0.2)

    # ---------- Properties ----------
    current = pyqtProperty(int, fget=getCurrent, fset=setCurrent, notify=currentChanged)  # type: pyqtProperty
    tabs = pyqtProperty('QStringList', fget=getTabs, fset=setTabs)  # type: pyqtProperty
    dogColor = pyqtProperty(QColor, fget=getDogColor, fset=setDogColor)  # type: pyqtProperty
    trackColor = pyqtProperty(QColor, fget=getTrackColor, fset=setTrackColor)  # type: pyqtProperty
