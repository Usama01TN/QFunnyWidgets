# -*- coding: utf-8 -*-
"""
JellySwitchWidget: a toggle switch whose knob is a jelly blob with a face. It sleeps (with floating
"z") when off, wakes up happy when on, squashes when pressed and wobbles like jelly when it slides.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QRadialGradient
from ManyQt.QtWidgets import QWidget
from math import sin, pi


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


def lerpColor(a, b, t):
    """
    :param a: QColor
    :param b: QColor
    :param t: qreal | float | int
    :return: QColor
    """
    t = clamp(t, 0.0, 1.0)  # type: float
    return QColor(int(lerp(a.red(), b.red(), t)), int(lerp(a.green(), b.green(), t)),
                  int(lerp(a.blue(), b.blue(), t)), int(lerp(a.alpha(), b.alpha(), t)))


class JellySwitchWidget(QWidget):
    """
    A wobbly jelly toggle switch with a face.
    """
    toggled = pyqtSignal(bool)  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param checked: bool
        :param onColor: QColor | Qt.GlobalColor | int | str | QString
        :param offColor: QColor | Qt.GlobalColor | int | str | QString
        :param knobColor: QColor | Qt.GlobalColor | int | str | QString
        :param wobbliness: (qreal | float | int) 0 = firm, 1 = very jiggly.
        :param showFace: bool
        :param toggled: callable | None
        :param args: any
        :param kwargs: any
        """
        checked = kwargs.pop('checked', False)  # type: bool
        onColor = kwargs.pop('onColor', '#34C759')  # type: QColor
        offColor = kwargs.pop('offColor', '#B8BCC8')  # type: QColor
        knobColor = kwargs.pop('knobColor', '#FFFFFF')  # type: QColor
        wobbliness = kwargs.pop('wobbliness', 0.7)  # type: float
        showFace = kwargs.pop('showFace', True)  # type: bool
        toggled = kwargs.pop('toggled', None)  # type: callable | None
        super(JellySwitchWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_checked = bool(checked)  # type: bool
        self.__m_onColor = QColor(onColor)  # type: QColor
        self.__m_offColor = QColor(offColor)  # type: QColor
        self.__m_knobColor = QColor(knobColor)  # type: QColor
        self.__m_wobbliness = float(clamp(float(wobbliness), 0.0, 1.0))  # type: float
        self.__m_showFace = bool(showFace)  # type: bool
        if callable(toggled):
            self.toggled.connect(toggled)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        # State.
        self.__m_pos = 1.0 if self.__m_checked else 0.0  # type: float  # knob position 0..1
        self.__m_vel = 0.0  # type: float
        self.__m_squash = 0.0  # type: float  # jelly deformation (signed)
        self.__m_squashVel = 0.0  # type: float
        self.__m_press = 0.0  # type: float
        self.__m_pressed = False  # type: bool
        self.__m_hover = 0.0  # type: float
        self.__m_hovered = False  # type: bool
        self.__m_last = 0.0  # type: float
        self.__m_toggleTime = -10.0  # type: float
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

    def _trackRect(self):
        """
        :return: QRectF
        """
        w = float(self.width())  # type: float
        h = float(self.height())  # type: float
        th = min(h * 0.8, w / 2.0) - 4.0  # type: float
        tw = th * 2.0  # type: float
        return QRectF((w - tw) / 2.0, (h - th) / 2.0, tw, th)

    # ---------- Public API ----------
    @pyqtSlot()
    def toggle(self):
        """
        :return:
        """
        self.setChecked(not self.__m_checked)

    def isChecked(self):
        """
        :return: bool
        """
        return self.__m_checked

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setChecked(self, checked):
        """
        :param checked: bool
        :return:
        """
        checked = bool(checked)  # type: bool
        if checked != self.__m_checked:
            self.__m_checked = checked  # type: bool
            self.__m_toggleTime = self._now()  # type: float
            self.__m_squashVel += 10.0 if checked else -10.0
            if not self.__m_timer.isActive():
                self.__m_timer.start(16)
            self.toggled.emit(checked)
            self.update()

    def getOnColor(self):
        """
        :return: QColor
        """
        return self.__m_onColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setOnColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        if self.__m_onColor != color:
            self.__m_onColor = color  # type: QColor
            self.update()

    def getOffColor(self):
        """
        :return: QColor
        """
        return self.__m_offColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setOffColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        if self.__m_offColor != color:
            self.__m_offColor = color  # type: QColor
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

    def getWobbliness(self):
        """
        :return: qreal | float | int
        """
        return self.__m_wobbliness

    @pyqtSlot('qreal')
    @pyqtSlot(float)
    @pyqtSlot(int)
    def setWobbliness(self, wobbliness):
        """
        :param wobbliness: (qreal | float | int) 0..1
        :return:
        """
        self.__m_wobbliness = float(clamp(float(wobbliness), 0.0, 1.0))  # type: float

    def isShowFace(self):
        """
        :return: bool
        """
        return self.__m_showFace

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setShowFace(self, showFace):
        """
        :param showFace: bool
        :return:
        """
        self.__m_showFace = bool(showFace)  # type: bool
        self.update()

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(130, 70)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(50, 28)

    def enterEvent(self, e):
        """
        :param e: QEvent
        :return:
        """
        self.__m_hovered = True  # type: bool
        super(JellySwitchWidget, self).enterEvent(e)

    def leaveEvent(self, e):
        """
        :param e: QEvent
        :return:
        """
        self.__m_hovered = False  # type: bool
        super(JellySwitchWidget, self).leaveEvent(e)

    def mousePressEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if e.button() == Qt.LeftButton:
            self.__m_pressed = True  # type: bool
        super(JellySwitchWidget, self).mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if self.__m_pressed and e.button() == Qt.LeftButton:
            self.__m_pressed = False  # type: bool
            if self.rect().contains(e.pos()):
                self.toggle()
        super(JellySwitchWidget, self).mouseReleaseEvent(e)

    def keyPressEvent(self, e):
        """
        :param e: QKeyEvent
        :return:
        """
        if e.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
            self.toggle()
            return
        super(JellySwitchWidget, self).keyPressEvent(e)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(JellySwitchWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(JellySwitchWidget, self).hideEvent(event)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        target = 1.0 if self.__m_checked else 0.0  # type: float
        wob = self.__m_wobbliness  # type: float
        # Knob slide spring (slight overshoot).
        k = 220.0  # type: float
        c = 22.0 - 8.0 * wob  # type: float
        self.__m_vel += ((target - self.__m_pos) * k - self.__m_vel * c) * dt
        self.__m_pos += self.__m_vel * dt
        # Jelly deformation spring, kicked by knob velocity.
        ks = 380.0 - 200.0 * wob  # type: float
        cs = 12.0 - 9.0 * wob  # type: float
        drive = self.__m_vel * 0.08  # type: float
        self.__m_squashVel += ((drive - self.__m_squash) * ks - self.__m_squashVel * cs) * dt
        self.__m_squash += self.__m_squashVel * dt
        self.__m_press += ((1.0 if self.__m_pressed else 0.0) - self.__m_press) * min(1.0, dt * 18.0)
        self.__m_hover += ((1.0 if self.__m_hovered else 0.0) - self.__m_hover) * min(1.0, dt * 10.0)
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
        track = self._trackRect()  # type: QRectF
        th = track.height()  # type: float
        t = clamp(self.__m_pos, 0.0, 1.0)  # type: float
        # Track.
        tc = lerpColor(self.__m_offColor, self.__m_onColor, t)  # type: QColor
        path = QPainterPath()  # type: QPainterPath
        path.addRoundedRect(track, th / 2.0, th / 2.0)
        p.setPen(Qt.NoPen)
        p.fillPath(path, tc)
        inner = QColor(0, 0, 0, 30)  # type: QColor
        p.setPen(QPen(inner, 1.5))
        p.drawPath(path)
        if self.hasFocus():
            fc = QColor(tc)  # type: QColor
            fc.setAlpha(110)
            fp = QPen(fc, 2.0)  # type: QPen
            p.setPen(fp)
            p.drawRoundedRect(track.adjusted(-3, -3, 3, 3), th / 2.0 + 3, th / 2.0 + 3)
        # Knob geometry.
        pad = th * 0.1  # type: float
        r = th / 2.0 - pad  # type: float
        x0 = track.left() + pad + r  # type: float
        x1 = track.right() - pad - r  # type: float
        cx = lerp(x0, x1, self.__m_pos)  # type: float
        cy = track.center().y()  # type: float
        sq = clamp(self.__m_squash, -0.45, 0.45)  # type: float
        sx = 1.0 + abs(sq) + 0.12 * self.__m_press + 0.05 * self.__m_hover  # type: float
        sy = 1.0 - abs(sq) * 0.6 - 0.18 * self.__m_press + 0.05 * self.__m_hover  # type: float
        p.save()
        p.translate(cx, cy + r * 0.18 * self.__m_press)
        # Shadow.
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 50))
        p.drawEllipse(QPointF(0, r * 0.12), r * sx, r * sy)
        # Jelly body with glossy gradient.
        kc = self.__m_knobColor  # type: QColor
        grad = QRadialGradient(QPointF(-r * 0.35, -r * 0.45), r * 1.8)  # type: QRadialGradient
        grad.setColorAt(0.0, kc.lighter(105))
        grad.setColorAt(0.6, kc)
        grad.setColorAt(1.0, kc.darker(118))
        p.setBrush(grad)
        p.drawEllipse(QPointF(0, 0), r * sx, r * sy)
        p.setBrush(QColor(255, 255, 255, 150))
        p.drawEllipse(QPointF(-r * 0.38 * sx, -r * 0.48 * sy), r * 0.22, r * 0.12)
        if self.__m_showFace:
            self._drawFace(p, r, sx, sy, t, now)
        p.restore()
        # Floating "z" when asleep.
        if t < 0.15 and self.__m_showFace:
            f = QFont(self.font())  # type: QFont
            f.setBold(True)
            for i in range(3):
                ph = (now * 0.6 + i / 3.0) % 1.0  # type: float
                f.setPointSizeF(max(5.0, th * (0.16 + 0.14 * ph)))
                p.setFont(f)
                c = QColor(self.palette().text().color())  # type: QColor
                c.setAlpha(int(200 * sin(ph * pi) * (1.0 - t / 0.15)))
                p.setPen(c)
                p.drawText(QPointF(cx + r * 0.7 + ph * r * 0.9 + sin(ph * 6.0) * 3.0,
                                   cy - r * 0.6 - ph * r * 1.4), 'z')
        p.end()

    def _drawFace(self, p, r, sx, sy, t, now):
        """
        :param p: QPainter
        :param r: (qreal | float | int) knob radius
        :param sx: qreal | float | int
        :param sy: qreal | float | int
        :param t: (qreal | float | int) 0 = off (asleep), 1 = on (awake)
        :param now: qreal | float | int
        :return:
        """
        ink = QColor('#2B2B33')  # type: QColor
        look = clamp(self.__m_vel * 0.06, -0.25, 0.25) * r  # type: float  # eyes lead the motion
        ex = r * 0.34 * sx  # type: float
        ey = -r * 0.1 * sy  # type: float
        pen = QPen(ink, max(1.2, r * 0.09), Qt.SolidLine, Qt.RoundCap)  # type: QPen
        excited = clamp(1.0 - (now - self.__m_toggleTime) / 0.8, 0.0, 1.0) * t  # type: float
        for d in (-1.0, 1.0):
            x = d * ex + look  # type: float
            if t < 0.5:
                # Sleepy closed eyes: little arcs.
                p.setPen(pen)
                p.setBrush(Qt.NoBrush)
                p.drawArc(QRectF(x - r * 0.15, ey - r * 0.1, r * 0.3, r * 0.2), 180 * 16, 180 * 16)
            else:
                open_ = clamp((t - 0.5) * 2.0, 0.0, 1.0)  # type: float
                er = r * (0.12 + 0.05 * excited)  # type: float
                p.setPen(Qt.NoPen)
                p.setBrush(ink)
                p.drawEllipse(QPointF(x, ey), er, er * open_)
                p.setBrush(QColor('#FFFFFF'))
                p.drawEllipse(QPointF(x - er * 0.35, ey - er * 0.35 * open_), er * 0.35, er * 0.35 * open_)
        # Blush.
        if t > 0.5:
            bc = QColor('#FF7A90')  # type: QColor
            bc.setAlpha(int(150 * (t - 0.5) * 2.0))
            p.setPen(Qt.NoPen)
            p.setBrush(bc)
            for d in (-1.0, 1.0):
                p.drawEllipse(QPointF(d * r * 0.58 * sx + look, r * 0.16), r * 0.15, r * 0.09)
        # Mouth: tiny "o" while asleep, big smile when on.
        p.setPen(pen)
        if t < 0.5:
            p.setBrush(Qt.NoBrush)
            breathe = 1.0 + 0.25 * sin(now * 3.0)  # type: float
            p.drawEllipse(QPointF(look, r * 0.3), r * 0.07 * breathe, r * 0.09 * breathe)
        else:
            mw = r * (0.42 + 0.12 * excited)  # type: float
            mouth = QPainterPath()  # type: QPainterPath
            mouth.moveTo(-mw / 2.0 + look, r * 0.18)
            mouth.quadTo(look, r * (0.5 + 0.15 * excited), mw / 2.0 + look, r * 0.18)
            p.setBrush(QColor('#E85A6B') if excited > 0.05 else Qt.NoBrush)
            p.drawPath(mouth)

    # ---------- Properties ----------
    checked = pyqtProperty(bool, fget=isChecked, fset=setChecked, notify=toggled)  # type: pyqtProperty
    onColor = pyqtProperty(QColor, fget=getOnColor, fset=setOnColor)  # type: pyqtProperty
    offColor = pyqtProperty(QColor, fget=getOffColor, fset=setOffColor)  # type: pyqtProperty
    knobColor = pyqtProperty(QColor, fget=getKnobColor, fset=setKnobColor)  # type: pyqtProperty
    wobbliness = pyqtProperty('qreal', fget=getWobbliness, fset=setWobbliness)  # type: pyqtProperty
    showFace = pyqtProperty(bool, fget=isShowFace, fset=setShowFace)  # type: pyqtProperty
