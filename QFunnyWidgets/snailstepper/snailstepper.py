# -*- coding: utf-8 -*-
"""
SnailStepperWidget: a wizard / checkout step indicator where progress is carried by a snail.
Completed steps get check marks, the current step pulses, and the snail crawls along the track at
a strictly limited snail pace, leaving a glistening slime trail. Click "next" too quickly and it
complains that it is going as fast as it can.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QFontMetricsF
from ManyQt.QtWidgets import QWidget
from math import sin, cos, pi


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


DEFAULT_STEPS = ['Cart', 'Shipping', 'Payment', 'Review', 'Done']  # type: list[str]


class SnailStepperWidget(QWidget):
    """
    Step indicator with a slow but determined snail.
    """
    currentChanged = pyqtSignal(int)  # type: pyqtSignal
    arrived = pyqtSignal(int)  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param steps: (list[str | unicode | QString]) Step labels.
        :param current: (int) Current step index.
        :param speed: (qreal | float | int) Snail speed in px/s.
        :param clickable: (bool) Clicking a step jumps to it.
        :param accentColor: QColor | Qt.GlobalColor | int | str | QString
        :param shellColor: QColor | Qt.GlobalColor | int | str | QString
        :param currentChanged: callable | None
        :param arrived: callable | None
        :param args: any
        :param kwargs: any
        """
        steps = kwargs.pop('steps', DEFAULT_STEPS)  # type: list[str]
        current = kwargs.pop('current', 0)  # type: int
        speed = kwargs.pop('speed', 70.0)  # type: float
        clickable = kwargs.pop('clickable', True)  # type: bool
        accentColor = kwargs.pop('accentColor', '#3BCEAC')  # type: QColor
        shellColor = kwargs.pop('shellColor', '#E07A5F')  # type: QColor
        currentChanged = kwargs.pop('currentChanged', None)  # type: callable | None
        arrived = kwargs.pop('arrived', None)  # type: callable | None
        super(SnailStepperWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_steps = list(steps) or list(DEFAULT_STEPS)  # type: list[str]
        self.__m_current = int(clamp(int(current), 0, len(self.__m_steps) - 1))  # type: int
        self.__m_speed = max(5.0, float(speed))  # type: float
        self.__m_clickable = bool(clickable)  # type: bool
        self.__m_accentColor = QColor(accentColor)  # type: QColor
        self.__m_shellColor = QColor(shellColor)  # type: QColor
        if callable(currentChanged):
            self.currentChanged.connect(currentChanged)
        if callable(arrived):
            self.arrived.connect(arrived)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.StrongFocus)
        # State.
        self.__m_x = -1.0  # type: float  # snail position, px
        self.__m_trail = -1.0  # type: float  # furthest slime point
        self.__m_facing = 1.0  # type: float
        self.__m_moving = False  # type: bool
        self.__m_crawl = 0.0  # type: float
        self.__m_arrivedAt = -10.0  # type: float
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

    def _layout(self):
        """
        :return: (tuple) step xs list[float], track y float, circle radius float, snail size float
        """
        n = len(self.__m_steps)  # type: int
        w = float(self.width())  # type: float
        h = float(self.height())  # type: float
        margin = 46.0  # type: float
        gap = (w - 2 * margin) / max(1, n - 1)  # type: float
        r = clamp(gap * 0.16, 9.0, 15.0)  # type: float
        y = h * 0.56  # type: float
        size = clamp(min(gap * 0.5, h * 0.42), 26.0, 52.0)  # type: float
        return [margin + i * gap for i in range(n)], y, r, size

    # ---------- Public API ----------
    @pyqtSlot()
    def next(self):
        """
        :return:
        """
        self.setCurrent(self.__m_current + 1)

    @pyqtSlot()
    def previous(self):
        """
        :return:
        """
        self.setCurrent(self.__m_current - 1)

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
        current = int(clamp(int(current), 0, len(self.__m_steps) - 1))  # type: int
        if current != self.__m_current:
            self.__m_current = current  # type: int
            self.__m_moving = True  # type: bool
            self.currentChanged.emit(current)
            self.update()

    def getSteps(self):
        """
        :return: list[str | unicode | QString]
        """
        return list(self.__m_steps)

    @pyqtSlot(list)
    def setSteps(self, steps):
        """
        :param steps: list[str]
        :return:
        """
        self.__m_steps = list(steps) or list(DEFAULT_STEPS)  # type: list[str]
        self.__m_current = min(self.__m_current, len(self.__m_steps) - 1)  # type: int
        self.update()

    def getSpeed(self):
        """
        :return: qreal | float | int
        """
        return self.__m_speed

    @pyqtSlot('qreal')
    @pyqtSlot(float)
    @pyqtSlot(int)
    def setSpeed(self, speed):
        """
        :param speed: (qreal | float | int) px/s
        :return:
        """
        self.__m_speed = max(5.0, float(speed))  # type: float
        self.update()

    def isClickable(self):
        """
        :return: bool
        """
        return self.__m_clickable

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setClickable(self, clickable):
        """
        :param clickable: bool
        :return:
        """
        self.__m_clickable = bool(clickable)  # type: bool

    def getAccentColor(self):
        """
        :return: QColor
        """
        return self.__m_accentColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setAccentColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        self.__m_accentColor = color  # type: QColor
        self.update()

    def getShellColor(self):
        """
        :return: QColor
        """
        return self.__m_shellColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setShellColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        self.__m_shellColor = color  # type: QColor
        self.update()

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(520, 130)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(260, 100)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(SnailStepperWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(SnailStepperWidget, self).hideEvent(event)

    def resizeEvent(self, event):
        """
        :param event: QResizeEvent
        :return:
        """
        super(SnailStepperWidget, self).resizeEvent(event)
        xs, y, r, size = self._layout()
        self.__m_x = xs[self.__m_current]  # type: float
        self.__m_trail = max(self.__m_trail, self.__m_x)  # type: float

    def mouseReleaseEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if e.button() == Qt.LeftButton and self.__m_clickable:
            xs, y, r, size = self._layout()
            for i, x in enumerate(xs):
                if abs(eventPos(e).x() - x) < r * 1.8 and abs(eventPos(e).y() - y) < r * 3.5:
                    self.setCurrent(i)
                    break
        super(SnailStepperWidget, self).mouseReleaseEvent(e)

    def keyPressEvent(self, e):
        """
        :param e: QKeyEvent
        :return:
        """
        if e.key() == Qt.Key_Right:
            self.next()
        elif e.key() == Qt.Key_Left:
            self.previous()
        else:
            super(SnailStepperWidget, self).keyPressEvent(e)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        xs, y, r, size = self._layout()
        target = xs[self.__m_current]  # type: float
        if self.__m_x < 0:
            self.__m_x = target  # type: float
            self.__m_trail = target  # type: float
        d = target - self.__m_x  # type: float
        if abs(d) > 0.5:
            # Snails move in pulses: speed rises and falls with each "step".
            self.__m_crawl += dt * 6.0
            v = self.__m_speed * (0.55 + 0.45 * abs(sin(self.__m_crawl)))  # type: float
            move = min(abs(d), v * dt)  # type: float
            self.__m_x += move if d > 0 else -move
            self.__m_facing = 1.0 if d > 0 else -1.0  # type: float
        elif self.__m_moving:
            self.__m_x = target  # type: float
            self.__m_moving = False  # type: bool
            self.__m_arrivedAt = now  # type: float
            self.arrived.emit(self.__m_current)
        # Slime only marks the furthest point reached; going back leaves it shining.
        self.__m_trail = max(self.__m_trail, self.__m_x) if self.__m_facing > 0 else self.__m_trail  # type: float
        self.__m_trail = min(self.__m_trail, xs[-1])  # type: float
        self.update()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        now = self._now()  # type: float
        xs, y, r, size = self._layout()
        tc = QColor(self.palette().text().color())  # type: QColor
        ac = self.__m_accentColor  # type: QColor
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        # Track.
        track = QColor(tc)  # type: QColor
        track.setAlpha(45)
        p.setPen(QPen(track, 4.0, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(xs[0], y), QPointF(xs[-1], y))
        # Slime trail with a travelling shine.
        if self.__m_trail > xs[0]:
            slime = QColor(ac)  # type: QColor
            slime.setAlpha(150)
            p.setPen(QPen(slime, 4.0, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(xs[0], y), QPointF(self.__m_trail, y))
            span = self.__m_trail - xs[0]  # type: float
            for k in range(3):
                sx = xs[0] + ((now * 0.4 + k / 3.0) % 1.0) * span  # type: float
                p.setPen(QPen(QColor(255, 255, 255, 170), 2.0, Qt.SolidLine, Qt.RoundCap))
                p.drawLine(QPointF(sx - 4, y - 1), QPointF(sx + 4, y - 1))
        # Steps.
        lf = QFont(self.font())  # type: QFont
        lf.setPointSizeF(8.5)
        nf = QFont(self.font())  # type: QFont
        nf.setBold(True)
        nf.setPointSizeF(max(7.0, r * 0.7))
        for i, x in enumerate(xs):
            done = i < self.__m_current and xs[i] <= self.__m_x + 1.0  # type: bool
            cur = i == self.__m_current  # type: bool
            c = QPointF(x, y)  # type: QPointF
            if cur:
                pulse = r * (1.25 + 0.15 * sin(now * 4.0))  # type: float
                halo = QColor(ac)  # type: QColor
                halo.setAlpha(50)
                p.setPen(Qt.NoPen)
                p.setBrush(halo)
                p.drawEllipse(c, pulse, pulse)
            if done:
                p.setPen(Qt.NoPen)
                p.setBrush(ac)
                p.drawEllipse(c, r, r)
                p.setPen(QPen(QColor('#FFFFFF'), max(2.0, r * 0.18), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                path = QPainterPath()  # type: QPainterPath
                path.moveTo(x - r * 0.45, y + r * 0.02)
                path.lineTo(x - r * 0.1, y + r * 0.35)
                path.lineTo(x + r * 0.45, y - r * 0.32)
                p.setBrush(Qt.NoBrush)
                p.drawPath(path)
            else:
                bg = self.palette().window().color()  # type: QColor
                p.setPen(QPen(ac if cur else track.lighter(150) if tc.lightness() > 128 else track, 2.5))
                p.setBrush(bg)
                p.drawEllipse(c, r, r)
                p.setFont(nf)
                nc = QColor(ac) if cur else QColor(tc)  # type: QColor
                if not cur:
                    nc.setAlpha(140)
                p.setPen(nc)
                p.drawText(QRectF(x - r, y - r, 2 * r, 2 * r), Qt.AlignCenter, str(i + 1))
            p.setFont(lf)
            lc = QColor(tc)  # type: QColor
            lc.setAlpha(230 if cur else 150)
            p.setPen(lc)
            lw = min(110.0, (xs[1] - xs[0]) if len(xs) > 1 else 110.0)  # type: float
            p.drawText(QRectF(x - lw / 2.0, y + r + 8.0, lw, 16.0), Qt.AlignHCenter | Qt.AlignTop,
                       QFontMetricsF(lf).elidedText(self.__m_steps[i], Qt.ElideRight, lw))
        # Snail.
        self._drawSnail(p, QPointF(self.__m_x, y - 2.0), size, now)
        # Speech.
        gap = abs(xs[self.__m_current] - self.__m_x)  # type: float
        unit = (xs[1] - xs[0]) if len(xs) > 1 else 100.0  # type: float
        speech = ''  # type: str
        if gap > unit * 1.2:
            speech = self.tr("I'm going as fast as I can!")  # type: str
        elif gap > 0.5:
            speech = self.tr('On my way...')  # type: str
        elif now - self.__m_arrivedAt < 1.2:
            speech = self.tr('Made it!') if self.__m_current < len(xs) - 1 else self.tr('Finally! Done!')  # type: str
        if speech:
            f = QFont(self.font())  # type: QFont
            f.setBold(True)
            f.setPointSizeF(8.0)
            fm = QFontMetricsF(f)  # type: QFontMetricsF
            tw = fm.horizontalAdvance(speech) if hasattr(fm, 'horizontalAdvance') else fm.width(speech)  # type: float
            bw = tw + 16.0  # type: float
            bh = fm.height() + 8.0  # type: float
            bx = clamp(self.__m_x - bw / 2.0, 2.0, self.width() - bw - 2.0)  # type: float
            by = max(2.0, y - size * 1.05 - bh)  # type: float
            bubble = QPainterPath()  # type: QPainterPath
            bubble.addRoundedRect(QRectF(bx, by, bw, bh), bh / 2.0, bh / 2.0)
            p.setPen(QPen(QColor(20, 20, 30, 60), 1.0))
            p.setBrush(QColor('#FFFFFF'))
            p.drawPath(bubble)
            p.setFont(f)
            p.setPen(QColor('#22222A'))
            p.drawText(QRectF(bx, by, bw, bh), Qt.AlignCenter, speech)
        p.end()

    def _drawSnail(self, p, base, s, now):
        """
        :param p: QPainter
        :param base: (QPointF) point on the track under the snail
        :param s: (qreal | float | int) size
        :param now: qreal | float | int
        :return:
        """
        moving = self.__m_moving  # type: bool
        stretch = 1.0 + (0.1 * sin(self.__m_crawl * 2.0) if moving else 0.0)  # type: float
        body = QColor('#D8C3A5')  # type: QColor
        shell = self.__m_shellColor  # type: QColor
        p.save()
        p.translate(base)
        p.scale(self.__m_facing, 1.0)
        # Body (foot), stretching while crawling.
        p.save()
        p.scale(stretch, 2.0 - stretch)
        foot = QPainterPath()  # type: QPainterPath
        foot.moveTo(-s * 0.6, 0)
        foot.quadTo(-s * 0.2, -s * 0.12, s * 0.3, -s * 0.12)
        foot.quadTo(s * 0.52, -s * 0.16, s * 0.5, -s * 0.02)
        foot.lineTo(s * 0.45, 0)
        foot.closeSubpath()
        p.setPen(QPen(body.darker(140), max(1.0, s * 0.02)))
        p.setBrush(body)
        p.drawPath(foot)
        p.restore()
        # Eye stalks (wobbly).
        hx = s * 0.42 * stretch  # type: float
        wob = sin(now * 5.0) * s * 0.03  # type: float
        for k, (dx, h) in enumerate(((0.06, 0.42), (-0.04, 0.36))):
            tip = QPointF(hx + dx * s + wob * (1 if k else -1), -s * h)  # type: QPointF
            p.setPen(QPen(body.darker(120), max(1.5, s * 0.04), Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(hx - s * 0.02, -s * 0.12), tip)
            p.setPen(QPen(body.darker(150), 1.0))
            p.setBrush(QColor('#FFFFFF'))
            p.drawEllipse(tip, s * 0.06, s * 0.06)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor('#1E1E24'))
            p.drawEllipse(QPointF(tip.x() + s * 0.02, tip.y()), s * 0.03, s * 0.03)
        # Smile.
        p.setPen(QPen(body.darker(170), max(1.0, s * 0.025), Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        p.drawArc(QRectF(hx - s * 0.04, -s * 0.11, s * 0.1, s * 0.06), 200 * 16, 140 * 16)
        # Shell with spiral.
        sc = QPointF(-s * 0.1, -s * 0.34)  # type: QPointF
        sr = s * 0.3  # type: float
        p.setPen(QPen(shell.darker(140), max(1.0, s * 0.03)))
        p.setBrush(shell)
        p.drawEllipse(sc, sr, sr)
        spiral = QPainterPath()  # type: QPainterPath
        turns = 2.2  # type: float
        for k in range(41):
            t = k / 40.0  # type: float
            ang = t * turns * 2.0 * pi + (self.__m_crawl * 0.5 if moving else 0.0)  # type: float
            rad = sr * 0.85 * (1.0 - t)  # type: float
            pt = QPointF(sc.x() + cos(ang) * rad, sc.y() + sin(ang) * rad)  # type: QPointF
            if k == 0:
                spiral.moveTo(pt)
            else:
                spiral.lineTo(pt)
        p.setPen(QPen(shell.darker(150), max(1.0, s * 0.03), Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        p.drawPath(spiral)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 80))
        p.drawEllipse(QPointF(sc.x() - sr * 0.35, sc.y() - sr * 0.45), sr * 0.25, sr * 0.14)
        p.restore()

    # ---------- Properties ----------
    current = pyqtProperty(int, fget=getCurrent, fset=setCurrent, notify=currentChanged)  # type: pyqtProperty
    steps = pyqtProperty('QStringList', fget=getSteps, fset=setSteps)  # type: pyqtProperty
    speed = pyqtProperty('qreal', fget=getSpeed, fset=setSpeed)  # type: pyqtProperty
    clickable = pyqtProperty(bool, fget=isClickable, fset=setClickable)  # type: pyqtProperty
    accentColor = pyqtProperty(QColor, fget=getAccentColor, fset=setAccentColor)  # type: pyqtProperty
    shellColor = pyqtProperty(QColor, fget=getShellColor, fset=setShellColor)  # type: pyqtProperty
