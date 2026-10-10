# -*- coding: utf-8 -*-
"""
RubberDuckWidget: a rubber-duck-debugging companion. It bobs on rippling water, blinks and looks
around, squeaks (with squash & stretch) when clicked and dispenses questionable developer advice in a
thought bubble. Call listen() and it nods thoughtfully before answering.
"""
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QFontMetricsF, QRadialGradient, QLinearGradient
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtWidgets import QWidget
from random import uniform, choice
from math import sin


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


DEFAULT_ADVICE = ['Have you tried turning it off and on again?', 'Read the error message. Slowly. Out loud.',
                  "It's always DNS.", 'Did you save the file?', 'Works on my machine. Ship my machine.',
                  'Explain it to me line by line.', 'Is it plugged in?', 'Check for a missing comma.',
                  'Clear the cache. Then clear it again.', 'Take a walk. The bug will miss you.',
                  'Off by one? Or off by two?', 'Delete it and see who complains.',
                  'Add a print statement. Add ten.', 'Blame the intern. Wait, you ARE the intern.']  # type: list[str]


class RubberDuckWidget(QWidget):
    """
    Debugging duck.
    """
    squeaked = pyqtSignal(int)  # type: pyqtSignal
    adviceGiven = pyqtSignal('QString')  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param duckColor: QColor | Qt.GlobalColor | int | str | QString
        :param beakColor: QColor | Qt.GlobalColor | int | str | QString
        :param waterColor: QColor | Qt.GlobalColor | int | str | QString
        :param advice: (list[str | unicode | QString]) Wisdom to dispense.
        :param adviceOnClick: (bool) Give advice after each squeak.
        :param adviceDuration: (int) ms the thought bubble stays visible.
        :param squeakText: (str | unicode | QString) Sound effect text.
        :param squeaked: callable | None
        :param adviceGiven: callable | None
        :param args: any
        :param kwargs: any
        """
        duckColor = kwargs.pop('duckColor', '#FFD43B')  # type: QColor
        beakColor = kwargs.pop('beakColor', '#FF8C1A')  # type: QColor
        waterColor = kwargs.pop('waterColor', '#4CC9F0')  # type: QColor
        advice = kwargs.pop('advice', DEFAULT_ADVICE)  # type: list[str]
        adviceOnClick = kwargs.pop('adviceOnClick', True)  # type: bool
        adviceDuration = kwargs.pop('adviceDuration', 3500)  # type: int
        squeakText = kwargs.pop('squeakText', 'SQUEAK!')  # type: str
        squeaked = kwargs.pop('squeaked', None)  # type: callable | None
        adviceGiven = kwargs.pop('adviceGiven', None)  # type: callable | None
        super(RubberDuckWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_duckColor = QColor(duckColor)  # type: QColor
        self.__m_beakColor = QColor(beakColor)  # type: QColor
        self.__m_waterColor = QColor(waterColor)  # type: QColor
        self.__m_advice = list(advice) or list(DEFAULT_ADVICE)  # type: list[str]
        self.__m_adviceOnClick = bool(adviceOnClick)  # type: bool
        self.__m_adviceDuration = max(500, int(adviceDuration))  # type: int
        self.__m_squeakText = squeakText  # type: str
        if callable(squeaked):
            self.squeaked.connect(squeaked)
        if callable(adviceGiven):
            self.adviceGiven.connect(adviceGiven)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setCursor(Qt.PointingHandCursor)
        # State.
        self.__m_squeaks = 0  # type: int
        self.__m_squash = 0.0  # type: float
        self.__m_squashVel = 0.0  # type: float
        self.__m_squeakAt = -10.0  # type: float
        self.__m_thinkUntil = 0.0  # type: float
        self.__m_bubbleText = ''  # type: str
        self.__m_bubbleUntil = 0.0  # type: float
        self.__m_bubbleShownAt = -10.0  # type: float
        self.__m_lastAdvice = ''  # type: str
        self.__m_blinkAt = 2.0  # type: float
        self.__m_lookX = 0.0  # type: float
        self.__m_lookTarget = 0.0  # type: float
        self.__m_nextLook = 1.5  # type: float
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
        :return: (tuple) duck center QPointF, duck size float, water line y float
        """
        w = float(self.width())  # type: float
        h = float(self.height())  # type: float
        s = max(20.0, min(w * 0.42, h * 0.42))  # type: float
        water = h - s * 0.28  # type: float
        return QPointF(w * 0.5, water - s * 0.18), s, water

    def _pickAdvice(self):
        """
        :return: str | unicode | QString
        """
        options = [a for a in self.__m_advice if a != self.__m_lastAdvice] or self.__m_advice  # type: list[str]
        self.__m_lastAdvice = choice(options)  # type: str
        return self.__m_lastAdvice

    def _say(self, text, now):
        """
        :param text: str | unicode | QString
        :param now: qreal | float | int
        :return:
        """
        self.__m_bubbleText = text  # type: str
        self.__m_bubbleShownAt = now  # type: float
        self.__m_bubbleUntil = now + self.__m_adviceDuration / 1000.0  # type: float
        self.adviceGiven.emit(text)

    # ---------- Public API ----------
    @pyqtSlot()
    def squeak(self):
        """
        Squeeze the duck.
        :return:
        """
        now = self._now()  # type: float
        self.__m_squeaks += 1
        self.__m_squeakAt = now  # type: float
        self.__m_squashVel -= 9.0  # type: float
        self.squeaked.emit(self.__m_squeaks)
        if self.__m_adviceOnClick and now >= self.__m_thinkUntil:
            self._say(self._pickAdvice(), now)

    @pyqtSlot()
    @pyqtSlot('QString')
    @pyqtSlot(str)
    def listen(self, problem=''):
        """
        Describe your problem; the duck nods for a moment, then answers.

        :param problem: (str | unicode | QString) Ignored. The duck already knows.
        :return:
        """
        now = self._now()  # type: float
        self.__m_thinkUntil = now + 1.6  # type: float
        self.__m_bubbleText = ''  # type: str
        self.__m_bubbleShownAt = now  # type: float
        self.__m_bubbleUntil = self.__m_thinkUntil  # type: float

    def getSqueaks(self):
        """
        :return: int
        """
        return self.__m_squeaks

    def getDuckColor(self):
        """
        :return: QColor
        """
        return self.__m_duckColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setDuckColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        if self.__m_duckColor != color:
            self.__m_duckColor = color  # type: QColor
            self.update()

    def getBeakColor(self):
        """
        :return: QColor
        """
        return self.__m_beakColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setBeakColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        if self.__m_beakColor != color:
            self.__m_beakColor = color  # type: QColor
            self.update()

    def getWaterColor(self):
        """
        :return: QColor
        """
        return self.__m_waterColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setWaterColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        if self.__m_waterColor != color:
            self.__m_waterColor = color  # type: QColor
            self.update()

    def getAdvice(self):
        """
        :return: list[str | unicode | QString]
        """
        return list(self.__m_advice)

    @pyqtSlot(list)
    def setAdvice(self, advice):
        """
        :param advice: list[str]
        :return:
        """
        self.__m_advice = list(advice) or list(DEFAULT_ADVICE)  # type: list[str]
        self.update()

    def isAdviceOnClick(self):
        """
        :return: bool
        """
        return self.__m_adviceOnClick

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setAdviceOnClick(self, adviceOnClick):
        """
        :param adviceOnClick: bool
        :return:
        """
        self.__m_adviceOnClick = bool(adviceOnClick)  # type: bool
        self.update()

    def getAdviceDuration(self):
        """
        :return: int
        """
        return self.__m_adviceDuration

    @pyqtSlot(int)
    def setAdviceDuration(self, adviceDuration):
        """
        :param adviceDuration: (int) ms
        :return:
        """
        self.__m_adviceDuration = max(500, int(adviceDuration))  # type: int

    def getSqueakText(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_squeakText

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setSqueakText(self, squeakText):
        """
        :param squeakText: str | unicode | QString
        :return:
        """
        self.__m_squeakText = squeakText  # type: str

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(320, 260)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(160, 140)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(RubberDuckWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(RubberDuckWidget, self).hideEvent(event)

    def mousePressEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        c, s, water = self._geometry()
        if e.button() == Qt.LeftButton and abs(eventPos(e).x() - c.x()) < s * 0.7 \
                and abs(eventPos(e).y() - c.y()) < s * 0.7:
            self.squeak()
        super(RubberDuckWidget, self).mousePressEvent(e)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        self.__m_squashVel += (-self.__m_squash * 300.0 - self.__m_squashVel * 9.0) * dt
        self.__m_squash += self.__m_squashVel * dt
        if now >= self.__m_nextLook:
            self.__m_lookTarget = choice([-1.0, -0.4, 0.0, 0.6, 1.0])  # type: float
            self.__m_nextLook = now + uniform(1.2, 3.5)  # type: float
        if now >= self.__m_blinkAt + 0.15:
            self.__m_blinkAt = now + uniform(2.0, 5.0)  # type: float
        self.__m_lookX += (self.__m_lookTarget - self.__m_lookX) * min(1.0, dt * 8.0)
        # Finished thinking: deliver wisdom.
        if self.__m_thinkUntil > 0 and now >= self.__m_thinkUntil:
            self.__m_thinkUntil = 0.0  # type: float
            self._say(self._pickAdvice(), now)
        self.update()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        now = self._now()  # type: float
        c, s, water = self._geometry()
        w = float(self.width())  # type: float
        h = float(self.height())  # type: float
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        thinking = now < self.__m_thinkUntil  # type: bool
        bob = sin(now * 2.2) * s * 0.03  # type: float
        rock = sin(now * 1.7) * 4.0  # type: float
        if thinking:
            rock += sin(now * 9.0) * 6.0  # nodding
        # Duck.
        p.save()
        p.translate(c.x(), c.y() + bob)
        p.rotate(rock)
        sq = clamp(self.__m_squash, -0.35, 0.35)  # type: float
        p.translate(0, s * 0.3)
        p.scale(1.0 - sq * 0.6, 1.0 + sq)
        p.translate(0, -s * 0.3)
        self._drawDuck(p, s, now, thinking)
        p.restore()
        # Water in front of the duck's bottom.
        self._drawWater(p, w, h, water, s, now)
        # Squeak text.
        since = now - self.__m_squeakAt  # type: float
        if since < 0.7:
            f = QFont(self.font())  # type: QFont
            f.setBold(True)
            f.setPointSizeF(max(7.0, s * 0.1) * (1.0 + 0.4 * clamp(since * 6.0, 0.0, 1.0)))
            p.setFont(f)
            col = QColor('#FF8C1A')  # type: QColor
            col.setAlpha(int(255 * (1.0 - since / 0.7)))
            p.setPen(col)
            p.save()
            p.translate(c.x() - s * 0.75, c.y() - s * 0.55 - since * s * 0.3)
            p.rotate(-12.0)
            p.drawText(QPointF(0, 0), self.__m_squeakText)
            p.restore()
        # Thought bubble.
        if now < self.__m_bubbleUntil:
            self._drawBubble(p, c, s, now, thinking)
        p.end()

    def _drawDuck(self, p, s, now, thinking):
        """
        Duck facing right, origin at body center.

        :param p: QPainter
        :param s: (qreal | float | int) size
        :param now: qreal | float | int
        :param thinking: bool
        :return:
        """
        dc = self.__m_duckColor  # type: QColor
        outline = QPen(dc.darker(150), max(1.2, s * 0.012))  # type: QPen
        # Body with a perky tail.
        body = QPainterPath()  # type: QPainterPath
        body.moveTo(-s * 0.55, -s * 0.12)
        body.quadTo(-s * 0.5, s * 0.02, -s * 0.38, s * 0.04)
        body.cubicTo(-s * 0.5, s * 0.38, s * 0.42, s * 0.42, s * 0.48, s * 0.06)
        body.cubicTo(s * 0.5, -s * 0.1, s * 0.2, -s * 0.12, -s * 0.05, -s * 0.06)
        body.cubicTo(-s * 0.25, -s * 0.02, -s * 0.38, -s * 0.06, -s * 0.55, -s * 0.12)
        grad = QRadialGradient(QPointF(-s * 0.05, -s * 0.05), s * 0.7)  # type: QRadialGradient
        grad.setColorAt(0.0, dc.lighter(115))
        grad.setColorAt(1.0, dc.darker(112))
        p.setPen(outline)
        p.setBrush(grad)
        p.drawPath(body)
        # Wing.
        wing = QPainterPath()  # type: QPainterPath
        flap = sin(now * 30.0) * s * 0.03 if now - self.__m_squeakAt < 0.5 else 0.0  # type: float
        wing.moveTo(-s * 0.22, s * 0.06)
        wing.cubicTo(-s * 0.12, -s * 0.06 - flap, s * 0.2, -s * 0.02 - flap, s * 0.16, s * 0.12)
        wing.quadTo(-s * 0.02, s * 0.2, -s * 0.22, s * 0.06)
        p.setBrush(dc.darker(106))
        p.drawPath(wing)
        # Head.
        hx = s * 0.22  # type: float
        hy = -s * 0.32  # type: float
        hr = s * 0.24  # type: float
        hg = QRadialGradient(QPointF(hx - hr * 0.3, hy - hr * 0.35), hr * 1.6)  # type: QRadialGradient
        hg.setColorAt(0.0, dc.lighter(118))
        hg.setColorAt(1.0, dc.darker(110))
        p.setBrush(hg)
        p.drawEllipse(QPointF(hx, hy), hr, hr)
        # Beak (opens on squeak).
        open_ = clamp(1.0 - (now - self.__m_squeakAt) / 0.4, 0.0, 1.0)  # type: float
        bc = self.__m_beakColor  # type: QColor
        p.setPen(QPen(bc.darker(140), max(1.0, s * 0.01)))
        p.setBrush(bc)
        bx = hx + hr * 0.75  # type: float
        by = hy + hr * 0.25  # type: float
        upper = QPainterPath()  # type: QPainterPath
        upper.moveTo(bx, by - s * 0.05)
        upper.quadTo(bx + s * 0.2, by - s * 0.05 - open_ * s * 0.05, bx + s * 0.22, by - open_ * s * 0.05)
        upper.quadTo(bx + s * 0.1, by + s * 0.01 - open_ * s * 0.04, bx, by + s * 0.01)
        upper.closeSubpath()
        lower = QPainterPath()  # type: QPainterPath
        lower.moveTo(bx, by + s * 0.01)
        lower.quadTo(bx + s * 0.1, by + s * 0.02 + open_ * s * 0.04, bx + s * 0.18, by + s * 0.03 + open_ * s * 0.06)
        lower.quadTo(bx + s * 0.08, by + s * 0.07 + open_ * s * 0.05, bx, by + s * 0.05)
        lower.closeSubpath()
        p.drawPath(lower)
        p.drawPath(upper)
        # Eye: blinks, looks around, squints when squeezed, looks up while thinking.
        ex = hx + hr * 0.3  # type: float
        ey = hy - hr * 0.15  # type: float
        er = hr * 0.24  # type: float
        ink = QColor('#1E1E24')  # type: QColor
        blinking = self.__m_blinkAt <= now < self.__m_blinkAt + 0.15  # type: bool
        if blinking or open_ > 0.3:
            p.setPen(QPen(ink, max(1.2, s * 0.015), Qt.SolidLine, Qt.RoundCap))
            p.setBrush(Qt.NoBrush)
            if open_ > 0.3:
                p.drawLine(QPointF(ex - er, ey - er * 0.5), QPointF(ex + er * 0.6, ey))
                p.drawLine(QPointF(ex + er * 0.6, ey), QPointF(ex - er, ey + er * 0.5))
            else:
                p.drawArc(QRectF(ex - er, ey - er * 0.5, er * 2.0, er), 180 * 16, 180 * 16)
        else:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor('#FFFFFF'))
            p.drawEllipse(QPointF(ex, ey), er, er * 1.1)
            lx = 0.0 if thinking else self.__m_lookX * er * 0.35  # type: float
            ly = -er * 0.4 if thinking else 0.0  # type: float
            p.setBrush(ink)
            p.drawEllipse(QPointF(ex + lx, ey + ly), er * 0.6, er * 0.65)
            p.setBrush(QColor('#FFFFFF'))
            p.drawEllipse(QPointF(ex + lx - er * 0.2, ey + ly - er * 0.25), er * 0.2, er * 0.2)
        # Blush.
        blush = QColor('#FF8FA3')  # type: QColor
        blush.setAlpha(120)
        p.setPen(Qt.NoPen)
        p.setBrush(blush)
        p.drawEllipse(QPointF(hx + hr * 0.25, hy + hr * 0.45), hr * 0.2, hr * 0.12)

    def _drawWater(self, p, w, h, water, s, now):
        """
        :param p: QPainter
        :param w: qreal | float | int
        :param h: qreal | float | int
        :param water: (qreal | float | int) water line y
        :param s: (qreal | float | int) duck size
        :param now: qreal | float | int
        :return:
        """
        wc = QColor(self.__m_waterColor)  # type: QColor
        path = QPainterPath()  # type: QPainterPath
        path.moveTo(0, h)
        steps = 40  # type: int
        for k in range(steps + 1):
            x = w * k / float(steps)  # type: float
            y = water + sin(x * 0.04 + now * 2.5) * s * 0.025 + sin(x * 0.09 - now * 1.7) * s * 0.012  # type: float
            path.lineTo(x, y)
        path.lineTo(w, h)
        path.closeSubpath()
        grad = QLinearGradient(QPointF(0, water), QPointF(0, h))  # type: QLinearGradient
        top = QColor(wc)  # type: QColor
        top.setAlpha(200)
        bottom = QColor(wc.darker(140))  # type: QColor
        bottom.setAlpha(230)
        grad.setColorAt(0.0, top)
        grad.setColorAt(1.0, bottom)
        p.setPen(QPen(wc.lighter(130), max(1.5, s * 0.015)))
        p.setBrush(grad)
        p.drawPath(path)
        # Ripples around the duck.
        c, s2, wl = self._geometry()
        p.setBrush(Qt.NoBrush)
        for k in range(2):
            t = (now * 0.5 + k * 0.5) % 1.0  # type: float
            rc = QColor('#FFFFFF')  # type: QColor
            rc.setAlpha(int(110 * (1.0 - t)))
            p.setPen(QPen(rc, max(1.0, s * 0.01)))
            rw = s * (0.55 + 0.45 * t)  # type: float
            p.drawEllipse(QPointF(c.x(), water + s * 0.02), rw, rw * 0.12)

    def _drawBubble(self, p, c, s, now, thinking):
        """
        :param p: QPainter
        :param c: (QPointF) duck center
        :param s: (qreal | float | int) duck size
        :param now: qreal | float | int
        :param thinking: bool
        :return:
        """
        f = QFont(self.font())  # type: QFont
        f.setPointSizeF(clamp(s * 0.075, 8.0, 11.0))
        fm = QFontMetricsF(f)  # type: QFontMetricsF
        maxW = min(self.width() - 16.0, max(140.0, s * 1.9))  # type: float
        text = '. . .' if thinking else self.__m_bubbleText  # type: str
        br = fm.boundingRect(QRectF(0, 0, maxW - 24.0, 1000.0), Qt.TextWordWrap | Qt.AlignCenter, text)  # type: QRectF
        bw = br.width() + 26.0  # type: float
        bh = br.height() + 18.0  # type: float
        headTop = c.y() - s * 0.6  # type: float
        bx = clamp(c.x() - bw * 0.35, 6.0, self.width() - bw - 6.0)  # type: float
        by = max(4.0, headTop - bh - s * 0.18)  # type: float
        since = now - self.__m_bubbleShownAt  # type: float
        left = self.__m_bubbleUntil - now  # type: float
        a = clamp(min(since * 6.0, left * 4.0), 0.0, 1.0)  # type: float
        p.save()
        p.setOpacity(a)
        ink = QColor('#22222A')  # type: QColor
        p.setPen(QPen(QColor(30, 30, 40, 60), 1.2))
        p.setBrush(QColor('#FFFFFF'))
        # Trail of little thought circles to the head.
        hx = c.x() + s * 0.15  # type: float
        for k, rr in enumerate((s * 0.025, s * 0.04)):
            t = (k + 1) / 3.0  # type: float
            p.drawEllipse(QPointF(hx + (bx + bw * 0.4 - hx) * t, headTop + (by + bh - headTop) * t), rr, rr)
        p.drawRoundedRect(QRectF(bx, by, bw, bh), bh * 0.35 if bh < 50 else 16.0, bh * 0.35 if bh < 50 else 16.0)
        p.setFont(f)
        p.setPen(ink)
        if thinking:
            dots = int(now * 4.0) % 4  # type: int
            text = '.' * dots  # type: str
            f.setBold(True)
            p.setFont(f)
        p.drawText(QRectF(bx + 13.0, by + 9.0, bw - 26.0, bh - 18.0), Qt.TextWordWrap | Qt.AlignCenter, text)
        p.restore()

    # ---------- Properties ----------
    duckColor = pyqtProperty(QColor, fget=getDuckColor, fset=setDuckColor)  # type: pyqtProperty
    beakColor = pyqtProperty(QColor, fget=getBeakColor, fset=setBeakColor)  # type: pyqtProperty
    waterColor = pyqtProperty(QColor, fget=getWaterColor, fset=setWaterColor)  # type: pyqtProperty
    advice = pyqtProperty('QStringList', fget=getAdvice, fset=setAdvice)  # type: pyqtProperty
    adviceOnClick = pyqtProperty(bool, fget=isAdviceOnClick, fset=setAdviceOnClick)  # type: pyqtProperty
    adviceDuration = pyqtProperty(int, fget=getAdviceDuration, fset=setAdviceDuration)  # type: pyqtProperty
    squeakText = pyqtProperty('QString', fget=getSqueakText, fset=setSqueakText)  # type: pyqtProperty
