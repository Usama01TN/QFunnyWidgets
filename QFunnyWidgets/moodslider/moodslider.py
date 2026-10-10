# -*- coding: utf-8 -*-
"""
MoodSliderWidget: a horizontal slider whose thumb is a face. Slide left, and it gets furious (red,
shaking, steaming); slide right, and it becomes ecstatic (heart eyes, floating hearts). The thumb
springs after the value, tilts with drag speed and shows a mood label bubble while you interact.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QFontMetricsF, QRadialGradient
from ManyQt.QtWidgets import QWidget
from random import uniform
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


def lerp(a, b, t):
    """
    :param a: qreal | float | int
    :param b: qreal | float | int
    :param t: qreal | float | int
    :return: qreal | float | int
    """
    return a + (b - a) * t


MOOD_STOPS = [(0.0, QColor('#E63946')), (0.25, QColor('#F4845F')), (0.5, QColor('#FFD23F')),
              (0.75, QColor('#9BDB4D')), (1.0, QColor('#3BCEAC'))]  # type: list[tuple]
DEFAULT_LABELS = ['Furious', 'Grumpy', 'Meh', 'Happy', 'Ecstatic']  # type: list[str]


def moodColor(t):
    """
    :param t: (qreal | float | int) 0..1
    :return: QColor
    """
    t = clamp(t, 0.0, 1.0)  # type: float
    for i in range(len(MOOD_STOPS) - 1):
        a, ca = MOOD_STOPS[i]
        b, cb = MOOD_STOPS[i + 1]
        if t <= b:
            k = (t - a) / float(b - a)  # type: float
            return QColor(int(lerp(ca.red(), cb.red(), k)), int(lerp(ca.green(), cb.green(), k)),
                          int(lerp(ca.blue(), cb.blue(), k)))
    return QColor(MOOD_STOPS[-1][1])


def heartPath(c, size):
    """
    :param c: (QPointF) center
    :param size: (qreal | float | int) half width
    :return: QPainterPath
    """
    x = c.x()  # type: float
    y = c.y()  # type: float
    s = size  # type: float
    path = QPainterPath()  # type: QPainterPath
    path.moveTo(x, y + s * 0.9)
    path.cubicTo(x - s * 1.6, y - s * 0.1, x - s * 0.7, y - s * 1.4, x, y - s * 0.45)
    path.cubicTo(x + s * 0.7, y - s * 1.4, x + s * 1.6, y - s * 0.1, x, y + s * 0.9)
    return path


class FloatItem(object):
    """
    A floating heart or steam puff.
    """

    def __init__(self, x=0.0, y=0.0, vx=0.0, vy=0.0, life=1.0, kind=0):
        """
        :param x: qreal | float | int
        :param y: qreal | float | int
        :param vx: qreal | float | int
        :param vy: qreal | float | int
        :param life: (qreal | float | int) s
        :param kind: (int) 0 = heart, 1 = steam
        """
        self.x = float(x)  # type: float
        self.y = float(y)  # type: float
        self.vx = float(vx)  # type: float
        self.vy = float(vy)  # type: float
        self.life = float(life)  # type: float
        self.maxLife = float(life)  # type: float
        self.kind = int(kind)  # type: int


class MoodSliderWidget(QWidget):
    """
    An emotional slider.
    """
    valueChanged = pyqtSignal(int)  # type: pyqtSignal
    moodChanged = pyqtSignal('QString')  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param value: int
        :param minimum: int
        :param maximum: int
        :param labels: (list[str | unicode | QString]) Mood names from worst to best.
        :param showLabel: bool
        :param trackColor: QColor | Qt.GlobalColor | int | str | QString
        :param valueChanged: callable | None
        :param moodChanged: callable | None
        :param args: any
        :param kwargs: any
        """
        value = kwargs.pop('value', 50)  # type: int
        minimum = kwargs.pop('minimum', 0)  # type: int
        maximum = kwargs.pop('maximum', 100)  # type: int
        labels = kwargs.pop('labels', DEFAULT_LABELS)  # type: list[str]
        showLabel = kwargs.pop('showLabel', True)  # type: bool
        trackColor = kwargs.pop('trackColor', QColor(127, 127, 127, 70))  # type: QColor
        valueChanged = kwargs.pop('valueChanged', None)  # type: callable | None
        moodChanged = kwargs.pop('moodChanged', None)  # type: callable | None
        super(MoodSliderWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_minimum = int(minimum)  # type: int
        self.__m_maximum = max(self.__m_minimum + 1, int(maximum))  # type: int
        self.__m_value = int(clamp(int(value), self.__m_minimum, self.__m_maximum))  # type: int
        self.__m_labels = list(labels) or list(DEFAULT_LABELS)  # type: list[str]
        self.__m_showLabel = bool(showLabel)  # type: bool
        self.__m_trackColor = QColor(trackColor)  # type: QColor
        if callable(valueChanged):
            self.valueChanged.connect(valueChanged)
        if callable(moodChanged):
            self.moodChanged.connect(moodChanged)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.PointingHandCursor)
        # State.
        self.__m_shown = self._ratio()  # type: float  # animated thumb position 0..1
        self.__m_vel = 0.0  # type: float
        self.__m_dragging = False  # type: bool
        self.__m_hovered = False  # type: bool
        self.__m_bubble = 0.0  # type: float
        self.__m_press = 0.0  # type: float
        self.__m_items = []  # type: list[FloatItem]
        self.__m_spawn = 0.0  # type: float
        self.__m_lastMood = self.getMood()  # type: str
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

    def _ratio(self):
        """
        :return: qreal | float | int
        """
        return (self.__m_value - self.__m_minimum) / float(self.__m_maximum - self.__m_minimum)

    def _geometry(self):
        """
        :return: (tuple) face radius float, track left float, track right float, track y float
        """
        h = float(self.height())  # type: float
        r = clamp((h - 54.0) / 2.0, 12.0, 30.0)  # type: float
        left = r + 6.0  # type: float
        right = max(left + 1.0, self.width() - r - 6.0)  # type: float
        y = h - r - 8.0  # type: float
        return r, left, right, y

    def _valueFromX(self, x):
        """
        :param x: qreal | float | int
        :return: int
        """
        r, left, right, y = self._geometry()
        t = clamp((x - left) / (right - left), 0.0, 1.0)  # type: float
        return int(round(self.__m_minimum + t * (self.__m_maximum - self.__m_minimum)))

    # ---------- Public API ----------
    def getMood(self):
        """
        :return: (str | unicode | QString) Current mood label.
        """
        n = len(self.__m_labels)  # type: int
        return self.__m_labels[min(n - 1, int(self._ratio() * n))]

    def getValue(self):
        """
        :return: int
        """
        return self.__m_value

    @pyqtSlot(int)
    def setValue(self, value):
        """
        :param value: int
        :return:
        """
        value = int(clamp(int(value), self.__m_minimum, self.__m_maximum))  # type: int
        if value != self.__m_value:
            self.__m_value = value  # type: int
            self.valueChanged.emit(value)
            mood = self.getMood()  # type: str
            if mood != self.__m_lastMood:
                self.__m_lastMood = mood  # type: str
                self.moodChanged.emit(mood)
            self.update()

    def getMinimum(self):
        """
        :return: int
        """
        return self.__m_minimum

    @pyqtSlot(int)
    def setMinimum(self, minimum):
        """
        :param minimum: int
        :return:
        """
        self.__m_minimum = min(int(minimum), self.__m_maximum - 1)  # type: int
        self.setValue(self.__m_value)
        self.update()

    def getMaximum(self):
        """
        :return: int
        """
        return self.__m_maximum

    @pyqtSlot(int)
    def setMaximum(self, maximum):
        """
        :param maximum: int
        :return:
        """
        self.__m_maximum = max(int(maximum), self.__m_minimum + 1)  # type: int
        self.setValue(self.__m_value)
        self.update()

    def getLabels(self):
        """
        :return: list[str | unicode | QString]
        """
        return list(self.__m_labels)

    @pyqtSlot(list)
    def setLabels(self, labels):
        """
        :param labels: list[str]
        :return:
        """
        self.__m_labels = list(labels) or list(DEFAULT_LABELS)  # type: list[str]
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
        if self.__m_trackColor != color:
            self.__m_trackColor = color  # type: QColor
            self.update()

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(340, 110)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(120, 70)

    def enterEvent(self, e):
        """
        :param e: QEvent
        :return:
        """
        self.__m_hovered = True  # type: bool
        super(MoodSliderWidget, self).enterEvent(e)

    def leaveEvent(self, e):
        """
        :param e: QEvent
        :return:
        """
        self.__m_hovered = False  # type: bool
        super(MoodSliderWidget, self).leaveEvent(e)

    def mousePressEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if e.button() == Qt.LeftButton:
            self.__m_dragging = True  # type: bool
            self.setValue(self._valueFromX(eventPos(e).x()))
        super(MoodSliderWidget, self).mousePressEvent(e)

    def mouseMoveEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if self.__m_dragging:
            self.setValue(self._valueFromX(eventPos(e).x()))
        super(MoodSliderWidget, self).mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        self.__m_dragging = False  # type: bool
        super(MoodSliderWidget, self).mouseReleaseEvent(e)

    def wheelEvent(self, e):
        """
        :param e: QWheelEvent
        :return:
        """
        step = 1 if e.angleDelta().y() > 0 else -1  # type: int
        self.setValue(self.__m_value + step * max(1, (self.__m_maximum - self.__m_minimum) // 50))
        e.accept()

    def keyPressEvent(self, e):
        """
        :param e: QKeyEvent
        :return:
        """
        span = self.__m_maximum - self.__m_minimum  # type: int
        steps = {Qt.Key_Left: -1, Qt.Key_Down: -1, Qt.Key_Right: 1, Qt.Key_Up: 1,
                 Qt.Key_PageDown: -max(1, span // 10), Qt.Key_PageUp: max(1, span // 10)}  # type: dict
        if e.key() in steps:
            self.setValue(self.__m_value + steps[e.key()])
        elif e.key() == Qt.Key_Home:
            self.setValue(self.__m_minimum)
        elif e.key() == Qt.Key_End:
            self.setValue(self.__m_maximum)
        else:
            super(MoodSliderWidget, self).keyPressEvent(e)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(MoodSliderWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(MoodSliderWidget, self).hideEvent(event)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        target = self._ratio()  # type: float
        self.__m_vel += ((target - self.__m_shown) * 300.0 - self.__m_vel * 20.0) * dt
        self.__m_shown += self.__m_vel * dt
        showBubble = self.__m_showLabel and (self.__m_dragging or self.__m_hovered or self.hasFocus())  # type: bool
        self.__m_bubble += ((1.0 if showBubble else 0.0) - self.__m_bubble) * min(1.0, dt * 10.0)
        self.__m_press += ((1.0 if self.__m_dragging else 0.0) - self.__m_press) * min(1.0, dt * 14.0)
        # Spawn hearts (ecstatic) or steam (furious).
        r, left, right, y = self._geometry()
        t = clamp(self.__m_shown, 0.0, 1.0)  # type: float
        cx = lerp(left, right, t)  # type: float
        rate = 0.0  # type: float
        kind = 0  # type: int
        if t > 0.9:
            rate = (t - 0.9) * 60.0  # type: float
            kind = 0  # type: int
        elif t < 0.1:
            rate = (0.1 - t) * 90.0  # type: float
            kind = 1  # type: int
        self.__m_spawn += rate * dt
        while self.__m_spawn > 1.0:
            self.__m_spawn -= 1.0
            if kind == 0:
                self.__m_items.append(FloatItem(cx + uniform(-r, r), y - r * 0.6, uniform(-15, 15),
                                                uniform(-70, -40), uniform(0.9, 1.4), 0))
            else:
                side = -1.0 if uniform(0, 1) < 0.5 else 1.0  # type: float
                self.__m_items.append(FloatItem(cx + side * r * 0.75, y - r * 0.75, side * uniform(20, 40),
                                                uniform(-60, -35), uniform(0.6, 0.9), 1))
        alive = []  # type: list[FloatItem]
        for it in self.__m_items:
            it.x += it.vx * dt + (sin(now * 5.0 + it.y * 0.1) * 12.0 * dt if it.kind == 0 else 0.0)
            it.y += it.vy * dt
            it.life -= dt
            if it.life > 0:
                alive.append(it)
        self.__m_items = alive  # type: list[FloatItem]
        self.update()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        now = self._now()  # type: float
        r, left, right, y = self._geometry()
        t = clamp(self.__m_shown, 0.0, 1.0)  # type: float
        mc = moodColor(t)  # type: QColor
        cx = lerp(left, right, t)  # type: float
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        # Track.
        th = max(6.0, r * 0.35)  # type: float
        track = QRectF(left, y - th / 2.0, right - left, th)  # type: QRectF
        p.setPen(Qt.NoPen)
        p.setBrush(self.__m_trackColor)
        p.drawRoundedRect(track, th / 2.0, th / 2.0)
        p.setBrush(mc)
        p.drawRoundedRect(QRectF(left, y - th / 2.0, max(th, cx - left), th), th / 2.0, th / 2.0)
        # Tick dots.
        n = len(self.__m_labels)  # type: int
        for i in range(n):
            tx = lerp(left, right, (i + 0.5) / float(n))  # type: float
            dc = QColor(255, 255, 255, 140) if tx < cx else QColor(127, 127, 127, 120)  # type: QColor
            p.setBrush(dc)
            p.drawEllipse(QPointF(tx, y), th * 0.18, th * 0.18)
        # Floating hearts / steam (behind face).
        for it in self.__m_items:
            a = clamp(it.life / it.maxLife, 0.0, 1.0)  # type: float
            if it.kind == 0:
                c = QColor('#FF4D6D')  # type: QColor
                c.setAlpha(int(230 * a))
                p.fillPath(heartPath(QPointF(it.x, it.y), r * 0.18 * (1.3 - a * 0.3)), c)
            else:
                c = QColor(200, 200, 210)  # type: QColor
                c.setAlpha(int(180 * a))
                p.setBrush(c)
                rr = r * (0.12 + 0.2 * (1.0 - a))  # type: float
                p.drawEllipse(QPointF(it.x, it.y), rr, rr)
        # Face.
        p.save()
        shake = (1.0 - t / 0.1) * 2.5 if t < 0.1 else 0.0  # type: float
        p.translate(cx + uniform(-shake, shake), y + uniform(-shake, shake) * 0.5)
        p.rotate(clamp(-self.__m_vel * 25.0, -25.0, 25.0))
        p.scale(1.0 + 0.1 * self.__m_press, 1.0 - 0.1 * self.__m_press)
        self._drawFace(p, r, t, mc, now)
        p.restore()
        # Mood bubble.
        if self.__m_bubble > 0.02:
            self._drawBubble(p, self.getMood(), cx, y - r - 8.0, mc)
        p.end()

    def _drawFace(self, p, r, t, mc, now):
        """
        :param p: QPainter
        :param r: (qreal | float | int) face radius
        :param t: (qreal | float | int) mood 0..1
        :param mc: (QColor) mood color
        :param now: qreal | float | int
        :return:
        """
        ink = QColor('#2B2B33')  # type: QColor
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 45))
        p.drawEllipse(QPointF(0, r * 0.1), r, r)
        grad = QRadialGradient(QPointF(-r * 0.35, -r * 0.4), r * 1.7)  # type: QRadialGradient
        grad.setColorAt(0.0, mc.lighter(130))
        grad.setColorAt(1.0, mc.darker(115))
        p.setBrush(grad)
        p.setPen(QPen(mc.darker(140), max(1.0, r * 0.05)))
        p.drawEllipse(QPointF(0, 0), r, r)
        ex = r * 0.36  # type: float
        ey = -r * 0.12  # type: float
        pen = QPen(ink, max(1.2, r * 0.08), Qt.SolidLine, Qt.RoundCap)  # type: QPen
        # Eyebrows: angry (inner low) -> relaxed -> raised.
        browTilt = lerp(0.5, -0.15, t) * r  # type: float
        browY = ey - r * lerp(0.28, 0.42, t)  # type: float
        if t < 0.5 or t > 0.75:
            p.setPen(pen)
            for d in (-1.0, 1.0):
                p.drawLine(QPointF(d * (ex - r * 0.2), browY + browTilt * 0.5),
                           QPointF(d * (ex + r * 0.18), browY - browTilt * 0.5))
        # Eyes.
        if t > 0.92:
            beat = 1.0 + 0.12 * sin(now * 10.0)  # type: float
            for d in (-1.0, 1.0):
                p.fillPath(heartPath(QPointF(d * ex, ey), r * 0.17 * beat), QColor('#E5383B'))
        else:
            # Pupils slightly squinted when furious, wide when happy.
            eh = r * lerp(0.08, 0.15, t)  # type: float
            p.setPen(Qt.NoPen)
            p.setBrush(ink)
            for d in (-1.0, 1.0):
                p.drawEllipse(QPointF(d * ex, ey), r * 0.11, eh)
                p.setBrush(QColor('#FFFFFF'))
                p.drawEllipse(QPointF(d * ex - r * 0.035, ey - eh * 0.4), r * 0.035, r * 0.035)
                p.setBrush(ink)
        # Mouth: curvature from frown to grin.
        curve = lerp(-0.32, 0.45, t) * r  # type: float
        mw = r * lerp(0.5, 0.75, t)  # type: float
        my = r * lerp(0.42, 0.3, t)  # type: float
        mouth = QPainterPath()  # type: QPainterPath
        mouth.moveTo(-mw / 2.0, my)
        mouth.quadTo(0, my + curve, mw / 2.0, my)
        p.setPen(pen)
        if t > 0.7:
            mouth.closeSubpath()
            p.setBrush(QColor('#8E1B2A'))
        else:
            p.setBrush(Qt.NoBrush)
        if 0.42 < t < 0.58:
            # "Meh": perfectly flat, slightly off-center.
            p.drawLine(QPointF(-mw / 2.0 + r * 0.05, my + r * 0.02), QPointF(mw / 2.0, my - r * 0.04))
        else:
            p.drawPath(mouth)
        # Blush when happy.
        if t > 0.6:
            bc = QColor('#FF7A90')  # type: QColor
            bc.setAlpha(int(160 * (t - 0.6) / 0.4))
            p.setPen(Qt.NoPen)
            p.setBrush(bc)
            for d in (-1.0, 1.0):
                p.drawEllipse(QPointF(d * r * 0.62, r * 0.18), r * 0.14, r * 0.08)

    def _drawBubble(self, p, text, x, bottom, color):
        """
        :param p: QPainter
        :param text: str | unicode | QString
        :param x: (qreal | float | int) center x
        :param bottom: (qreal | float | int) y of the bubble tip
        :param color: QColor
        :return:
        """
        f = QFont(self.font())  # type: QFont
        f.setBold(True)
        f.setPointSizeF(9.0)
        fm = QFontMetricsF(f)  # type: QFontMetricsF
        tw = fm.horizontalAdvance(text) if hasattr(fm, 'horizontalAdvance') else fm.width(text)  # type: float
        bw = tw + 18.0  # type: float
        bh = fm.height() + 8.0  # type: float
        bx = clamp(x - bw / 2.0, 2.0, max(2.0, self.width() - bw - 2.0))  # type: float
        by = bottom - bh - 6.0  # type: float
        a = self.__m_bubble  # type: float
        p.save()
        p.setOpacity(a)
        p.translate(x, bottom)
        p.scale(0.7 + 0.3 * a, 0.7 + 0.3 * a)
        p.translate(-x, -bottom)
        path = QPainterPath()  # type: QPainterPath
        path.addRoundedRect(QRectF(bx, by, bw, bh), bh / 2.0, bh / 2.0)
        tail = QPainterPath()  # type: QPainterPath
        tail.moveTo(x - 5.0, by + bh - 1.0)
        tail.lineTo(x, bottom)
        tail.lineTo(x + 5.0, by + bh - 1.0)
        tail.closeSubpath()
        path = path.united(tail)  # type: QPainterPath
        p.setPen(Qt.NoPen)
        p.setBrush(color.darker(125))
        p.drawPath(path)
        p.setFont(f)
        p.setPen(QColor('#FFFFFF'))
        p.drawText(QRectF(bx, by, bw, bh), Qt.AlignCenter, text)
        p.restore()

    # ---------- Properties ----------
    value = pyqtProperty(int, fget=getValue, fset=setValue, notify=valueChanged)  # type: pyqtProperty
    minimum = pyqtProperty(int, fget=getMinimum, fset=setMinimum)  # type: pyqtProperty
    maximum = pyqtProperty(int, fget=getMaximum, fset=setMaximum)  # type: pyqtProperty
    labels = pyqtProperty('QStringList', fget=getLabels, fset=setLabels)  # type: pyqtProperty
    showLabel = pyqtProperty(bool, fget=isShowLabel, fset=setShowLabel)  # type: pyqtProperty
    trackColor = pyqtProperty(QColor, fget=getTrackColor, fset=setTrackColor)  # type: pyqtProperty
