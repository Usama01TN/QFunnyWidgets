# -*- coding: utf-8 -*-
"""
RocketBackToTop: a "back to top" button for any scroll area, shaped like a small rocket. It rises
into view once you have scrolled down, idles with a flickering flame, and when clicked it rumbles,
launches on a trail of fire and smoke while the content scrolls smoothly back to the top. Scroll down
again and it returns on a parachute. Only the rocket itself takes clicks; the rest passes through.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QRect, QRectF, QPointF, QEvent, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QRegion
from ManyQt.QtWidgets import QWidget, QAbstractScrollArea
from random import uniform
from math import sin

HIDDEN, RISING, IDLE, SINKING, LAUNCH, PARACHUTE = range(6)  # type: tuple
RUMBLE = 0.35  # type: float
FLIGHT = 0.9  # type: float


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


def easeInOut(t):
    """
    :param t: (qreal | float | int) 0..1
    :return: qreal | float | int
    """
    t = clamp(t, 0.0, 1.0)  # type: float
    return 3 * t * t - 2 * t * t * t


class Smoke(object):
    """
    A smoke puff.
    """

    def __init__(self, x=0.0, y=0.0, vx=0.0, vy=0.0, life=1.0):
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
        self.maxLife = float(life)  # type: float


class RocketBackToTop(QWidget):
    """
    Back-to-top rocket overlay for a QAbstractScrollArea (pass the scroll area as parent).
    """
    STRIP = 84  # type: int
    launched = pyqtSignal()  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param threshold: (int) Scroll position in px after which the rocket appears.
        :param color: (QColor | Qt.GlobalColor | int | str | QString) Fin and nose color.
        :param bodyColor: QColor | Qt.GlobalColor | int | str | QString
        :param label: (str | unicode | QString) Text painted on the rocket.
        :param launched: callable | None
        :param args: any
        :param kwargs: any
        """
        threshold = kwargs.pop('threshold', 300)  # type: int
        color = kwargs.pop('color', '#E63946')  # type: QColor
        bodyColor = kwargs.pop('bodyColor', '#EEF0F5')  # type: QColor
        label = kwargs.pop('label', 'TOP')  # type: str
        launched = kwargs.pop('launched', None)  # type: callable | None
        super(RocketBackToTop, self).__init__(*args, **kwargs)
        # Options.
        self.__m_threshold = max(0, int(threshold))  # type: int
        self.__m_color = QColor(color)  # type: QColor
        self.__m_bodyColor = QColor(bodyColor)  # type: QColor
        self.__m_label = label  # type: str
        if callable(launched):
            self.launched.connect(launched)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(self.tr('Back to top'))
        # State.
        self.__m_mode = HIDDEN  # type: int
        self.__m_modeAt = 0.0  # type: float
        self.__m_y = 0.0  # type: float
        self.__m_vy = 0.0  # type: float
        self.__m_startScroll = 0  # type: int
        self.__m_flown = False  # type: bool
        self.__m_hovered = False  # type: bool
        self.__m_smoke = []  # type: list[Smoke]
        self.__m_smokeAcc = 0.0  # type: float
        self.__m_last = 0.0  # type: float
        # Hook into the scroll area.
        self.__m_area = self.parentWidget() if isinstance(self.parentWidget(), QAbstractScrollArea) else None  # type: QAbstractScrollArea | None
        self.__m_viewport = self.__m_area.viewport() if self.__m_area is not None else None  # type: QWidget | None
        if self.__m_area is not None:
            # Watch the viewport, not the area: its geometry is only final once the viewport itself resizes.
            self.__m_area.viewport().installEventFilter(self)
            self.__m_area.verticalScrollBar().valueChanged.connect(self._onScroll)
        self._place()
        self.hide()
        # Timing.
        self.__m_clock = QElapsedTimer()  # type: QElapsedTimer
        self.__m_clock.start()
        self.__m_timer = QTimer(self)  # type: QTimer
        self.__m_timer.timeout.connect(self._tick)

    # ---------- Helpers ----------
    def _now(self):
        """
        :return: qreal | float | int
        """
        return self.__m_clock.elapsed() / 1000.0

    def _home(self):
        """
        :return: (qreal | float | int) Idle rocket center y.
        """
        return self.height() - 56.0

    def _place(self):
        """
        Cover a strip on the right of the viewport.
        :return: None
        """
        if self.__m_area is None:
            return
        vg = self.__m_area.viewport().geometry()  # type: QRect
        self.setGeometry(vg.right() - self.STRIP - 4, vg.top(), self.STRIP, vg.height())
        if self.__m_mode == IDLE:
            self.__m_y = self._home()  # type: float

    def _setMode(self, mode):
        """
        :param mode: int
        :return:
        """
        self.__m_mode = mode  # type: int
        self.__m_modeAt = self._now()  # type: float
        if mode != HIDDEN:
            self.show()
            self.raise_()
            if not self.__m_timer.isActive():
                self.__m_last = self._now()  # type: float
                self.__m_timer.start(16)

    def _updateMask(self):
        """
        Only the rocket (or its whole flight path while launching) receives clicks and paints.
        :return:
        """
        if self.__m_mode in (LAUNCH,) or self.__m_smoke:
            self.setMask(QRegion(self.rect()))
        else:
            self.setMask(QRegion(QRect(0, int(self.__m_y - 70), self.STRIP, 130)))

    @pyqtSlot(int)
    def _onScroll(self, value):
        """
        :param value: int
        :return:
        """
        if self.__m_mode == LAUNCH:
            return
        far = value > self.__m_threshold  # type: bool
        if far and self.__m_mode in (HIDDEN, SINKING):
            if self.__m_flown:
                self.__m_y = -60.0  # type: float
                self.__m_vy = 0.0  # type: float
                self._setMode(PARACHUTE)
            else:
                if self.__m_mode == HIDDEN:
                    self.__m_y = self.height() + 60.0  # type: float
                self._setMode(RISING)
        elif not far and self.__m_mode in (RISING, IDLE, PARACHUTE):
            self._setMode(SINKING)

    # ---------- Public API ----------
    @pyqtSlot()
    def launch(self):
        """
        Blast off and scroll back to the top.
        :return:
        """
        if self.__m_mode in (IDLE, RISING, PARACHUTE) and self.__m_area is not None:
            self.__m_startScroll = self.__m_area.verticalScrollBar().value()  # type: int
            self.__m_y = self._home()  # type: float
            self._setMode(LAUNCH)
            self.launched.emit()

    def getThreshold(self):
        """
        :return: int
        """
        return self.__m_threshold

    @pyqtSlot(int)
    def setThreshold(self, threshold):
        """
        :param threshold: (int) px
        :return:
        """
        self.__m_threshold = max(0, int(threshold))  # type: int
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
        self.__m_color = color  # type: QColor
        self.update()

    def getBodyColor(self):
        """
        :return: QColor
        """
        return self.__m_bodyColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setBodyColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        self.__m_bodyColor = color  # type: QColor
        self.update()

    def getLabel(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_label

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setLabel(self, label):
        """
        :param label: str | unicode | QString
        :return:
        """
        self.__m_label = label  # type: str
        self.update()

    # ---------- Qt overrides ----------
    def eventFilter(self, obj, event):
        """
        :param obj: QObject
        :param event: QEvent
        :return: bool
        """
        if obj is self.__m_viewport and event.type() == QEvent.Resize:
            self._place()
        return super(RocketBackToTop, self).eventFilter(obj, event)

    def enterEvent(self, e):
        """
        :param e: QEvent
        :return:
        """
        self.__m_hovered = True  # type: bool
        super(RocketBackToTop, self).enterEvent(e)

    def leaveEvent(self, e):
        """
        :param e: QEvent
        :return:
        """
        self.__m_hovered = False  # type: bool
        super(RocketBackToTop, self).leaveEvent(e)

    def mouseReleaseEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if e.button() == Qt.LeftButton and abs(eventPos(e).y() - self.__m_y) < 50:
            self.launch()
        super(RocketBackToTop, self).mouseReleaseEvent(e)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        since = now - self.__m_modeAt  # type: float
        mode = self.__m_mode  # type: int
        home = self._home()  # type: float
        cx = self.STRIP / 2.0  # type: float
        if mode in (RISING, IDLE):
            self.__m_vy += ((home - self.__m_y) * 120.0 - self.__m_vy * 13.0) * dt
            self.__m_y += self.__m_vy * dt
            if mode == RISING and abs(home - self.__m_y) < 1.0:
                self._setMode(IDLE)
        elif mode == SINKING:
            self.__m_vy += 900.0 * dt
            self.__m_y += self.__m_vy * dt
            if self.__m_y > self.height() + 70:
                self.__m_vy = 0.0  # type: float
                self._setMode(HIDDEN)
        elif mode == PARACHUTE:
            self.__m_y = min(home, self.__m_y + 70.0 * dt)  # type: float
            if self.__m_y >= home:
                self.__m_flown = False  # type: bool
                self._setMode(IDLE)
        elif mode == LAUNCH:
            if since > RUMBLE:
                t = (since - RUMBLE) / FLIGHT  # type: float
                self.__m_y = home - (home + 120.0) * t * t  # type: float
                if self.__m_area is not None:
                    self.__m_area.verticalScrollBar().setValue(int(self.__m_startScroll * (1.0 - easeInOut(t))))
                self.__m_smokeAcc += dt * 50.0
                if t >= 1.0:
                    if self.__m_area is not None:
                        self.__m_area.verticalScrollBar().setValue(0)
                    self.__m_flown = True  # type: bool
                    self._setMode(HIDDEN)
            else:
                self.__m_smokeAcc += dt * 25.0
            while self.__m_smokeAcc > 1.0:
                self.__m_smokeAcc -= 1.0
                self.__m_smoke.append(Smoke(cx + uniform(-6, 6), self.__m_y + 30.0, uniform(-25, 25),
                                            uniform(10, 40), uniform(0.6, 1.1)))
        alive = []  # type: list[Smoke]
        for s in self.__m_smoke:
            s.x += s.vx * dt
            s.y += s.vy * dt
            s.vx *= 0.97
            s.life -= dt
            if s.life > 0:
                alive.append(s)
        self.__m_smoke = alive  # type: list[Smoke]
        if self.__m_mode == HIDDEN and not self.__m_smoke:
            self.__m_timer.stop()
            self.clearMask()
            self.hide()
            return
        self._updateMask()
        self.update()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        now = self._now()  # type: float
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        # Smoke.
        p.setPen(Qt.NoPen)
        for s in self.__m_smoke:
            a = clamp(s.life / s.maxLife, 0.0, 1.0)  # type: float
            sc = QColor(210, 214, 222)  # type: QColor
            sc.setAlpha(int(170 * a))
            p.setBrush(sc)
            r = 5.0 + 14.0 * (1.0 - a)  # type: float
            p.drawEllipse(QPointF(s.x, s.y), r, r)
        if self.__m_mode != HIDDEN:
            cx = self.STRIP / 2.0  # type: float
            y = self.__m_y  # type: float
            mode = self.__m_mode  # type: int
            since = now - self.__m_modeAt  # type: float
            if mode == LAUNCH and since < RUMBLE:
                cx += uniform(-2.0, 2.0)
            elif mode == IDLE:
                y += sin(now * 2.5) * 2.5 - (3.0 if self.__m_hovered else 0.0)
            if mode == PARACHUTE:
                self._drawParachute(p, QPointF(cx, y), now)
            self._drawRocket(p, QPointF(cx, y), mode, since, now)
        p.end()

    def _drawRocket(self, p, c, mode, since, now):
        """
        :param p: QPainter
        :param c: (QPointF) rocket center
        :param mode: int
        :param since: qreal | float | int
        :param now: qreal | float | int
        :return:
        """
        accent = self.__m_color  # type: QColor
        body = self.__m_bodyColor  # type: QColor
        # Flame.
        if mode == LAUNCH:
            length = 18.0 + (40.0 if since > RUMBLE else since / RUMBLE * 18.0)  # type: float
        elif mode == PARACHUTE:
            length = 0.0  # type: float
        else:
            length = 8.0 + 4.0 * abs(sin(now * 17.0)) + (6.0 if self.__m_hovered else 0.0)  # type: float
        if length > 0:
            for col, wf, lf in ((QColor('#FF9F1C'), 1.0, 1.0), (QColor('#FFD23F'), 0.6, 0.65)):
                fl = QPainterPath()  # type: QPainterPath
                top = c.y() + 22.0  # type: float
                ln = length * lf * (0.9 + 0.2 * abs(sin(now * 23.0)))  # type: float
                fl.moveTo(c.x() - 8.0 * wf, top)
                fl.quadTo(c.x() - 6.0 * wf, top + ln * 0.6, c.x(), top + ln)
                fl.quadTo(c.x() + 6.0 * wf, top + ln * 0.6, c.x() + 8.0 * wf, top)
                fl.closeSubpath()
                p.setPen(Qt.NoPen)
                p.fillPath(fl, col)
        # Fins.
        p.setPen(QPen(accent.darker(140), 1.2))
        p.setBrush(accent)
        for d in (-1.0, 1.0):
            fin = QPainterPath()  # type: QPainterPath
            fin.moveTo(c.x() + d * 12.0, c.y() + 2.0)
            fin.lineTo(c.x() + d * 22.0, c.y() + 22.0)
            fin.lineTo(c.x() + d * 12.0, c.y() + 18.0)
            fin.closeSubpath()
            p.drawPath(fin)
        # Body + nose cone.
        hull = QPainterPath()  # type: QPainterPath
        hull.moveTo(c.x(), c.y() - 38.0)
        hull.cubicTo(c.x() + 14.0, c.y() - 26.0, c.x() + 14.0, c.y() - 8.0, c.x() + 12.0, c.y() + 20.0)
        hull.lineTo(c.x() - 12.0, c.y() + 20.0)
        hull.cubicTo(c.x() - 14.0, c.y() - 8.0, c.x() - 14.0, c.y() - 26.0, c.x(), c.y() - 38.0)
        p.setPen(QPen(body.darker(140), 1.2))
        p.setBrush(body)
        p.drawPath(hull)
        p.save()
        p.setClipPath(hull)
        p.fillRect(QRectF(c.x() - 16, c.y() - 40, 32, 13), accent)
        p.restore()
        p.drawPath(hull)
        p.setPen(QPen(accent.darker(140), 1.0))
        p.setBrush(accent.darker(110))
        p.drawRect(QRectF(c.x() - 7.0, c.y() + 19.0, 14.0, 4.0))
        # Porthole with a tiny pilot.
        win = QPointF(c.x(), c.y() - 12.0)  # type: QPointF
        p.setPen(QPen(QColor('#8D99AE'), 2.0))
        p.setBrush(QColor('#BDE6FF'))
        p.drawEllipse(win, 7.0, 7.0)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor('#1E1E24'))
        look = -1.5 if (self.__m_hovered or mode == LAUNCH) else 0.0  # type: float
        if mode == LAUNCH and since > RUMBLE:
            for d in (-1.0, 1.0):
                p.drawEllipse(QPointF(win.x() + d * 2.2, win.y() - 1.0), 1.4, 2.2)  # wide-eyed
            p.drawEllipse(QPointF(win.x(), win.y() + 2.8), 1.6, 1.8)               # "wheee"
        else:
            for d in (-1.0, 1.0):
                p.drawEllipse(QPointF(win.x() + d * 2.2, win.y() + look), 1.1, 1.3)
            p.setPen(QPen(QColor('#1E1E24'), 0.9, Qt.SolidLine, Qt.RoundCap))
            p.setBrush(Qt.NoBrush)
            p.drawArc(QRectF(win.x() - 2.0, win.y() + 0.5, 4.0, 2.6), 200 * 16, 140 * 16)
        # Label.
        f = QFont(self.font())  # type: QFont
        f.setBold(True)
        f.setPixelSize(8)
        p.setFont(f)
        p.setPen(accent.darker(120))
        p.drawText(QRectF(c.x() - 12.0, c.y() + 2.0, 24.0, 12.0), Qt.AlignCenter, self.__m_label)

    def _drawParachute(self, p, c, now):
        """
        :param p: QPainter
        :param c: (QPointF) rocket center
        :param now: qreal | float | int
        :return:
        """
        sway = sin(now * 2.0) * 3.0  # type: float
        top = QPointF(c.x() + sway, c.y() - 82.0)  # type: QPointF
        canopy = QPainterPath()  # type: QPainterPath
        canopy.moveTo(top.x() - 30.0, top.y() + 18.0)
        canopy.cubicTo(top.x() - 30.0, top.y() - 12.0, top.x() + 30.0, top.y() - 12.0, top.x() + 30.0, top.y() + 18.0)
        for k in range(4):
            x0 = top.x() + 30.0 - k * 15.0  # type: float
            canopy.quadTo(x0 - 7.5, top.y() + 12.0, x0 - 15.0, top.y() + 18.0)
        p.setPen(QPen(QColor('#9AA0AD'), 1.0))
        p.setBrush(self.__m_color.lighter(130))
        p.drawPath(canopy)
        p.setPen(QPen(QColor('#9AA0AD'), 0.9))
        for x in (-30.0, -10.0, 10.0, 30.0):
            p.drawLine(QPointF(top.x() + x, top.y() + 18.0), QPointF(c.x() + x * 0.3, c.y() - 34.0))

    # ---------- Properties ----------
    threshold = pyqtProperty(int, fget=getThreshold, fset=setThreshold)  # type: pyqtProperty
    color = pyqtProperty(QColor, fget=getColor, fset=setColor)  # type: pyqtProperty
    bodyColor = pyqtProperty(QColor, fget=getBodyColor, fset=setBodyColor)  # type: pyqtProperty
    label = pyqtProperty('QString', fget=getLabel, fset=setLabel)  # type: pyqtProperty
