# -*- coding: utf-8 -*-
"""
VolumeKnobWidget: a rotary volume dial with a face. Muted, its mouth is zipped; low volume makes it
hum contentedly, medium makes it sing (music notes float away), loud makes it squint with sound waves,
and at maximum it screams, shakes and the whole knob blushes red.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QRadialGradient
from ManyQt.QtWidgets import QWidget
from math import sin, cos, atan2, degrees, radians
from random import uniform


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


def levelColor(t):
    """
    :param t: (qreal | float | int) 0..1
    :return: QColor
    """
    stops = [(0.0, QColor('#3BCEAC')), (0.55, QColor('#FFD23F')), (0.8, QColor('#FF9F1C')), (1.0, QColor('#E63946'))]
    t = clamp(t, 0.0, 1.0)  # type: float
    for i in range(len(stops) - 1):
        a, ca = stops[i]
        b, cb = stops[i + 1]
        if t <= b:
            k = (t - a) / float(b - a)  # type: float
            return QColor(int(lerp(ca.red(), cb.red(), k)), int(lerp(ca.green(), cb.green(), k)),
                          int(lerp(ca.blue(), cb.blue(), k)))
    return QColor(stops[-1][1])


MOODS = [(0.0, 'Muted'), (0.3, 'Whisper'), (0.65, 'Chill'), (0.9, 'Party'), (1.01, 'NEIGHBOURS ARE CALLING')]  # type: list
START_ANGLE = 225.0  # type: float  # degrees, maths convention (0 = right, counter-clockwise)
SWEEP = 270.0  # type: float


class Note(object):
    """
    A floating music note.
    """

    def __init__(self, x=0.0, y=0.0, vx=0.0, vy=0.0, life=1.5, size=1.0):
        """
        :param x: qreal | float | int
        :param y: qreal | float | int
        :param vx: qreal | float | int
        :param vy: qreal | float | int
        :param life: (qreal | float | int) s
        :param size: (qreal | float | int) scale
        """
        self.x = float(x)  # type: float
        self.y = float(y)  # type: float
        self.vx = float(vx)  # type: float
        self.vy = float(vy)  # type: float
        self.life = float(life)  # type: float
        self.maxLife = float(life)  # type: float
        self.size = float(size)  # type: float


class VolumeKnobWidget(QWidget):
    """
    Rotary volume knob with feelings about loud music.
    """
    valueChanged = pyqtSignal(int)  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param value: (int) 0..100
        :param knobColor: QColor | Qt.GlobalColor | int | str | QString
        :param trackColor: QColor | Qt.GlobalColor | int | str | QString
        :param showLabel: bool
        :param valueChanged: callable | None
        :param args: any
        :param kwargs: any
        """
        value = kwargs.pop('value', 40)  # type: int
        knobColor = kwargs.pop('knobColor', '#E9EAF0')  # type: QColor
        trackColor = kwargs.pop('trackColor', QColor(127, 127, 127, 60))  # type: QColor
        showLabel = kwargs.pop('showLabel', True)  # type: bool
        valueChanged = kwargs.pop('valueChanged', None)  # type: callable | None
        super(VolumeKnobWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_value = int(clamp(int(value), 0, 100))  # type: int
        self.__m_knobColor = QColor(knobColor)  # type: QColor
        self.__m_trackColor = QColor(trackColor)  # type: QColor
        self.__m_showLabel = bool(showLabel)  # type: bool
        if callable(valueChanged):
            self.valueChanged.connect(valueChanged)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.OpenHandCursor)
        # State.
        self.__m_shown = self.__m_value / 100.0  # type: float
        self.__m_dragging = False  # type: bool
        self.__m_beforeMute = 40  # type: int
        self.__m_notes = []  # type: list[Note]
        self.__m_noteAcc = 0.0  # type: float
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
        :return: (tuple) center QPointF, knob radius float, label area top float
        """
        w = float(self.width())  # type: float
        h = float(self.height())  # type: float
        labelH = 40.0 if self.__m_showLabel else 0.0  # type: float
        R = max(12.0, min(w, h - labelH) / 2.0 * 0.62)  # type: float
        return QPointF(w / 2.0, (h - labelH) / 2.0), R, h - labelH

    def _valueFromPos(self, pos):
        """
        :param pos: QPointF
        :return: int
        """
        c, R, top = self._geometry()
        ang = degrees(atan2(-(pos.y() - c.y()), pos.x() - c.x()))  # type: float
        d = (START_ANGLE - ang) % 360.0  # type: float
        if d > SWEEP:
            # Dead zone at the bottom: snap to the closer end.
            return 100 if d < SWEEP + (360.0 - SWEEP) / 2.0 else 0
        return int(round(d / SWEEP * 100.0))

    def _mood(self, t):
        """
        :param t: (qreal | float | int) 0..1
        :return: str | unicode | QString
        """
        if t <= 0.001:
            return MOODS[0][1]
        for limit, name in MOODS[1:]:
            if t < limit:
                return name
        return MOODS[-1][1]

    # ---------- Public API ----------
    @pyqtSlot()
    def toggleMute(self):
        """
        :return:
        """
        if self.__m_value > 0:
            self.__m_beforeMute = self.__m_value  # type: int
            self.setValue(0)
        else:
            self.setValue(self.__m_beforeMute or 40)

    def getValue(self):
        """
        :return: int
        """
        return self.__m_value

    @pyqtSlot(int)
    def setValue(self, value):
        """
        :param value: (int) 0..100
        :return:
        """
        value = int(clamp(int(value), 0, 100))  # type: int
        if value != self.__m_value:
            self.__m_value = value  # type: int
            self.valueChanged.emit(value)
            self.update()

    def getKnobColor(self):
        """
        :return: QColor
        """
        return self.__m_knobColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setKnobColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        if self.__m_knobColor != color:
            self.__m_knobColor = color  # type: QColor
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
        return QSize(240, 260)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(100, 120)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(VolumeKnobWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(VolumeKnobWidget, self).hideEvent(event)

    def mousePressEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if e.button() == Qt.LeftButton:
            self.__m_dragging = True  # type: bool
            self.setCursor(Qt.ClosedHandCursor)
            self.setValue(self._valueFromPos(eventPos(e)))
        super(VolumeKnobWidget, self).mousePressEvent(e)

    def mouseMoveEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if self.__m_dragging:
            v = self._valueFromPos(eventPos(e))  # type: int
            # Avoid jumping from 100 straight to 0 across the dead zone.
            if abs(v - self.__m_value) < 60:
                self.setValue(v)
        super(VolumeKnobWidget, self).mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        self.__m_dragging = False  # type: bool
        self.setCursor(Qt.OpenHandCursor)
        super(VolumeKnobWidget, self).mouseReleaseEvent(e)

    def mouseDoubleClickEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        self.toggleMute()
        super(VolumeKnobWidget, self).mouseDoubleClickEvent(e)

    def wheelEvent(self, e):
        """
        :param e: QWheelEvent
        :return:
        """
        self.setValue(self.__m_value + (3 if e.angleDelta().y() > 0 else -3))
        e.accept()

    def keyPressEvent(self, e):
        """
        :param e: QKeyEvent
        :return:
        """
        k = e.key()  # type: int
        if k in (Qt.Key_Up, Qt.Key_Right):
            self.setValue(self.__m_value + 1)
        elif k in (Qt.Key_Down, Qt.Key_Left):
            self.setValue(self.__m_value - 1)
        elif k == Qt.Key_PageUp:
            self.setValue(self.__m_value + 10)
        elif k == Qt.Key_PageDown:
            self.setValue(self.__m_value - 10)
        elif k == Qt.Key_M:
            self.toggleMute()
        else:
            super(VolumeKnobWidget, self).keyPressEvent(e)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        self.__m_shown += (self.__m_value / 100.0 - self.__m_shown) * min(1.0, dt * 14.0)
        t = self.__m_shown  # type: float
        c, R, top = self._geometry()
        if 0.05 < t < 0.9:
            self.__m_noteAcc += dt * (0.8 + t * 4.0)
            while self.__m_noteAcc > 1.0:
                self.__m_noteAcc -= 1.0
                side = -1.0 if uniform(0, 1) < 0.5 else 1.0  # type: float
                self.__m_notes.append(Note(c.x() + side * R * 0.9, c.y() - R * 0.3, side * uniform(15, 35),
                                           -uniform(25, 45), uniform(1.2, 1.8), R / 60.0 * uniform(0.8, 1.2)))
        alive = []  # type: list[Note]
        for n in self.__m_notes:
            n.x += n.vx * dt + sin(now * 4.0 + n.y * 0.05) * 10.0 * dt
            n.y += n.vy * dt
            n.life -= dt
            if n.life > 0:
                alive.append(n)
        self.__m_notes = alive  # type: list[Note]
        self.update()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        now = self._now()  # type: float
        c, R, labelTop = self._geometry()
        t = clamp(self.__m_shown, 0.0, 1.0)  # type: float
        lc = levelColor(t)  # type: QColor
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        # Sound waves.
        if t > 0.65:
            loud = (t - 0.65) / 0.35  # type: float
            wc = QColor(lc)  # type: QColor
            for k in range(3):
                ph = (now * (1.5 + loud * 2.0) + k / 3.0) % 1.0  # type: float
                wc.setAlpha(int(200 * (1.0 - ph) * (0.4 + 0.6 * loud)))
                p.setPen(QPen(wc, max(1.5, R * 0.05), Qt.SolidLine, Qt.RoundCap))
                p.setBrush(Qt.NoBrush)
                rr = R * (1.4 + ph * 0.5)  # type: float
                rect = QRectF(c.x() - rr, c.y() - rr, rr * 2, rr * 2)  # type: QRectF
                p.drawArc(rect, -30 * 16, 60 * 16)
                p.drawArc(rect, 150 * 16, 60 * 16)
        # Track + level ring.
        rr = R * 1.2  # type: float
        ring = QRectF(c.x() - rr, c.y() - rr, rr * 2, rr * 2)  # type: QRectF
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(self.__m_trackColor, R * 0.11, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(ring, int(START_ANGLE * 16), int(-SWEEP * 16))
        if t > 0.004:
            p.setPen(QPen(lc, R * 0.11, Qt.SolidLine, Qt.RoundCap))
            p.drawArc(ring, int(START_ANGLE * 16), int(-SWEEP * t * 16))
        # Knob (shakes when loud).
        shake = R * 0.04 * clamp((t - 0.7) / 0.3, 0.0, 1.0) ** 2  # type: float
        kc = QPointF(c.x() + uniform(-shake, shake), c.y() + uniform(-shake, shake))  # type: QPointF
        base = self.__m_knobColor  # type: QColor
        if t > 0.9:
            k = (t - 0.9) / 0.1 * (0.6 + 0.4 * sin(now * 14.0))  # type: float
            base = QColor(int(lerp(base.red(), 255, k * 0.5)), int(lerp(base.green(), 120, k * 0.5)),
                          int(lerp(base.blue(), 120, k * 0.5)))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 55))
        p.drawEllipse(kc + QPointF(0, R * 0.08), R, R)
        grad = QRadialGradient(kc + QPointF(-R * 0.3, -R * 0.4), R * 1.7)  # type: QRadialGradient
        grad.setColorAt(0.0, base.lighter(110))
        grad.setColorAt(1.0, base.darker(125))
        p.setBrush(grad)
        p.setPen(QPen(base.darker(140), max(1.0, R * 0.03)))
        p.drawEllipse(kc, R, R)
        # Grip ridges + notch rotate with the value.
        ang = radians(START_ANGLE - SWEEP * t)  # type: float
        p.setPen(QPen(base.darker(118), max(1.0, R * 0.03), Qt.SolidLine, Qt.RoundCap))
        for k in range(24):
            a = ang + k * 3.14159265 * 2.0 / 24.0  # type: float
            p.drawLine(QPointF(kc.x() + cos(a) * R * 0.88, kc.y() - sin(a) * R * 0.88),
                       QPointF(kc.x() + cos(a) * R * 0.97, kc.y() - sin(a) * R * 0.97))
        p.setPen(Qt.NoPen)
        p.setBrush(lc.darker(110))
        p.drawEllipse(QPointF(kc.x() + cos(ang) * R * 0.76, kc.y() - sin(ang) * R * 0.76), R * 0.07, R * 0.07)
        self._drawFace(p, kc, R * 0.62, t, now)
        # Notes.
        for n in self.__m_notes:
            nc = QColor(lc)  # type: QColor
            nc.setAlpha(int(230 * clamp(n.life / n.maxLife, 0.0, 1.0)))
            self._drawNote(p, QPointF(n.x, n.y), n.size, nc)
        # Label.
        if self.__m_showLabel:
            tc = QColor(self.palette().text().color())  # type: QColor
            f = QFont(self.font())  # type: QFont
            f.setBold(True)
            f.setPointSizeF(11.0)
            p.setFont(f)
            p.setPen(tc)
            p.drawText(QRectF(0, labelTop, self.width(), 20), Qt.AlignCenter, '{}%'.format(self.__m_value))
            f2 = QFont(self.font())  # type: QFont
            f2.setPointSizeF(8.5)
            f2.setBold(t >= 0.9)
            p.setFont(f2)
            mc = QColor(lc) if t >= 0.9 else QColor(tc)  # type: QColor
            if t < 0.9:
                mc.setAlpha(160)
            p.setPen(mc)
            p.drawText(QRectF(0, labelTop + 19, self.width(), 18), Qt.AlignCenter, self._mood(self.__m_value / 100.0))
        p.end()

    def _drawFace(self, p, c, r, t, now):
        """
        :param p: QPainter
        :param c: (QPointF) face center
        :param r: (qreal | float | int) face radius
        :param t: (qreal | float | int) volume 0..1
        :param now: qreal | float | int
        :return:
        """
        ink = QColor('#2B2B33')  # type: QColor
        pen = QPen(ink, max(1.2, r * 0.08), Qt.SolidLine, Qt.RoundCap)  # type: QPen
        ex = r * 0.38  # type: float
        ey = c.y() - r * 0.2  # type: float
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        if t <= 0.004:
            # Peaceful closed eyes, zipped mouth.
            for d in (-1.0, 1.0):
                p.drawArc(QRectF(c.x() + d * ex - r * 0.14, ey - r * 0.06, r * 0.28, r * 0.18), 180 * 16, 180 * 16)
            my = c.y() + r * 0.35  # type: float
            p.drawLine(QPointF(c.x() - r * 0.35, my), QPointF(c.x() + r * 0.35, my))
            zp = QPen(ink, max(1.0, r * 0.05))  # type: QPen
            p.setPen(zp)
            for k in range(7):
                x = c.x() - r * 0.3 + k * r * 0.1  # type: float
                p.drawLine(QPointF(x, my - r * 0.07), QPointF(x, my + r * 0.07))
            p.setBrush(QColor('#C9A227'))
            p.drawRoundedRect(QRectF(c.x() + r * 0.33, my - r * 0.08, r * 0.14, r * 0.2), 2, 2)
            return
        if t < 0.3:
            # Content: open eyes, gentle smile.
            p.setPen(Qt.NoPen)
            p.setBrush(ink)
            for d in (-1.0, 1.0):
                p.drawEllipse(QPointF(c.x() + d * ex, ey), r * 0.09, r * 0.11)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            p.drawArc(QRectF(c.x() - r * 0.22, c.y() + r * 0.05, r * 0.44, r * 0.3), 200 * 16, 140 * 16)
        elif t < 0.65:
            # Singing: happy closed eyes, "o" mouth pulsing with the beat.
            for d in (-1.0, 1.0):
                p.drawArc(QRectF(c.x() + d * ex - r * 0.14, ey - r * 0.1, r * 0.28, r * 0.2), 20 * 16, 140 * 16)
            beat = 0.75 + 0.25 * abs(sin(now * 6.0))  # type: float
            p.setBrush(QColor('#7A2E2E'))
            p.drawEllipse(QPointF(c.x(), c.y() + r * 0.3), r * 0.14 * beat, r * 0.18 * beat)
        elif t < 0.9:
            # Loud: squinting > <, wide mouth.
            for d in (-1.0, 1.0):
                x = c.x() + d * ex  # type: float
                p.drawLine(QPointF(x - d * r * 0.13, ey - r * 0.1), QPointF(x + d * r * 0.08, ey))
                p.drawLine(QPointF(x + d * r * 0.08, ey), QPointF(x - d * r * 0.13, ey + r * 0.1))
            p.setBrush(QColor('#7A2E2E'))
            mouth = QPainterPath()  # type: QPainterPath
            mouth.addRoundedRect(QRectF(c.x() - r * 0.3, c.y() + r * 0.12, r * 0.6, r * 0.38), r * 0.15, r * 0.15)
            p.drawPath(mouth)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor('#FFFFFF'))
            p.drawRect(QRectF(c.x() - r * 0.22, c.y() + r * 0.14, r * 0.44, r * 0.08))
        else:
            # TOO LOUD: huge eyes with tiny pupils, screaming.
            for d in (-1.0, 1.0):
                x = c.x() + d * ex  # type: float
                p.setPen(QPen(ink, max(1.0, r * 0.05)))
                p.setBrush(QColor('#FFFFFF'))
                p.drawEllipse(QPointF(x, ey - r * 0.05), r * 0.22, r * 0.24)
                p.setPen(Qt.NoPen)
                p.setBrush(ink)
                p.drawEllipse(QPointF(x + uniform(-1, 1), ey - r * 0.05 + uniform(-1, 1)), r * 0.05, r * 0.05)
            p.setPen(pen)
            p.setBrush(QColor('#5A1A1A'))
            o = 1.0 + 0.12 * sin(now * 30.0)  # type: float
            p.drawEllipse(QPointF(c.x(), c.y() + r * 0.38), r * 0.24, r * 0.26 * o)

    @staticmethod
    def _drawNote(p, pt, s, color):
        """
        :param p: QPainter
        :param pt: (QPointF) note head center
        :param s: (qreal | float | int) scale
        :param color: QColor
        :return:
        """
        p.save()
        p.translate(pt)
        p.scale(s, s)
        p.rotate(-20)
        p.setPen(Qt.NoPen)
        p.setBrush(color)
        p.drawEllipse(QPointF(0, 0), 5.0, 3.6)
        p.restore()
        p.save()
        p.translate(pt)
        p.scale(s, s)
        p.setPen(QPen(color, 1.6, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(4.2, -1.0), QPointF(4.2, -15.0))
        path = QPainterPath()  # type: QPainterPath
        path.moveTo(4.2, -15.0)
        path.quadTo(10.0, -12.0, 8.0, -6.0)
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)
        p.restore()

    # ---------- Properties ----------
    value = pyqtProperty(int, fget=getValue, fset=setValue, notify=valueChanged)  # type: pyqtProperty
    knobColor = pyqtProperty(QColor, fget=getKnobColor, fset=setKnobColor)  # type: pyqtProperty
    trackColor = pyqtProperty(QColor, fget=getTrackColor, fset=setTrackColor)  # type: pyqtProperty
    showLabel = pyqtProperty(bool, fget=isShowLabel, fset=setShowLabel)  # type: pyqtProperty
