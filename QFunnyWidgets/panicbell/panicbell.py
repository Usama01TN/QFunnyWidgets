# -*- coding: utf-8 -*-
"""
PanicBellWidget: a notification bell whose stress level follows the unread count. It naps at zero,
swings and dings on every new notification, sweats past a threshold and completely loses it at
"99+" (spiral eyes, flashing alarm glow). Clicking clears the count and the bell sighs with relief.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QRadialGradient
from ManyQt.QtWidgets import QWidget
from math import sin, cos, pi
from random import uniform


def clamp(x, a, b):
    """
    :param x: qreal | float | int
    :param a: qreal | float | int
    :param b: qreal | float | int
    :return: qreal | float | int
    """
    return a if x < a else b if x > b else x


class Puff(object):
    """
    A sweat drop or relief puff.
    """

    def __init__(self, x=0.0, y=0.0, vx=0.0, vy=0.0, life=0.8, kind=0):
        """
        :param x: qreal | float | int
        :param y: qreal | float | int
        :param vx: qreal | float | int
        :param vy: qreal | float | int
        :param life: (qreal | float | int) s
        :param kind: (int) 0 = sweat, 1 = relief puff
        """
        self.x = float(x)  # type: float
        self.y = float(y)  # type: float
        self.vx = float(vx)  # type: float
        self.vy = float(vy)  # type: float
        self.life = float(life)  # type: float
        self.maxLife = float(life)  # type: float
        self.kind = int(kind)  # type: int


class PanicBellWidget(QWidget):
    """
    Notification bell with an anxiety problem.
    """
    clicked = pyqtSignal()  # type: pyqtSignal
    countChanged = pyqtSignal(int)  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param count: (int) Unread notifications.
        :param color: (QColor | Qt.GlobalColor | int | str | QString) Bell color.
        :param badgeColor: QColor | Qt.GlobalColor | int | str | QString
        :param panicThreshold: (int) Count at which the bell starts sweating.
        :param maxDisplay: (int) Counts above this show "<maxDisplay>+" and trigger meltdown.
        :param clearOnClick: (bool) Clicking resets the count to 0.
        :param clicked: callable | None
        :param countChanged: callable | None
        :param args: any
        :param kwargs: any
        """
        count = kwargs.pop('count', 0)  # type: int
        color = kwargs.pop('color', '#FFB703')  # type: QColor
        badgeColor = kwargs.pop('badgeColor', '#E63946')  # type: QColor
        panicThreshold = kwargs.pop('panicThreshold', 10)  # type: int
        maxDisplay = kwargs.pop('maxDisplay', 99)  # type: int
        clearOnClick = kwargs.pop('clearOnClick', True)  # type: bool
        clicked = kwargs.pop('clicked', None)  # type: callable | None
        countChanged = kwargs.pop('countChanged', None)  # type: callable | None
        super(PanicBellWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_count = max(0, int(count))  # type: int
        self.__m_color = QColor(color)  # type: QColor
        self.__m_badgeColor = QColor(badgeColor)  # type: QColor
        self.__m_panicThreshold = max(1, int(panicThreshold))  # type: int
        self.__m_maxDisplay = max(1, int(maxDisplay))  # type: int
        self.__m_clearOnClick = bool(clearOnClick)  # type: bool
        if callable(clicked):
            self.clicked.connect(clicked)
        if callable(countChanged):
            self.countChanged.connect(countChanged)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setCursor(Qt.PointingHandCursor)
        # State.
        self.__m_angle = 0.0  # type: float  # swing, degrees
        self.__m_angVel = 0.0  # type: float
        self.__m_badgePop = 1.0  # type: float
        self.__m_badgeVel = 0.0  # type: float
        self.__m_dingAt = -10.0  # type: float
        self.__m_reliefAt = -10.0  # type: float
        self.__m_puffs = []  # type: list[Puff]
        self.__m_sweatAcc = 0.0  # type: float
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

    def _stress(self):
        """
        :return: (int) 0 = asleep, 1 = alert, 2 = sweating, 3 = meltdown
        """
        if self.__m_count <= 0:
            return 0
        if self.__m_count > self.__m_maxDisplay:
            return 3
        if self.__m_count >= self.__m_panicThreshold:
            return 2
        return 1

    def _geometry(self):
        """
        :return: (tuple) pivot QPointF, bell size float
        """
        w = float(self.width())  # type: float
        h = float(self.height())  # type: float
        s = max(10.0, min(w * 0.7, h * 0.78))  # type: float
        return QPointF(w / 2.0, (h - s) / 2.0 + s * 0.06), s

    # ---------- Public API ----------
    @pyqtSlot()
    def ring(self):
        """
        Swing and ding once.
        :return:
        """
        self.__m_angVel += 260.0 * (1 if uniform(0, 1) < 0.5 else -1)
        self.__m_dingAt = self._now()  # type: float
        self.update()

    @pyqtSlot()
    def increment(self):
        """
        Add one notification.
        :return:
        """
        self.setCount(self.__m_count + 1)

    @pyqtSlot()
    def clear(self):
        """
        Reset the count to zero.
        :return:
        """
        self.setCount(0)

    def getCount(self):
        """
        :return: int
        """
        return self.__m_count

    @pyqtSlot(int)
    def setCount(self, count):
        """
        :param count: int
        :return:
        """
        count = max(0, int(count))  # type: int
        if count == self.__m_count:
            return
        old = self.__m_count  # type: int
        self.__m_count = count  # type: int
        if count > old:
            self.ring()
            self.__m_badgeVel += 8.0
        elif count == 0 and old > 0:
            self.__m_reliefAt = self._now()  # type: float
            p, s = self._geometry()
            for k in range(7):
                a = -pi / 2.0 + uniform(-0.9, 0.9)  # type: float
                self.__m_puffs.append(Puff(p.x() + s * 0.2, p.y() + s * 0.62, cos(a) * 25.0 + 30.0,
                                           sin(a) * 25.0, uniform(0.8, 1.2), 1))
        self.countChanged.emit(count)
        self.update()

    def getColor(self):
        """
        :return: QColor
        """
        return self.__m_color

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        if self.__m_color != color:
            self.__m_color = color  # type: QColor
            self.update()

    def getBadgeColor(self):
        """
        :return: QColor
        """
        return self.__m_badgeColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setBadgeColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        if self.__m_badgeColor != color:
            self.__m_badgeColor = color  # type: QColor
            self.update()

    def getPanicThreshold(self):
        """
        :return: int
        """
        return self.__m_panicThreshold

    @pyqtSlot(int)
    def setPanicThreshold(self, panicThreshold):
        """
        :param panicThreshold: int
        :return:
        """
        self.__m_panicThreshold = max(1, int(panicThreshold))  # type: int
        self.update()

    def getMaxDisplay(self):
        """
        :return: int
        """
        return self.__m_maxDisplay

    @pyqtSlot(int)
    def setMaxDisplay(self, maxDisplay):
        """
        :param maxDisplay: int
        :return:
        """
        self.__m_maxDisplay = max(1, int(maxDisplay))  # type: int
        self.update()

    def isClearOnClick(self):
        """
        :return: bool
        """
        return self.__m_clearOnClick

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setClearOnClick(self, clearOnClick):
        """
        :param clearOnClick: bool
        :return:
        """
        self.__m_clearOnClick = bool(clearOnClick)  # type: bool

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(180, 180)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(48, 48)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(PanicBellWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(PanicBellWidget, self).hideEvent(event)

    def mouseReleaseEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if e.button() == Qt.LeftButton and self.rect().contains(e.pos()):
            self.clicked.emit()
            if self.__m_clearOnClick:
                self.clear()
        super(PanicBellWidget, self).mouseReleaseEvent(e)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        stress = self._stress()  # type: int
        # Swing: damped pendulum, kept going by panic.
        if stress >= 2:
            self.__m_angVel += sin(now * (14.0 if stress == 3 else 9.0)) * (900.0 if stress == 3 else 260.0) * dt
        self.__m_angVel += (-self.__m_angle * 90.0 - self.__m_angVel * 3.2) * dt
        self.__m_angle = clamp(self.__m_angle + self.__m_angVel * dt, -40.0, 40.0)  # type: float
        self.__m_badgeVel += ((1.0 - self.__m_badgePop) * 300.0 - self.__m_badgeVel * 12.0) * dt
        self.__m_badgePop += self.__m_badgeVel * dt
        # Sweat.
        p, s = self._geometry()
        if stress >= 2:
            self.__m_sweatAcc += dt * (5.0 if stress == 2 else 12.0)
            while self.__m_sweatAcc > 1.0:
                self.__m_sweatAcc -= 1.0
                side = -1.0 if uniform(0, 1) < 0.5 else 1.0  # type: float
                self.__m_puffs.append(Puff(p.x() + side * s * 0.25, p.y() + s * 0.3, side * uniform(40, 90),
                                           -uniform(60, 120), 0.7, 0))
        alive = []  # type: list[Puff]
        for pf in self.__m_puffs:
            if pf.kind == 0:
                pf.vy += 500.0 * dt
            pf.x += pf.vx * dt
            pf.y += pf.vy * dt
            pf.life -= dt
            if pf.life > 0:
                alive.append(pf)
        self.__m_puffs = alive  # type: list[Puff]
        self.update()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        now = self._now()  # type: float
        pivot, s = self._geometry()
        stress = self._stress()  # type: int
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        # Meltdown alarm glow.
        if stress == 3:
            a = 0.5 + 0.5 * sin(now * 12.0)  # type: float
            glow = QRadialGradient(QPointF(pivot.x(), pivot.y() + s * 0.45), s * 0.75)  # type: QRadialGradient
            gc = QColor('#FF2E3F')  # type: QColor
            gc.setAlpha(int(120 * a))
            glow.setColorAt(0.0, gc)
            gc.setAlpha(0)
            glow.setColorAt(1.0, gc)
            p.setPen(Qt.NoPen)
            p.setBrush(glow)
            p.drawEllipse(QPointF(pivot.x(), pivot.y() + s * 0.45), s * 0.75, s * 0.75)
        # Ding arcs.
        since = now - self.__m_dingAt  # type: float
        if since < 0.6 or stress == 3:
            t = (since / 0.6) if since < 0.6 else (now * 2.0) % 1.0  # type: float
            ac = QColor(self.palette().text().color())  # type: QColor
            ac.setAlpha(int(200 * (1.0 - t)))
            pen = QPen(ac, max(1.5, s * 0.025), Qt.SolidLine, Qt.RoundCap)  # type: QPen
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            cy = pivot.y() + s * 0.4  # type: float
            for k in range(2):
                rr = s * (0.5 + 0.12 * k + 0.1 * t)  # type: float
                p.drawArc(QRectF(pivot.x() - rr, cy - rr, rr * 2, rr * 2), -25 * 16, 50 * 16)
                p.drawArc(QRectF(pivot.x() - rr, cy - rr, rr * 2, rr * 2), 155 * 16, 50 * 16)
        p.save()
        p.translate(pivot)
        shake = 0.0 if stress < 3 else 2.0  # type: float
        p.translate(uniform(-shake, shake), uniform(-shake, shake))
        p.rotate(self.__m_angle)
        self._drawBell(p, s, stress, now)
        p.restore()
        # Badge (not rotating, so it stays readable).
        if self.__m_count > 0:
            self._drawBadge(p, pivot, s)
        # Puffs.
        p.setPen(Qt.NoPen)
        for pf in self.__m_puffs:
            a = clamp(pf.life / pf.maxLife, 0.0, 1.0)  # type: float
            if pf.kind == 0:
                col = QColor('#7FD6FF')  # type: QColor
                col.setAlpha(int(255 * a))
                drop = QPainterPath()  # type: QPainterPath
                ds = max(2.0, s * 0.025)  # type: float
                drop.moveTo(pf.x, pf.y - ds * 1.6)
                drop.quadTo(pf.x + ds, pf.y, pf.x, pf.y + ds)
                drop.quadTo(pf.x - ds, pf.y, pf.x, pf.y - ds * 1.6)
                p.fillPath(drop, col)
            else:
                col = QColor(220, 225, 235)  # type: QColor
                col.setAlpha(int(170 * a))
                p.setBrush(col)
                rr = s * (0.03 + 0.06 * (1.0 - a))  # type: float
                p.drawEllipse(QPointF(pf.x, pf.y), rr, rr)
        p.end()

    def _drawBell(self, p, s, stress, now):
        """
        Draw the bell in pivot coordinates (0, 0 = hanging point).

        :param p: QPainter
        :param s: (qreal | float | int) size
        :param stress: int
        :param now: qreal | float | int
        :return:
        """
        bc = self.__m_color  # type: QColor
        # Clapper swings a bit behind.
        p.setPen(Qt.NoPen)
        p.setBrush(bc.darker(150))
        p.drawEllipse(QPointF(-self.__m_angle * s * 0.004, s * 0.86), s * 0.09, s * 0.09)
        # Body.
        body = QPainterPath()  # type: QPainterPath
        top = s * 0.1  # type: float
        bottom = s * 0.78  # type: float
        body.moveTo(-s * 0.08, top)
        body.cubicTo(-s * 0.36, top + s * 0.02, -s * 0.34, s * 0.45, -s * 0.38, s * 0.62)
        body.quadTo(-s * 0.4, bottom - s * 0.04, -s * 0.47, bottom)
        body.lineTo(s * 0.47, bottom)
        body.quadTo(s * 0.4, bottom - s * 0.04, s * 0.38, s * 0.62)
        body.cubicTo(s * 0.34, s * 0.45, s * 0.36, top + s * 0.02, s * 0.08, top)
        body.closeSubpath()
        grad = QRadialGradient(QPointF(-s * 0.15, s * 0.3), s * 0.7)  # type: QRadialGradient
        grad.setColorAt(0.0, bc.lighter(130))
        grad.setColorAt(1.0, bc.darker(115))
        p.setBrush(grad)
        p.setPen(QPen(bc.darker(150), max(1.5, s * 0.02)))
        p.drawPath(body)
        p.drawRoundedRect(QRectF(-s * 0.5, bottom - s * 0.01, s, s * 0.07), s * 0.035, s * 0.035)
        p.setBrush(bc.darker(110))
        p.drawEllipse(QPointF(0, top - s * 0.02), s * 0.06, s * 0.06)
        # Face.
        ink = QColor('#3A2A10')  # type: QColor
        fy = s * 0.42  # type: float
        ex = s * 0.11  # type: float
        pen = QPen(ink, max(1.2, s * 0.022), Qt.SolidLine, Qt.RoundCap)  # type: QPen
        relieved = now - self.__m_reliefAt < 1.5  # type: bool
        if stress == 0:
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            for d in (-1.0, 1.0):
                if relieved:
                    p.drawArc(QRectF(d * ex - s * 0.045, fy - s * 0.04, s * 0.09, s * 0.06), 0, 180 * 16)
                else:
                    p.drawArc(QRectF(d * ex - s * 0.045, fy - s * 0.03, s * 0.09, s * 0.06), 180 * 16, 180 * 16)
            breathe = 1.0 + 0.2 * sin(now * 2.5)  # type: float
            if relieved:
                p.drawArc(QRectF(-s * 0.06, fy + s * 0.06, s * 0.12, s * 0.07), 200 * 16, 140 * 16)
            else:
                p.drawEllipse(QPointF(0, fy + s * 0.11), s * 0.025 * breathe, s * 0.03 * breathe)
            # Sleeping "z".
            if not relieved:
                f = QFont(self.font())  # type: QFont
                f.setBold(True)
                for k in range(2):
                    ph = (now * 0.5 + k * 0.5) % 1.0  # type: float
                    f.setPointSizeF(max(5.0, s * (0.06 + 0.05 * ph)))
                    p.setFont(f)
                    zc = QColor(self.palette().text().color())  # type: QColor
                    zc.setAlpha(int(220 * sin(ph * pi)))
                    p.setPen(zc)
                    p.drawText(QPointF(s * 0.28 + ph * s * 0.12, fy - s * 0.15 - ph * s * 0.25), 'z')
            return
        if stress == 3:
            # Spiral eyes.
            p.setPen(Qt.NoPen)
            p.setBrush(QColor('#FFFFFF'))
            for d in (-1.0, 1.0):
                p.drawEllipse(QPointF(d * ex, fy), s * 0.075, s * 0.075)
            p.setPen(QPen(ink, max(1.0, s * 0.012), Qt.SolidLine, Qt.RoundCap))
            p.setBrush(Qt.NoBrush)
            for d in (-1.0, 1.0):
                spiral = QPainterPath()  # type: QPainterPath
                for k in range(36):
                    a = k * 0.5 + now * 12.0 * d  # type: float
                    rr = s * 0.0019 * k  # type: float
                    pt = QPointF(d * ex + cos(a) * rr, fy + sin(a) * rr)  # type: QPointF
                    if k == 0:
                        spiral.moveTo(pt)
                    else:
                        spiral.lineTo(pt)
                p.drawPath(spiral)
        else:
            er = s * (0.04 if stress == 1 else 0.055)  # type: float
            for d in (-1.0, 1.0):
                p.setPen(Qt.NoPen)
                p.setBrush(QColor('#FFFFFF'))
                p.drawEllipse(QPointF(d * ex, fy), er, er * 1.1)
                p.setBrush(ink)
                look = sin(now * 7.0) * er * 0.4 if stress == 2 else 0.0  # type: float
                p.drawEllipse(QPointF(d * ex + look, fy + er * 0.1), er * 0.55, er * 0.6)
            if stress == 2:
                p.setPen(pen)
                for d in (-1.0, 1.0):
                    p.drawLine(QPointF(d * (ex + s * 0.06), fy - s * 0.07), QPointF(d * (ex - s * 0.04), fy - s * 0.1))
        # Mouth.
        p.setPen(pen)
        if stress == 1:
            p.setBrush(Qt.NoBrush)
            p.drawArc(QRectF(-s * 0.06, fy + s * 0.04, s * 0.12, s * 0.08), 200 * 16, 140 * 16)
        else:
            p.setBrush(QColor('#7A1F1F'))
            o = 1.0 + 0.25 * sin(now * (20.0 if stress == 3 else 8.0))  # type: float
            p.drawEllipse(QPointF(0, fy + s * 0.12), s * 0.045 * o, s * (0.04 if stress == 2 else 0.06) * o)

    def _drawBadge(self, p, pivot, s):
        """
        :param p: QPainter
        :param pivot: QPointF
        :param s: qreal | float | int
        :return:
        """
        text = str(self.__m_count) if self.__m_count <= self.__m_maxDisplay else '{}+'.format(self.__m_maxDisplay)  # type: str
        f = QFont(self.font())  # type: QFont
        f.setBold(True)
        f.setPointSizeF(max(6.0, s * 0.075))
        p.setFont(f)
        fm = p.fontMetrics()
        tw = float(fm.horizontalAdvance(text) if hasattr(fm, 'horizontalAdvance') else fm.width(text))  # type: float
        bh = s * 0.2  # type: float
        bw = max(bh, tw + bh * 0.6)  # type: float
        c = QPointF(pivot.x() + s * 0.3, pivot.y() + s * 0.2)  # type: QPointF
        p.save()
        p.translate(c)
        k = max(0.2, self.__m_badgePop)  # type: float
        p.scale(k, k)
        rect = QRectF(-bw / 2.0, -bh / 2.0, bw, bh)  # type: QRectF
        p.setPen(QPen(QColor('#FFFFFF'), max(1.5, s * 0.015)))
        p.setBrush(self.__m_badgeColor)
        p.drawRoundedRect(rect, bh / 2.0, bh / 2.0)
        p.setPen(QColor('#FFFFFF'))
        p.drawText(rect, Qt.AlignCenter, text)
        p.restore()

    # ---------- Properties ----------
    count = pyqtProperty(int, fget=getCount, fset=setCount, notify=countChanged)  # type: pyqtProperty
    color = pyqtProperty(QColor, fget=getColor, fset=setColor)  # type: pyqtProperty
    badgeColor = pyqtProperty(QColor, fget=getBadgeColor, fset=setBadgeColor)  # type: pyqtProperty
    panicThreshold = pyqtProperty(int, fget=getPanicThreshold, fset=setPanicThreshold)  # type: pyqtProperty
    maxDisplay = pyqtProperty(int, fget=getMaxDisplay, fset=setMaxDisplay)  # type: pyqtProperty
    clearOnClick = pyqtProperty(bool, fget=isClearOnClick, fset=setClearOnClick)  # type: pyqtProperty
