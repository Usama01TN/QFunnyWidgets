# -*- coding: utf-8 -*-
"""
GooglyEyesWidget: a row of googly eyes whose pupils chase the mouse cursor with wobbly spring
physics and gravity, blink at random, get angry when poked repeatedly and spin dizzy on click.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty, QPoint
from ManyQt.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QRadialGradient, QCursor
from ManyQt.QtWidgets import QWidget
from math import sin, cos, pi, hypot
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


class PupilState(object):
    """
    Physics state of one pupil (offset from the eye center, in px).
    """

    def __init__(self, x=0.0, y=0.0, vx=0.0, vy=0.0):
        """
        :param x: qreal | float | int
        :param y: qreal | float | int
        :param vx: qreal | float | int
        :param vy: qreal | float | int
        """
        self.x = float(x)  # type: float
        self.y = float(y)  # type: float
        self.vx = float(vx)  # type: float
        self.vy = float(vy)  # type: float


class GooglyEyesWidget(QWidget):
    """
    Googly eyes that follow the cursor, blink, get grumpy and go dizzy when clicked.
    """
    DIZZY_MS = 1600  # type: int
    BLINK_MS = 160  # type: int
    ANGRY_POKES = 3  # type: int
    poked = pyqtSignal(int)  # type: pyqtSignal
    gotAngry = pyqtSignal()  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param eyeCount: (int) Number of eyes (1..6).
        :param eyeColor: QColor | Qt.GlobalColor | int | str | QString
        :param pupilColor: QColor | Qt.GlobalColor | int | str | QString
        :param lidColor: (QColor | Qt.GlobalColor | int | str | QString) Eyelid color.
        :param wobble: (qreal | float | int) 0 = stiff, 1 = very wobbly.
        :param gravity: (qreal | float | int) Pupil gravity in px/s^2.
        :param blinkInterval: (int) Average ms between blinks.
        :param autoBlink: bool
        :param poked: callable | None
        :param gotAngry: callable | None
        :param args: any
        :param kwargs: any
        """
        eyeCount = kwargs.pop('eyeCount', 2)  # type: int
        eyeColor = kwargs.pop('eyeColor', '#FFFFFF')  # type: QColor
        pupilColor = kwargs.pop('pupilColor', '#17171C')  # type: QColor
        lidColor = kwargs.pop('lidColor', '#F2B8A0')  # type: QColor
        wobble = kwargs.pop('wobble', 0.6)  # type: float
        gravity = kwargs.pop('gravity', 900.0)  # type: float
        blinkInterval = kwargs.pop('blinkInterval', 3500)  # type: int
        autoBlink = kwargs.pop('autoBlink', True)  # type: bool
        poked = kwargs.pop('poked', None)  # type: callable | None
        gotAngry = kwargs.pop('gotAngry', None)  # type: callable | None
        super(GooglyEyesWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_eyeCount = int(clamp(int(eyeCount), 1, 6))  # type: int
        self.__m_eyeColor = QColor(eyeColor)  # type: QColor
        self.__m_pupilColor = QColor(pupilColor)  # type: QColor
        self.__m_lidColor = QColor(lidColor)  # type: QColor
        self.__m_wobble = float(clamp(float(wobble), 0.0, 1.0))  # type: float
        self.__m_gravity = max(0.0, float(gravity))  # type: float
        self.__m_blinkInterval = max(300, int(blinkInterval))  # type: int
        self.__m_autoBlink = bool(autoBlink)  # type: bool
        if callable(poked):
            self.poked.connect(poked)
        if callable(gotAngry):
            self.gotAngry.connect(gotAngry)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        # State.
        self.__m_pupils = [PupilState() for _ in range(self.__m_eyeCount)]  # type: list[PupilState]
        self.__m_pokeCount = 0  # type: int
        self.__m_pokeTimes = []  # type: list[float]
        self.__m_angryUntil = 0.0  # type: float
        self.__m_dizzyUntil = 0.0  # type: float
        self.__m_blinkStart = -1.0  # type: float
        self.__m_nextBlink = 0.0  # type: float
        self.__m_squish = 0.0  # type: float
        self.__m_last = 0.0  # type: float
        self.__m_eyeRects = []  # type: list[QRectF]
        # Timing.
        self.__m_clock = QElapsedTimer()  # type: QElapsedTimer
        self.__m_clock.start()
        self.__m_nextBlink = self._scheduleBlink(0.0)  # type: float
        self.__m_timer = QTimer(self)  # type: QTimer
        self.__m_timer.timeout.connect(self._tick)
        self.__m_timer.start(16)

    # ---------- Helpers ----------
    def _now(self):
        """
        :return: qreal | float | int
        """
        return self.__m_clock.elapsed() / 1000.0

    def _scheduleBlink(self, now):
        """
        :param now: (qreal | float | int) Current time in s.
        :return: qreal | float | int
        """
        base = self.__m_blinkInterval / 1000.0  # type: float
        return now + uniform(base * 0.5, base * 1.5)

    def _layout(self):
        """
        Compute eye rects (cached for painting and hit-testing).
        :return: list[QRectF]
        """
        n = self.__m_eyeCount  # type: int
        w = float(self.width())  # type: float
        h = float(self.height())  # type: float
        gap = 0.18  # type: float
        r = min(w / (n * 2.0 + (n - 1) * gap * 2.0 + 0.4), h / 2.5)  # type: float
        r = max(4.0, r)  # type: float
        total = n * 2.0 * r + (n - 1) * gap * 2.0 * r  # type: float
        x0 = (w - total) / 2.0  # type: float
        cy = h / 2.0 + r * 0.12  # type: float
        rects = []  # type: list[QRectF]
        for i in range(n):
            cx = x0 + r + i * (2.0 * r + gap * 2.0 * r)  # type: float
            rects.append(QRectF(cx - r, cy - r, 2.0 * r, 2.0 * r))
        return rects

    # ---------- Public API ----------
    @pyqtSlot()
    def blink(self):
        """
        Blink right now.
        :return:
        """
        self.__m_blinkStart = self._now()  # type: float
        self.update()

    @pyqtSlot()
    def makeDizzy(self):
        """
        Spin the pupils around for a moment.
        :return:
        """
        self.__m_dizzyUntil = self._now() + self.DIZZY_MS / 1000.0  # type: float
        self.update()

    def getPokeCount(self):
        """
        :return: int
        """
        return self.__m_pokeCount

    def getEyeCount(self):
        """
        :return: int
        """
        return self.__m_eyeCount

    @pyqtSlot(int)
    def setEyeCount(self, eyeCount):
        """
        :param eyeCount: int
        :return:
        """
        eyeCount = int(clamp(int(eyeCount), 1, 6))  # type: int
        if eyeCount != self.__m_eyeCount:
            self.__m_eyeCount = eyeCount  # type: int
            self.__m_pupils = [PupilState() for _ in range(eyeCount)]  # type: list[PupilState]
            self.update()

    def getEyeColor(self):
        """
        :return: QColor
        """
        return self.__m_eyeColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setEyeColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        if self.__m_eyeColor != color:
            self.__m_eyeColor = color  # type: QColor
            self.update()

    def getPupilColor(self):
        """
        :return: QColor
        """
        return self.__m_pupilColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setPupilColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        if self.__m_pupilColor != color:
            self.__m_pupilColor = color  # type: QColor
            self.update()

    def getLidColor(self):
        """
        :return: QColor
        """
        return self.__m_lidColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setLidColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        if self.__m_lidColor != color:
            self.__m_lidColor = color  # type: QColor
            self.update()

    def getWobble(self):
        """
        :return: qreal | float | int
        """
        return self.__m_wobble

    @pyqtSlot('qreal')
    @pyqtSlot(float)
    @pyqtSlot(int)
    def setWobble(self, wobble):
        """
        :param wobble: (qreal | float | int) 0..1
        :return:
        """
        self.__m_wobble = float(clamp(float(wobble), 0.0, 1.0))  # type: float

    def getGravity(self):
        """
        :return: qreal | float | int
        """
        return self.__m_gravity

    @pyqtSlot('qreal')
    @pyqtSlot(float)
    @pyqtSlot(int)
    def setGravity(self, gravity):
        """
        :param gravity: (qreal | float | int) px/s^2
        :return:
        """
        self.__m_gravity = max(0.0, float(gravity))  # type: float

    def getBlinkInterval(self):
        """
        :return: int
        """
        return self.__m_blinkInterval

    @pyqtSlot(int)
    def setBlinkInterval(self, blinkInterval):
        """
        :param blinkInterval: (int) ms
        :return:
        """
        self.__m_blinkInterval = max(300, int(blinkInterval))  # type: int
        self.__m_nextBlink = self._scheduleBlink(self._now())  # type: float

    def isAutoBlink(self):
        """
        :return: bool
        """
        return self.__m_autoBlink

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setAutoBlink(self, autoBlink):
        """
        :param autoBlink: bool
        :return:
        """
        self.__m_autoBlink = bool(autoBlink)  # type: bool

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(260, 140)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(60, 30)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(GooglyEyesWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(GooglyEyesWidget, self).hideEvent(event)

    def mousePressEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if e.button() == Qt.LeftButton:
            hit = any(r.contains(eventPos(e)) for r in self.__m_eyeRects)  # type: bool
            if hit:
                now = self._now()  # type: float
                self.__m_pokeCount += 1
                self.__m_squish = 1.0  # type: float
                self.__m_pokeTimes = [t for t in self.__m_pokeTimes if now - t < 2.0] + [now]  # type: list[float]
                self.makeDizzy()
                self.blink()
                if len(self.__m_pokeTimes) >= self.ANGRY_POKES and now > self.__m_angryUntil:
                    self.__m_angryUntil = now + 3.0  # type: float
                    self.gotAngry.emit()
                self.poked.emit(self.__m_pokeCount)
        super(GooglyEyesWidget, self).mousePressEvent(e)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        Integrate pupil physics, blinking and squish.
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        if not self.__m_eyeRects:
            self.__m_eyeRects = self._layout()  # type: list[QRectF]
        cursor = self.mapFromGlobal(QCursor.pos())  # type: QPoint
        dizzy = now < self.__m_dizzyUntil  # type: bool
        # Lower stiffness and damping = wobblier pupils.
        k = 260.0 - 190.0 * self.__m_wobble  # type: float
        c = 18.0 - 14.0 * self.__m_wobble  # type: float
        for i, rect in enumerate(self.__m_eyeRects):
            if i >= len(self.__m_pupils):
                break
            ps = self.__m_pupils[i]  # type: PupilState
            r = rect.width() / 2.0  # type: float
            maxR = r * 0.52  # type: float
            cx = rect.center().x()  # type: float
            cy = rect.center().y()  # type: float
            if dizzy:
                # Opposite spin directions per eye = maximum silliness.
                a = now * 14.0 * (1 if i % 2 == 0 else -1)  # type: float
                tx = cos(a) * maxR * 0.85  # type: float
                ty = sin(a) * maxR * 0.85  # type: float
                kk = k * 3.0  # type: float
            else:
                dx = cursor.x() - cx  # type: float
                dy = cursor.y() - cy  # type: float
                d = hypot(dx, dy)  # type: float
                s = min(1.0, d / (r * 4.0)) * maxR / d if d > 1e-3 else 0.0  # type: float
                tx = dx * s  # type: float
                ty = dy * s  # type: float
                kk = k  # type: float
            ax = (tx - ps.x) * kk - ps.vx * c  # type: float
            ay = (ty - ps.y) * kk - ps.vy * c + self.__m_gravity * 0.25  # type: float
            ps.vx += ax * dt
            ps.vy += ay * dt
            ps.x += ps.vx * dt
            ps.y += ps.vy * dt
            # Bounce off the eye wall like a real googly eye.
            dist = hypot(ps.x, ps.y)  # type: float
            if dist > maxR:
                nx = ps.x / dist  # type: float
                ny = ps.y / dist  # type: float
                ps.x = nx * maxR
                ps.y = ny * maxR
                vn = ps.vx * nx + ps.vy * ny  # type: float
                if vn > 0:
                    ps.vx -= 1.6 * vn * nx
                    ps.vy -= 1.6 * vn * ny
        # Blink scheduling.
        if self.__m_autoBlink and now >= self.__m_nextBlink:
            self.blink()
            self.__m_nextBlink = self._scheduleBlink(now)  # type: float
        self.__m_squish = max(0.0, self.__m_squish - dt * 3.0)  # type: float
        self.update()

    # ---------- Painting ----------
    def _blinkAmount(self, now):
        """
        :param now: qreal | float | int
        :return: (qreal | float | int) 0 = open, 1 = closed.
        """
        if self.__m_blinkStart < 0:
            return 0.0
        t = (now - self.__m_blinkStart) / (self.BLINK_MS / 1000.0)  # type: float
        if t >= 2.0:
            self.__m_blinkStart = -1.0  # type: float
            return 0.0
        return t if t < 1.0 else 2.0 - t

    def resizeEvent(self, event):
        """
        :param event: QResizeEvent
        :return:
        """
        super(GooglyEyesWidget, self).resizeEvent(event)
        self.__m_eyeRects = self._layout()  # type: list[QRectF]

    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        if not self.__m_eyeRects:
            self.__m_eyeRects = self._layout()  # type: list[QRectF]
        now = self._now()  # type: float
        blinkAmt = self._blinkAmount(now)  # type: float
        angry = now < self.__m_angryUntil  # type: bool
        p = QPainter(self)  # type: QPainter
        p.setRenderHint(QPainter.Antialiasing, True)
        squish = self.__m_squish  # type: float
        for i, rect in enumerate(self.__m_eyeRects):
            r = rect.width() / 2.0  # type: float
            c = rect.center()  # type: QPointF
            p.save()
            # Squash & stretch when poked.
            p.translate(c)
            sx = 1.0 + 0.12 * squish * sin(squish * pi * 3.0)  # type: float
            p.scale(sx, 2.0 - sx)
            if angry:
                p.translate(uniform(-1.5, 1.5), uniform(-1.5, 1.5))
            # Drop shadow.
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 45))
            p.drawEllipse(QPointF(0, r * 0.08), r * 1.02, r * 1.02)
            # Eyeball with soft shading.
            grad = QRadialGradient(QPointF(-r * 0.3, -r * 0.35), r * 1.6)  # type: QRadialGradient
            grad.setColorAt(0.0, self.__m_eyeColor)
            grad.setColorAt(0.75, self.__m_eyeColor.darker(108))
            grad.setColorAt(1.0, self.__m_eyeColor.darker(135))
            p.setBrush(QBrush(grad))
            pen = QPen(QColor(30, 30, 40, 200))  # type: QPen
            pen.setWidthF(max(1.5, r * 0.06))
            p.setPen(pen)
            p.drawEllipse(QPointF(0, 0), r, r)
            # Pupil.
            ps = self.__m_pupils[i] if i < len(self.__m_pupils) else PupilState()  # type: PupilState
            pr = r * 0.46  # type: float
            p.setPen(Qt.NoPen)
            p.setBrush(self.__m_pupilColor)
            p.drawEllipse(QPointF(ps.x, ps.y), pr, pr)
            p.setBrush(QColor(255, 255, 255, 220))
            p.drawEllipse(QPointF(ps.x - pr * 0.35, ps.y - pr * 0.38), pr * 0.26, pr * 0.26)
            p.drawEllipse(QPointF(ps.x + pr * 0.3, ps.y + pr * 0.32), pr * 0.1, pr * 0.1)
            # Eyelid (blink + angry squint).
            lid = max(blinkAmt, 0.32 if angry else 0.0)  # type: float
            if lid > 0.0:
                clip = QPainterPath()  # type: QPainterPath
                clip.addEllipse(QPointF(0, 0), r, r)
                p.setClipPath(clip)
                lidPath = QPainterPath()  # type: QPainterPath
                edge = -r + 2.0 * r * lid  # type: float
                tilt = (r * 0.35 if i % 2 == 0 else -r * 0.35) if angry and blinkAmt < 0.3 else 0.0  # type: float
                lidPath.moveTo(-r, -r - 1)
                lidPath.lineTo(r, -r - 1)
                lidPath.lineTo(r, edge - tilt)
                lidPath.quadTo(0, edge + r * 0.25, -r, edge + tilt)
                lidPath.closeSubpath()
                p.setBrush(self.__m_lidColor)
                lp = QPen(self.__m_lidColor.darker(140))  # type: QPen
                lp.setWidthF(max(1.0, r * 0.05))
                p.setPen(lp)
                p.drawPath(lidPath)
                p.setClipping(False)
                p.setPen(pen)
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(QPointF(0, 0), r, r)
            # Angry eyebrows.
            if angry:
                bp = QPen(QColor(40, 30, 30))  # type: QPen
                bp.setWidthF(max(2.0, r * 0.16))
                bp.setCapStyle(Qt.RoundCap)
                p.setPen(bp)
                d = 1 if i % 2 == 0 else -1  # type: int
                p.drawLine(QPointF(-r * 0.7 * d, -r * 1.35), QPointF(r * 0.6 * d, -r * 1.05))
            p.restore()
        # Dizzy stars orbiting above.
        if now < self.__m_dizzyUntil and self.__m_eyeRects:
            top = min(rc.top() for rc in self.__m_eyeRects)  # type: float
            cx = float(self.width()) / 2.0  # type: float
            spread = (self.__m_eyeRects[-1].right() - self.__m_eyeRects[0].left()) * 0.35  # type: float
            p.setPen(Qt.NoPen)
            for k in range(3):
                a = now * 5.0 + k * 2.0 * pi / 3.0  # type: float
                sx = cx + cos(a) * spread  # type: float
                sy = top - 6.0 + sin(a) * 6.0  # type: float
                self._drawStar(p, QPointF(sx, sy), 7.0 + 2.0 * sin(now * 9.0 + k), QColor('#FFD23F'))
        p.end()

    @staticmethod
    def _drawStar(p, c, r, color):
        """
        :param p: QPainter
        :param c: QPointF
        :param r: qreal | float | int
        :param color: QColor
        :return:
        """
        path = QPainterPath()  # type: QPainterPath
        for j in range(10):
            rr = r if j % 2 == 0 else r * 0.45  # type: float
            a = -pi / 2.0 + j * pi / 5.0  # type: float
            pt = QPointF(c.x() + cos(a) * rr, c.y() + sin(a) * rr)  # type: QPointF
            if j == 0:
                path.moveTo(pt)
            else:
                path.lineTo(pt)
        path.closeSubpath()
        p.setBrush(color)
        p.drawPath(path)

    # ---------- Properties ----------
    eyeCount = pyqtProperty(int, fget=getEyeCount, fset=setEyeCount)  # type: pyqtProperty
    eyeColor = pyqtProperty(QColor, fget=getEyeColor, fset=setEyeColor)  # type: pyqtProperty
    pupilColor = pyqtProperty(QColor, fget=getPupilColor, fset=setPupilColor)  # type: pyqtProperty
    lidColor = pyqtProperty(QColor, fget=getLidColor, fset=setLidColor)  # type: pyqtProperty
    wobble = pyqtProperty('qreal', fget=getWobble, fset=setWobble)  # type: pyqtProperty
    gravity = pyqtProperty('qreal', fget=getGravity, fset=setGravity)  # type: pyqtProperty
    blinkInterval = pyqtProperty(int, fget=getBlinkInterval, fset=setBlinkInterval)  # type: pyqtProperty
    autoBlink = pyqtProperty(bool, fget=isAutoBlink, fset=setAutoBlink)  # type: pyqtProperty
