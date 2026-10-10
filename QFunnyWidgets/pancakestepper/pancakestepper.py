# -*- coding: utf-8 -*-
"""
PancakeStepperWidget: a quantity input (spin box) served as a stack of pancakes. "+" drops a fresh
pancake onto the stack (squash on landing, butter and syrup on top), "-" flips the top one off the
plate. Near the maximum the stack starts to wobble; asking for more makes it nearly topple.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QLinearGradient
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


class Drop(object):
    """
    Landing state of one stacked pancake.
    """

    def __init__(self, offset=0.0, vel=0.0):
        """
        :param offset: (qreal | float | int) px above its resting place
        :param vel: qreal | float | int
        """
        self.offset = float(offset)  # type: float
        self.vel = float(vel)  # type: float
        self.squash = 0.0  # type: float


class Flip(object):
    """
    A pancake flipped off the stack.
    """

    def __init__(self, x=0.0, y=0.0, vx=0.0, vy=0.0, vrot=0.0):
        """
        :param x: qreal | float | int
        :param y: qreal | float | int
        :param vx: qreal | float | int
        :param vy: qreal | float | int
        :param vrot: (qreal | float | int) degrees/s
        """
        self.x = float(x)  # type: float
        self.y = float(y)  # type: float
        self.vx = float(vx)  # type: float
        self.vy = float(vy)  # type: float
        self.rot = 0.0  # type: float
        self.vrot = float(vrot)  # type: float
        self.life = 1.2  # type: float


class PancakeStepperWidget(QWidget):
    """
    Quantity stepper, but make it breakfast.
    """
    valueChanged = pyqtSignal(int)  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param value: int
        :param minimum: int
        :param maximum: (int) Stack height limit (1..20).
        :param unit: (str | unicode | QString) Singular unit name for the label.
        :param accentColor: (QColor | Qt.GlobalColor | int | str | QString) Button color.
        :param valueChanged: callable | None
        :param args: any
        :param kwargs: any
        """
        value = kwargs.pop('value', 2)  # type: int
        minimum = kwargs.pop('minimum', 0)  # type: int
        maximum = kwargs.pop('maximum', 8)  # type: int
        unit = kwargs.pop('unit', 'pancake')  # type: str
        accentColor = kwargs.pop('accentColor', '#C47F3A')  # type: QColor
        valueChanged = kwargs.pop('valueChanged', None)  # type: callable | None
        super(PancakeStepperWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_minimum = max(0, int(minimum))  # type: int
        self.__m_maximum = int(clamp(int(maximum), self.__m_minimum + 1, 20))  # type: int
        self.__m_value = int(clamp(int(value), self.__m_minimum, self.__m_maximum))  # type: int
        self.__m_unit = unit  # type: str
        self.__m_accentColor = QColor(accentColor)  # type: QColor
        if callable(valueChanged):
            self.valueChanged.connect(valueChanged)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        # State.
        self.__m_drops = [Drop() for _ in range(self.__m_value)]  # type: list[Drop]
        self.__m_flips = []  # type: list[Flip]
        self.__m_sway = 0.0  # type: float
        self.__m_swayVel = 0.0  # type: float
        self.__m_refuseAt = -10.0  # type: float
        self.__m_minusRect = QRectF()  # type: QRectF
        self.__m_plusRect = QRectF()  # type: QRectF
        self.__m_hoverBtn = 0  # type: int
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
        :return: (tuple) plate center QPointF, pancake width float, pancake thickness float
        """
        w = float(self.width())  # type: float
        h = float(self.height())  # type: float
        plate = QPointF(w / 2.0, h - 58.0)  # type: QPointF
        pw = clamp(min(w * 0.55, 170.0), 60.0, 170.0)  # type: float
        th = clamp((plate.y() - 40.0) / (self.__m_maximum + 1.5), 5.0, 16.0)  # type: float
        return plate, pw, th

    def _refuse(self):
        """
        :return:
        """
        self.__m_refuseAt = self._now()  # type: float
        self.__m_swayVel += 45.0 if uniform(0, 1) < 0.5 else -45.0

    # ---------- Public API ----------
    @pyqtSlot()
    def increment(self):
        """
        :return:
        """
        if self.__m_value >= self.__m_maximum:
            self._refuse()
        else:
            self.setValue(self.__m_value + 1)

    @pyqtSlot()
    def decrement(self):
        """
        :return:
        """
        self.setValue(self.__m_value - 1)

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
        if value == self.__m_value:
            return
        plate, pw, th = self._geometry()
        while len(self.__m_drops) < value:
            self.__m_drops.append(Drop(offset=plate.y() * 0.6 + uniform(0, 20)))
        while len(self.__m_drops) > value:
            self.__m_drops.pop()
            top = plate.y() - (len(self.__m_drops) + 0.5) * th  # type: float
            self.__m_flips.append(Flip(plate.x(), top, uniform(-120, 120), -uniform(380, 480), uniform(-720, 720)))
        self.__m_value = value  # type: int
        self.valueChanged.emit(value)
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
        self.__m_minimum = int(clamp(int(minimum), 0, self.__m_maximum - 1))  # type: int
        if self.__m_value < self.__m_minimum:
            self.setValue(self.__m_minimum)

    def getMaximum(self):
        """
        :return: int
        """
        return self.__m_maximum

    @pyqtSlot(int)
    def setMaximum(self, maximum):
        """
        :param maximum: (int) 1..20
        :return:
        """
        self.__m_maximum = int(clamp(int(maximum), self.__m_minimum + 1, 20))  # type: int
        if self.__m_value > self.__m_maximum:
            self.setValue(self.__m_maximum)
        self.update()

    def getUnit(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_unit

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setUnit(self, unit):
        """
        :param unit: str | unicode | QString
        :return:
        """
        self.__m_unit = unit  # type: str
        self.update()

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

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(260, 280)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(160, 180)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(PancakeStepperWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(PancakeStepperWidget, self).hideEvent(event)

    def mouseMoveEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        hover = -1 if self.__m_minusRect.contains(eventPos(e)) else 1 if self.__m_plusRect.contains(eventPos(e)) else 0  # type: int
        if hover != self.__m_hoverBtn:
            self.__m_hoverBtn = hover  # type: int
            self.setCursor(Qt.PointingHandCursor if hover else Qt.ArrowCursor)
        super(PancakeStepperWidget, self).mouseMoveEvent(e)

    def leaveEvent(self, e):
        """
        :param e: QEvent
        :return:
        """
        self.__m_hoverBtn = 0  # type: int
        super(PancakeStepperWidget, self).leaveEvent(e)

    def mouseReleaseEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if e.button() == Qt.LeftButton:
            if self.__m_minusRect.contains(eventPos(e)):
                self.decrement()
            elif self.__m_plusRect.contains(eventPos(e)):
                self.increment()
        super(PancakeStepperWidget, self).mouseReleaseEvent(e)

    def wheelEvent(self, e):
        """
        :param e: QWheelEvent
        :return:
        """
        if e.angleDelta().y() > 0:
            self.increment()
        else:
            self.decrement()
        e.accept()

    def keyPressEvent(self, e):
        """
        :param e: QKeyEvent
        :return:
        """
        if e.key() in (Qt.Key_Up, Qt.Key_Right, Qt.Key_Plus):
            self.increment()
        elif e.key() in (Qt.Key_Down, Qt.Key_Left, Qt.Key_Minus):
            self.decrement()
        else:
            super(PancakeStepperWidget, self).keyPressEvent(e)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        for d in self.__m_drops:
            if d.offset > 0 or d.vel != 0:
                d.vel -= 2600.0 * dt
                d.offset += d.vel * dt
                if d.offset <= 0:
                    d.offset = 0.0
                    d.squash = clamp(-d.vel / 1400.0, 0.0, 0.5)
                    d.vel = -d.vel * 0.25 if abs(d.vel) > 160 else 0.0
                    if d.vel:
                        self.__m_swayVel += uniform(-6, 6)
            d.squash = max(0.0, d.squash - dt * 3.0)
        # A tall stack sways on its own; refusal adds a big shove.
        tall = clamp((self.__m_value - self.__m_maximum * 0.6) / (self.__m_maximum * 0.4), 0.0, 1.0)  # type: float
        self.__m_swayVel += sin(now * 2.3) * 20.0 * tall * dt
        self.__m_swayVel += (-self.__m_sway * 30.0 - self.__m_swayVel * 2.5) * dt
        self.__m_sway = clamp(self.__m_sway + self.__m_swayVel * dt, -14.0, 14.0)  # type: float
        alive = []  # type: list[Flip]
        for f in self.__m_flips:
            f.vy += 1500.0 * dt
            f.x += f.vx * dt
            f.y += f.vy * dt
            f.rot += f.vrot * dt
            f.life -= dt
            if f.life > 0 and f.y < self.height() + 40:
                alive.append(f)
        self.__m_flips = alive  # type: list[Flip]
        self.update()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        now = self._now()  # type: float
        plate, pw, th = self._geometry()
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        tc = QColor(self.palette().text().color())  # type: QColor
        # Plate.
        p.setPen(QPen(QColor('#C9CCD6'), 1.2))
        p.setBrush(QColor('#F4F5F8'))
        p.drawEllipse(QPointF(plate.x(), plate.y() + th * 0.4), pw * 0.68, th * 1.3)
        p.setBrush(QColor('#E6E8EE'))
        p.drawEllipse(QPointF(plate.x(), plate.y() + th * 0.4), pw * 0.48, th * 0.8)
        # Stack (rotates around the plate as it sways).
        p.save()
        p.translate(plate)
        p.rotate(self.__m_sway)
        n = len(self.__m_drops)  # type: int
        for i, d in enumerate(self.__m_drops):
            y = -(i + 0.5) * th - d.offset  # type: float
            self._drawPancake(p, QPointF(uniform(-0.3, 0.3) if abs(self.__m_swayVel) > 30 else 0.0, y), pw, th, d.squash,
                              top=(i == n - 1), now=now)
        p.restore()
        # Flipped pancakes.
        for f in self.__m_flips:
            p.save()
            p.translate(f.x, f.y)
            p.rotate(f.rot)
            p.setOpacity(clamp(f.life / 0.4, 0.0, 1.0))
            self._drawPancake(p, QPointF(0, 0), pw, th, 0.0, top=False, now=now)
            p.restore()
        # Controls.
        h = float(self.height())  # type: float
        br = 17.0  # type: float
        cy = h - 22.0  # type: float
        self.__m_minusRect = QRectF(plate.x() - pw * 0.7 - br, cy - br, br * 2, br * 2)  # type: QRectF
        self.__m_plusRect = QRectF(plate.x() + pw * 0.7 - br, cy - br, br * 2, br * 2)  # type: QRectF
        ac = self.__m_accentColor  # type: QColor
        for rect, sign, enabled, hov in (
                (self.__m_minusRect, -1, self.__m_value > self.__m_minimum, self.__m_hoverBtn == -1),
                (self.__m_plusRect, 1, self.__m_value < self.__m_maximum, self.__m_hoverBtn == 1)):
            col = QColor(ac.lighter(115) if hov else ac)  # type: QColor
            if not enabled:
                col.setAlpha(80)
            p.setPen(Qt.NoPen)
            p.setBrush(col)
            p.drawEllipse(rect)
            p.setPen(QPen(QColor('#FFFFFF'), 2.5, Qt.SolidLine, Qt.RoundCap))
            c = rect.center()  # type: QPointF
            p.drawLine(c - QPointF(6, 0), c + QPointF(6, 0))
            if sign > 0:
                p.drawLine(c - QPointF(0, 6), c + QPointF(0, 6))
        # Label.
        f = QFont(self.font())  # type: QFont
        f.setBold(True)
        f.setPointSizeF(10.5)
        p.setFont(f)
        refusing = now - self.__m_refuseAt < 1.6  # type: bool
        v = self.__m_value  # type: int
        if refusing:
            label = self.tr("That's enough {}s.").format(self.__m_unit)  # type: str
            p.setPen(QColor('#E63946'))
        else:
            label = '{} {}{}'.format(v, self.__m_unit, '' if v == 1 else 's') if v else self.tr('No {}s :(').format(self.__m_unit)  # type: str
            p.setPen(tc)
        p.drawText(QRectF(
            self.__m_minusRect.right(), cy - 12.0, self.__m_plusRect.left() - self.__m_minusRect.right(), 24.0
        ), Qt.AlignCenter, label)
        if v >= self.__m_maximum * 0.8 and not refusing:
            sf = QFont(self.font())  # type: QFont
            sf.setItalic(True)
            sf.setPointSizeF(8.5)
            p.setFont(sf)
            wc = QColor(tc)  # type: QColor
            wc.setAlpha(150)
            p.setPen(wc)
            p.drawText(QRectF(0, 4, self.width(), 18), Qt.AlignHCenter | Qt.AlignTop, self.tr('Whoa... steady...'))
        p.end()

    def _drawPancake(self, p, c, pw, th, squash, top, now):
        """
        :param p: QPainter
        :param c: (QPointF) center
        :param pw: (qreal | float | int) width
        :param th: (qreal | float | int) thickness
        :param squash: (qreal | float | int) landing squash 0..0.5
        :param top: (bool) top pancake gets toppings and a face
        :param now: qreal | float | int
        :return:
        """
        w = pw * (1.0 + squash * 0.3)  # type: float
        t = th * (1.0 - squash)  # type: float
        rect = QRectF(c.x() - w / 2.0, c.y() - t / 2.0, w, t)  # type: QRectF
        grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())  # type: QLinearGradient
        grad.setColorAt(0.0, QColor('#F2C27B'))
        grad.setColorAt(0.5, QColor('#E0A458'))
        grad.setColorAt(1.0, QColor('#B9783A'))
        p.setPen(QPen(QColor('#9A5F2A'), 1.0))
        p.setBrush(grad)
        p.drawRoundedRect(rect, t / 2.0, t / 2.0)
        if not top:
            return
        # Syrup drips + butter + face.
        syrup = QColor(170, 90, 20, 200)  # type: QColor
        p.setPen(Qt.NoPen)
        p.setBrush(syrup)
        sp = QPainterPath()  # type: QPainterPath
        sp.addRoundedRect(QRectF(rect.left() + w * 0.12, rect.top() - 1, w * 0.76, t * 0.5), t * 0.25, t * 0.25)
        p.drawPath(sp)
        for k, fx in enumerate((0.2, 0.55, 0.78)):
            drip = t * (0.6 + 0.4 * ((now * 0.4 + k * 0.33) % 1.0))  # type: float
            p.drawRoundedRect(QRectF(rect.left() + w * fx - 2.5, rect.top(), 5.0, drip), 2.5, 2.5)
        p.setBrush(QColor('#FFE680'))
        p.setPen(QPen(QColor('#E8C547'), 1.0))
        bw = min(w * 0.2, 26.0)  # type: float
        p.drawRoundedRect(QRectF(c.x() - bw / 2.0 + w * 0.1, rect.top() - bw * 0.45, bw, bw * 0.5), 3, 3)
        # A smug little face on the side of the top pancake.
        ink = QColor('#4A2A10')  # type: QColor
        p.setPen(Qt.NoPen)
        p.setBrush(ink)
        nervous = self.__m_value >= self.__m_maximum * 0.8  # type: bool
        for d in (-1.0, 1.0):
            p.drawEllipse(QPointF(c.x() - w * 0.12 + d * t * 0.6, c.y() + t * 0.05), t * 0.13, t * (0.2 if nervous else 0.13))
        p.setPen(QPen(ink, max(1.0, t * 0.1), Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        if nervous:
            p.drawLine(QPointF(c.x() - w * 0.12 - t * 0.3, c.y() + t * 0.32), QPointF(c.x() - w * 0.12 + t * 0.3, c.y() + t * 0.28))
        else:
            p.drawArc(QRectF(c.x() - w * 0.12 - t * 0.35, c.y() - t * 0.05, t * 0.7, t * 0.45), 200 * 16, 140 * 16)

    # ---------- Properties ----------
    value = pyqtProperty(int, fget=getValue, fset=setValue, notify=valueChanged)  # type: pyqtProperty
    minimum = pyqtProperty(int, fget=getMinimum, fset=setMinimum)  # type: pyqtProperty
    maximum = pyqtProperty(int, fget=getMaximum, fset=setMaximum)  # type: pyqtProperty
    unit = pyqtProperty('QString', fget=getUnit, fset=setUnit)  # type: pyqtProperty
    accentColor = pyqtProperty(QColor, fget=getAccentColor, fset=setAccentColor)  # type: pyqtProperty
