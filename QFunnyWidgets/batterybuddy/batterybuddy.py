# -*- coding: utf-8 -*-
"""
BatteryBuddyWidget: a battery status indicator with a personality. Full, it bounces with energy;
half full it is fine; low, it yawns; nearly empty it sweats and slumps; at the very end it flickers
and begs to be plugged in. While charging it happily munches electricity under a pulsing bolt.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QLinearGradient
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


class Spark(object):
    """
    An electric spark.
    """

    def __init__(self, x=0.0, y=0.0, vx=0.0, vy=0.0, life=0.4):
        """
        :param x: qreal | float | int
        :param y: qreal | float | int
        :param vx: qreal | float | int
        :param vy: qreal | float | int
        :param life: (qreal | float | int) s
        """
        self.x = float(x)  # type: float
        self.y = float(y)  # type: float
        self.vx = float(vx)  # type: float
        self.vy = float(vy)  # type: float
        self.life = float(life)  # type: float


class BatteryBuddyWidget(QWidget):
    """
    Battery indicator with feelings about its charge level.
    """
    levelChanged = pyqtSignal(int)  # type: pyqtSignal
    chargingChanged = pyqtSignal(bool)  # type: pyqtSignal
    lowBattery = pyqtSignal()  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param level: (int) 0..100
        :param charging: bool
        :param lowThreshold: (int) Level below which lowBattery() is emitted.
        :param caseColor: QColor | Qt.GlobalColor | int | str | QString
        :param showLabel: bool
        :param levelChanged: callable | None
        :param chargingChanged: callable | None
        :param lowBattery: callable | None
        :param args: any
        :param kwargs: any
        """
        level = kwargs.pop('level', 75)  # type: int
        charging = kwargs.pop('charging', False)  # type: bool
        lowThreshold = kwargs.pop('lowThreshold', 20)  # type: int
        caseColor = kwargs.pop('caseColor', '#8B8FA3')  # type: QColor
        showLabel = kwargs.pop('showLabel', True)  # type: bool
        levelChanged = kwargs.pop('levelChanged', None)  # type: callable | None
        chargingChanged = kwargs.pop('chargingChanged', None)  # type: callable | None
        lowBattery = kwargs.pop('lowBattery', None)  # type: callable | None
        super(BatteryBuddyWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_level = int(clamp(int(level), 0, 100))  # type: int
        self.__m_charging = bool(charging)  # type: bool
        self.__m_lowThreshold = int(clamp(int(lowThreshold), 1, 99))  # type: int
        self.__m_caseColor = QColor(caseColor)  # type: QColor
        self.__m_showLabel = bool(showLabel)  # type: bool
        for sig, cb in ((self.levelChanged, levelChanged), (self.chargingChanged, chargingChanged),
                        (self.lowBattery, lowBattery)):
            if callable(cb):
                sig.connect(cb)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        # State.
        self.__m_shown = self.__m_level / 100.0  # type: float
        self.__m_sparks = []  # type: list[Spark]
        self.__m_sparkAcc = 0.0  # type: float
        self.__m_blinkAt = 2.0  # type: float
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

    def _geometry(self):
        """
        :return: (tuple) body QRectF, label top float
        """
        w = float(self.width())  # type: float
        h = float(self.height())  # type: float
        labelH = 42.0 if self.__m_showLabel else 0.0  # type: float
        bw = max(40.0, min(w - 40.0, (h - labelH - 30.0) * 2.0))  # type: float
        bh = bw * 0.5  # type: float
        body = QRectF((w - bw) / 2.0 - bw * 0.03, (h - labelH - bh) / 2.0 + 6.0, bw, bh)  # type: QRectF
        return body, h - labelH

    def _status(self):
        """
        :return: str | unicode | QString
        """
        lv = self.__m_level  # type: int
        if self.__m_charging:
            return self.tr('Charging... yum') if lv < 100 else self.tr('Full and smug about it')
        if lv >= 80:
            return self.tr('Fully energized')
        if lv >= 50:
            return self.tr('Doing fine')
        if lv >= self.__m_lowThreshold:
            return self.tr('Getting sleepy')
        if lv >= 5:
            return self.tr('Running on fumes')
        return self.tr('PLUG ME IN!!')

    # ---------- Public API ----------
    def getLevel(self):
        """
        :return: int
        """
        return self.__m_level

    @pyqtSlot(int)
    def setLevel(self, level):
        """
        :param level: (int) 0..100
        :return:
        """
        level = int(clamp(int(level), 0, 100))  # type: int
        if level != self.__m_level:
            old = self.__m_level  # type: int
            self.__m_level = level  # type: int
            self.levelChanged.emit(level)
            if old >= self.__m_lowThreshold > level:
                self.lowBattery.emit()
            self.update()

    def isCharging(self):
        """
        :return: bool
        """
        return self.__m_charging

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setCharging(self, charging):
        """
        :param charging: bool
        :return:
        """
        charging = bool(charging)  # type: bool
        if charging != self.__m_charging:
            self.__m_charging = charging  # type: bool
            self.chargingChanged.emit(charging)
            self.update()

    def getLowThreshold(self):
        """
        :return: int
        """
        return self.__m_lowThreshold

    @pyqtSlot(int)
    def setLowThreshold(self, lowThreshold):
        """
        :param lowThreshold: int
        :return:
        """
        self.__m_lowThreshold = int(clamp(int(lowThreshold), 1, 99))  # type: int
        self.update()

    def getCaseColor(self):
        """
        :return: QColor
        """
        return self.__m_caseColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setCaseColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        if self.__m_caseColor != color:
            self.__m_caseColor = color  # type: QColor
            self.update()

    def isShowLabel(self):
        """
        :return: bool
        """
        return self.__m_showLabel

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setShowLabel(self, showLabel):
        """
        :param showLabel: bool
        :return:
        """
        self.__m_showLabel = bool(showLabel)  # type: bool
        self.update()

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(280, 200)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(120, 100)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(BatteryBuddyWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(BatteryBuddyWidget, self).hideEvent(event)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        self.__m_shown += (self.__m_level / 100.0 - self.__m_shown) * min(1.0, dt * 6.0)
        if now >= self.__m_blinkAt + 0.14:
            self.__m_blinkAt = now + uniform(2.0, 4.5)  # type: float
        if self.__m_charging:
            body, top = self._geometry()
            self.__m_sparkAcc += dt * 14.0
            while self.__m_sparkAcc > 1.0:
                self.__m_sparkAcc -= 1.0
                a = uniform(-pi * 0.5, pi * 0.5)  # type: float
                sp = uniform(60, 150)  # type: float
                self.__m_sparks.append(Spark(body.right() + body.height() * 0.12, body.center().y() + uniform(-6, 6),
                                             cos(a) * sp, sin(a) * sp, uniform(0.2, 0.45)))
        alive = []  # type: list[Spark]
        for s in self.__m_sparks:
            s.x += s.vx * dt
            s.y += s.vy * dt
            s.life -= dt
            if s.life > 0:
                alive.append(s)
        self.__m_sparks = alive  # type: list[Spark]
        self.update()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        now = self._now()  # type: float
        body, labelTop = self._geometry()
        t = clamp(self.__m_shown, 0.0, 1.0)  # type: float
        lv = self.__m_level  # type: int
        chg = self.__m_charging  # type: bool
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        p.save()
        c = body.center()  # type: QPointF
        # Body language: bounce when full, slump when empty.
        if chg or lv >= 80:
            p.translate(0, -abs(sin(now * (7.0 if chg else 4.0))) * body.height() * 0.06)
        elif lv < self.__m_lowThreshold:
            p.translate(c)
            p.rotate(4.0 + sin(now * 1.2) * 1.5)
            p.translate(-c)
            p.translate(0, body.height() * 0.05)
        bh = body.height()  # type: float
        rad = bh * 0.2  # type: float
        case = self.__m_caseColor  # type: QColor
        # Shadow.
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 45))
        p.drawRoundedRect(body.translated(0, bh * 0.06), rad, rad)
        # Nub.
        p.setBrush(case)
        p.drawRoundedRect(QRectF(body.right() - 2.0, c.y() - bh * 0.18, bh * 0.14, bh * 0.36), bh * 0.05, bh * 0.05)
        # Case interior.
        p.setBrush(case.lighter(165))  # light interior keeps the face readable on any theme
        p.setPen(QPen(case, max(2.5, bh * 0.07)))
        p.drawRoundedRect(body, rad, rad)
        # Charge fill.
        inner = body.adjusted(bh * 0.1, bh * 0.1, -bh * 0.1, -bh * 0.1)  # type: QRectF
        fc = QColor('#3BCEAC') if lv >= 50 else QColor('#FFD23F') if lv >= self.__m_lowThreshold else QColor('#E63946')  # type: QColor
        if chg:
            fc = QColor('#4CC9F0')  # type: QColor
        flicker = lv < 5 and not chg and sin(now * 23.0) * sin(now * 7.0) > 0.3  # type: bool
        if not flicker and t > 0.002:
            fill = QRectF(inner.left(), inner.top(), max(inner.height() * 0.15, inner.width() * t), inner.height())  # type: QRectF
            grad = QLinearGradient(fill.topLeft(), fill.bottomLeft())  # type: QLinearGradient
            grad.setColorAt(0.0, fc.lighter(115))
            grad.setColorAt(1.0, fc.darker(108))
            fp = QPainterPath()  # type: QPainterPath
            fp.addRoundedRect(fill, rad * 0.6, rad * 0.6)
            p.setPen(Qt.NoPen)
            p.fillPath(fp, grad)
            if chg:
                # Shimmer sweeping through the charge.
                p.save()
                p.setClipPath(fp)
                sx = fill.left() + ((now * 0.8) % 1.0) * (fill.width() + 60.0) - 30.0  # type: float
                sh = QLinearGradient(QPointF(sx - 30, 0), QPointF(sx + 30, 0))  # type: QLinearGradient
                sh.setColorAt(0.0, QColor(255, 255, 255, 0))
                sh.setColorAt(0.5, QColor(255, 255, 255, 110))
                sh.setColorAt(1.0, QColor(255, 255, 255, 0))
                p.fillRect(fill, sh)
                p.restore()
        self._drawFace(p, QPointF(inner.center().x(), inner.center().y()), bh * 0.5, lv, chg, now)
        p.restore()
        # Bolt + sparks while charging.
        if chg:
            pulse = 1.0 + 0.12 * sin(now * 8.0)  # type: float
            self._drawBolt(p, QPointF(body.right() + bh * 0.02, body.top() - bh * 0.18), bh * 0.28 * pulse)
            for s in self.__m_sparks:
                sc = QColor('#FFD23F')  # type: QColor
                sc.setAlpha(int(255 * clamp(s.life / 0.45, 0.0, 1.0)))
                p.setPen(QPen(sc, 2.0, Qt.SolidLine, Qt.RoundCap))
                p.drawLine(QPointF(s.x, s.y), QPointF(s.x - s.vx * 0.04, s.y - s.vy * 0.04))
        # Low battery sweat.
        if not chg and 5 <= lv < self.__m_lowThreshold:
            k = (now * 0.9) % 1.0  # type: float
            dc = QColor('#7FD6FF')  # type: QColor
            dc.setAlpha(int(255 * (1.0 - k)))
            x = body.left() + bh * 0.1  # type: float
            y = body.top() - bh * 0.05 + k * bh * 0.4  # type: float
            drop = QPainterPath()  # type: QPainterPath
            drop.moveTo(x, y - 6.0)
            drop.quadTo(x + 4.0, y + 1.0, x, y + 3.5)
            drop.quadTo(x - 4.0, y + 1.0, x, y - 6.0)
            p.fillPath(drop, dc)
        # Labels.
        if self.__m_showLabel:
            tc = QColor(self.palette().text().color())  # type: QColor
            f = QFont(self.font())  # type: QFont
            f.setBold(True)
            f.setPointSizeF(12.0)
            p.setFont(f)
            p.setPen(tc)
            p.drawText(QRectF(0, labelTop, self.width(), 22), Qt.AlignCenter, '{}%'.format(lv))
            f2 = QFont(self.font())  # type: QFont
            f2.setPointSizeF(8.5)
            f2.setBold(lv < 5 and not chg)
            p.setFont(f2)
            sc = QColor('#E63946') if (lv < 5 and not chg) else QColor(tc)  # type: QColor
            if not (lv < 5 and not chg):
                sc.setAlpha(165)
            p.setPen(sc)
            p.drawText(QRectF(0, labelTop + 21, self.width(), 18), Qt.AlignCenter, self._status())
        p.end()

    def _drawFace(self, p, c, r, lv, chg, now):
        """
        :param p: QPainter
        :param c: (QPointF) face center
        :param r: (qreal | float | int) face scale
        :param lv: (int) level
        :param chg: (bool) charging
        :param now: qreal | float | int
        :return:
        """
        ink = QColor('#1E1E28')  # type: QColor
        pen = QPen(ink, max(1.5, r * 0.09), Qt.SolidLine, Qt.RoundCap)  # type: QPen
        ex = r * 0.42  # type: float
        ey = c.y() - r * 0.15  # type: float
        my = c.y() + r * 0.32  # type: float
        er = r * 0.13  # type: float
        blinking = self.__m_blinkAt <= now < self.__m_blinkAt + 0.14  # type: bool
        yawn = 0.0  # type: float
        lidY = 0.0  # type: float
        if not chg and self.__m_lowThreshold <= lv < 50:
            ph = now % 4.5  # type: float
            yawn = sin(ph / 1.0 * pi) if ph < 1.0 else 0.0  # type: float
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        # Eyes.
        for d in (-1.0, 1.0):
            x = c.x() + d * ex  # type: float
            if chg:
                p.drawArc(QRectF(x - er, ey - er * 0.6, er * 2.0, er * 1.4), 20 * 16, 140 * 16)
            elif lv < 5:
                k = er * 0.8  # type: float
                p.drawLine(QPointF(x - k, ey - k), QPointF(x + k, ey + k))
                p.drawLine(QPointF(x - k, ey + k), QPointF(x + k, ey - k))
            elif blinking or yawn > 0.3:
                p.drawLine(QPointF(x - er, ey), QPointF(x + er, ey))
            else:
                big = er * (1.15 if lv >= 80 else 1.0)  # type: float
                eye = QPainterPath()  # type: QPainterPath
                eye.addEllipse(QPointF(x, ey), big, big * 1.1)
                if lv < 50:
                    # Heavy eyelids when tired: keep only the part below the lid line.
                    lid = 0.5 if lv >= self.__m_lowThreshold else 0.7  # type: float
                    cut = QPainterPath()  # type: QPainterPath
                    lidY = ey - big * 1.1 + big * 2.2 * lid  # type: float
                    cut.addRect(QRectF(x - big * 1.2, lidY, big * 2.4, big * 2.4))
                    eye = eye.intersected(cut)  # type: QPainterPath
                p.setPen(Qt.NoPen)
                p.fillPath(eye, ink)
                if lv >= 50:
                    p.setBrush(QColor('#FFFFFF'))
                    p.drawEllipse(QPointF(x - big * 0.3, ey - big * 0.35), big * 0.32, big * 0.32)
                else:
                    p.setPen(pen)
                    p.drawLine(QPointF(x - big * 1.15, lidY), QPointF(x + big * 1.15, lidY))
                p.setPen(pen)
                p.setBrush(Qt.NoBrush)
        # Mouth.
        p.setPen(pen)
        if chg:
            munch = abs(sin(now * 9.0))  # type: float
            p.setBrush(QColor('#7A2E2E'))
            p.drawEllipse(QPointF(c.x(), my), r * 0.2, r * (0.06 + 0.14 * munch))
        elif lv < 5:
            p.setBrush(Qt.NoBrush)
            p.drawLine(QPointF(c.x() - r * 0.2, my), QPointF(c.x() + r * 0.2, my))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor('#FF7A90'))
            p.drawEllipse(QPointF(c.x() + r * 0.08, my + r * 0.1), r * 0.08, r * 0.1)
        elif yawn > 0.05:
            p.setBrush(QColor('#7A2E2E'))
            p.drawEllipse(QPointF(c.x(), my), r * 0.14, r * 0.2 * yawn + r * 0.02)
        elif lv >= 80:
            p.setBrush(QColor('#7A2E2E'))
            m = QPainterPath()  # type: QPainterPath
            m.moveTo(c.x() - r * 0.3, my - r * 0.08)
            m.quadTo(c.x(), my + r * 0.4, c.x() + r * 0.3, my - r * 0.08)
            m.closeSubpath()
            p.drawPath(m)
        elif lv >= 50:
            p.setBrush(Qt.NoBrush)
            p.drawArc(QRectF(c.x() - r * 0.24, my - r * 0.22, r * 0.48, r * 0.3), 200 * 16, 140 * 16)
        elif lv >= self.__m_lowThreshold:
            p.setBrush(Qt.NoBrush)
            p.drawLine(QPointF(c.x() - r * 0.18, my), QPointF(c.x() + r * 0.18, my))
        else:
            p.setBrush(Qt.NoBrush)
            m = QPainterPath()  # type: QPainterPath
            m.moveTo(c.x() - r * 0.22, my)
            for k in range(1, 7):
                m.lineTo(c.x() - r * 0.22 + k * r * 0.44 / 6.0, my + (r * 0.05 if k % 2 else -r * 0.05))
            p.drawPath(m)

    @staticmethod
    def _drawBolt(p, c, s):
        """
        :param p: QPainter
        :param c: (QPointF) center
        :param s: (qreal | float | int) size
        :return:
        """
        bolt = QPainterPath()  # type: QPainterPath
        pts = [(0.15, -1.0), (-0.55, 0.15), (-0.05, 0.15), (-0.2, 1.0), (0.55, -0.2), (0.05, -0.2)]  # type: list
        for i, (x, y) in enumerate(pts):
            pt = QPointF(c.x() + x * s, c.y() + y * s)  # type: QPointF
            if i == 0:
                bolt.moveTo(pt)
            else:
                bolt.lineTo(pt)
        bolt.closeSubpath()
        p.setPen(QPen(QColor('#B8860B'), 1.5))
        p.setBrush(QColor('#FFD23F'))
        p.drawPath(bolt)

    # ---------- Properties ----------
    level = pyqtProperty(int, fget=getLevel, fset=setLevel, notify=levelChanged)  # type: pyqtProperty
    charging = pyqtProperty(bool, fget=isCharging, fset=setCharging, notify=chargingChanged)  # type: pyqtProperty
    lowThreshold = pyqtProperty(int, fget=getLowThreshold, fset=setLowThreshold)  # type: pyqtProperty
    caseColor = pyqtProperty(QColor, fget=getCaseColor, fset=setCaseColor)  # type: pyqtProperty
    showLabel = pyqtProperty(bool, fget=isShowLabel, fset=setShowLabel)  # type: pyqtProperty
