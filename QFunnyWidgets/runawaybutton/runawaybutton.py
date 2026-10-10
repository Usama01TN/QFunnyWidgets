# -*- coding: utf-8 -*-
"""
RunawayButtonWidget: an arena with a button that refuses to be clicked. It springs away from the
cursor with squash & stretch, taunts you in a speech bubble and, after enough escapes, gets tired,
sweats, and finally lets you catch it (confetti included).
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QFontMetricsF, QLinearGradient
from ManyQt.QtWidgets import QWidget
from math import sin, cos, pi, hypot, atan2, degrees
from random import uniform, choice


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


DEFAULT_TAUNTS = ['Nope!', 'Too slow!', 'Missed me!', 'Hehe', 'Not today!',
                  'Catch me if you can!', 'Almost!', 'Wheee!', 'Try harder!']  # type: list[str]
CONFETTI_COLORS = ['#FF4D6D', '#FFD23F', '#3BCEAC', '#5E60CE', '#FF9F1C', '#4CC9F0']  # type: list[str]


class Particle(object):
    """
    One confetti piece.
    """

    def __init__(self, x=0.0, y=0.0, vx=0.0, vy=0.0, rot=0.0, vrot=0.0, color=None, life=1.0):
        """
        :param x: qreal | float | int
        :param y: qreal | float | int
        :param vx: qreal | float | int
        :param vy: qreal | float | int
        :param rot: (qreal | float | int) degrees
        :param vrot: (qreal | float | int) degrees/s
        :param color: QColor | None
        :param life: (qreal | float | int) s
        """
        self.x = float(x)  # type: float
        self.y = float(y)  # type: float
        self.vx = float(vx)  # type: float
        self.vy = float(vy)  # type: float
        self.rot = float(rot)  # type: float
        self.vrot = float(vrot)  # type: float
        self.color = color if color is not None else QColor('#FFD23F')  # type: QColor
        self.life = float(life)  # type: float


class RunawayButtonWidget(QWidget):
    """
    A button that runs away from the mouse until it gets tired.
    """
    BTN_W = 150.0  # type: float
    BTN_H = 50.0  # type: float
    clicked = pyqtSignal()  # type: pyqtSignal
    escaped = pyqtSignal(int)  # type: pyqtSignal
    caught = pyqtSignal(int)  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param text: (str | unicode | QString) Label while running.
        :param tiredText: (str | unicode | QString) Label once it gives up.
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :param textColor: QColor | Qt.GlobalColor | int | str | QString
        :param dodgeRadius: (qreal | float | int) Cursor distance (px) from the button edge that triggers an escape.
        :param maxEscapes: (int) Escapes before the button gives up (0 = never).
        :param taunts: (list[str | unicode | QString]) Speech bubble lines.
        :param autoReset: (int) ms after being caught before it runs again (0 = never).
        :param clicked: callable | None
        :param escaped: callable | None
        :param caught: callable | None
        :param args: any
        :param kwargs: any
        """
        text = kwargs.pop('text', 'Click me!')  # type: str
        tiredText = kwargs.pop('tiredText', 'Fine... click')  # type: str
        color = kwargs.pop('color', '#FF4D6D')  # type: QColor
        textColor = kwargs.pop('textColor', '#FFFFFF')  # type: QColor
        dodgeRadius = kwargs.pop('dodgeRadius', 32.0)  # type: float
        maxEscapes = kwargs.pop('maxEscapes', 7)  # type: int
        taunts = kwargs.pop('taunts', DEFAULT_TAUNTS)  # type: list[str]
        autoReset = kwargs.pop('autoReset', 3000)  # type: int
        clicked = kwargs.pop('clicked', None)  # type: callable | None
        escaped = kwargs.pop('escaped', None)  # type: callable | None
        caught = kwargs.pop('caught', None)  # type: callable | None
        super(RunawayButtonWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_text = text  # type: str
        self.__m_tiredText = tiredText  # type: str
        self.__m_color = QColor(color)  # type: QColor
        self.__m_textColor = QColor(textColor)  # type: QColor
        self.__m_dodgeRadius = max(10.0, float(dodgeRadius))  # type: float
        self.__m_maxEscapes = max(0, int(maxEscapes))  # type: int
        self.__m_taunts = list(taunts) or list(DEFAULT_TAUNTS)  # type: list[str]
        self.__m_autoReset = max(0, int(autoReset))  # type: int
        for sig, cb in ((self.clicked, clicked), (self.escaped, escaped), (self.caught, caught)):
            if callable(cb):
                sig.connect(cb)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        # State.
        self.__m_pos = QPointF(-1, -1)  # type: QPointF  # button center
        self.__m_target = QPointF(-1, -1)  # type: QPointF
        self.__m_vel = QPointF(0, 0)  # type: QPointF
        self.__m_escapes = 0  # type: int
        self.__m_taunt = ''  # type: str
        self.__m_tauntUntil = 0.0  # type: float
        self.__m_caughtAt = -1.0  # type: float
        self.__m_pressed = False  # type: bool
        self.__m_hover = False  # type: bool
        self.__m_mouse = QPointF(-999, -999)  # type: QPointF
        self.__m_particles = []  # type: list[Particle]
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

    def _isTired(self):
        """
        :return: bool
        """
        return 0 < self.__m_maxEscapes <= self.__m_escapes

    def _buttonRect(self):
        """
        :return: QRectF
        """
        return QRectF(self.__m_pos.x() - self.BTN_W / 2.0, self.__m_pos.y() - self.BTN_H / 2.0,
                      self.BTN_W, self.BTN_H)

    def _ensurePos(self):
        """
        Place the button in the center the first time we know our size.
        :return:
        """
        if self.__m_pos.x() < 0:
            c = QPointF(self.width() / 2.0, self.height() / 2.0)  # type: QPointF
            self.__m_pos = QPointF(c)  # type: QPointF
            self.__m_target = QPointF(c)  # type: QPointF

    def _clampCentre(self, pt):
        """
        :param pt: QPointF
        :return: QPointF
        """
        mx = self.BTN_W / 2.0 + 6.0  # type: float
        my = self.BTN_H / 2.0 + 30.0  # type: float
        return QPointF(clamp(pt.x(), mx, max(mx, self.width() - mx)),
                       clamp(pt.y(), my, max(my, self.height() - my + 22.0)))

    def _escape(self, cursor):
        """
        Pick a new spot far from the cursor.

        :param cursor: QPointF
        :return:
        """
        best = None  # type: QPointF | None
        bestD = -1.0  # type: float
        for _ in range(14):
            cand = self._clampCentre(QPointF(uniform(0, self.width()), uniform(0, self.height())))  # type: QPointF
            d = hypot(cand.x() - cursor.x(), cand.y() - cursor.y())  # type: float
            travel = hypot(cand.x() - self.__m_pos.x(), cand.y() - self.__m_pos.y())  # type: float
            score = d - abs(travel - 160.0) * 0.4  # type: float  # prefer medium hops
            if score > bestD:
                bestD = score  # type: float
                best = cand  # type: QPointF
        self.__m_target = best  # type: QPointF
        self.__m_escapes += 1
        self.__m_taunt = choice(self.__m_taunts) if not self._isTired() else 'I give up...'  # type: str
        self.__m_tauntUntil = self._now() + 1.1  # type: float
        self.escaped.emit(self.__m_escapes)

    def _burst(self, c):
        """
        :param c: QPointF
        :return:
        """
        for _ in range(70):
            a = uniform(0, 2.0 * pi)  # type: float
            s = uniform(120, 420)  # type: float
            self.__m_particles.append(Particle(c.x(), c.y(), cos(a) * s, sin(a) * s - 220, uniform(0, 360),
                                               uniform(-720, 720), QColor(choice(CONFETTI_COLORS)),
                                               uniform(1.0, 1.8)))

    # ---------- Public API ----------
    @pyqtSlot()
    def reset(self):
        """
        Make the button cheeky again.
        :return:
        """
        self.__m_escapes = 0  # type: int
        self.__m_caughtAt = -1.0  # type: float
        self.__m_taunt = ''  # type: str
        self.update()

    def getEscapes(self):
        """
        :return: int
        """
        return self.__m_escapes

    def getText(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_text

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setText(self, text):
        """
        :param text: str | unicode | QString
        :return:
        """
        self.__m_text = text  # type: str
        self.update()

    def getTiredText(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_tiredText

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setTiredText(self, tiredText):
        """
        :param tiredText: str | unicode | QString
        :return:
        """
        self.__m_tiredText = tiredText  # type: str
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

    def getTextColor(self):
        """
        :return: QColor
        """
        return self.__m_textColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setTextColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        if self.__m_textColor != color:
            self.__m_textColor = color  # type: QColor
            self.update()

    def getDodgeRadius(self):
        """
        :return: qreal | float | int
        """
        return self.__m_dodgeRadius

    @pyqtSlot('qreal')
    @pyqtSlot(float)
    @pyqtSlot(int)
    def setDodgeRadius(self, dodgeRadius):
        """
        :param dodgeRadius: qreal | float | int
        :return:
        """
        self.__m_dodgeRadius = max(10.0, float(dodgeRadius))  # type: float

    def getMaxEscapes(self):
        """
        :return: int
        """
        return self.__m_maxEscapes

    @pyqtSlot(int)
    def setMaxEscapes(self, maxEscapes):
        """
        :param maxEscapes: int
        :return:
        """
        self.__m_maxEscapes = max(0, int(maxEscapes))  # type: int
        self.update()

    def getTaunts(self):
        """
        :return: list[str | unicode | QString]
        """
        return list(self.__m_taunts)

    @pyqtSlot(list)
    def setTaunts(self, taunts):
        """
        :param taunts: list[str]
        :return:
        """
        self.__m_taunts = list(taunts) or list(DEFAULT_TAUNTS)  # type: list[str]
        self.update()

    def getAutoReset(self):
        """
        :return: int
        """
        return self.__m_autoReset

    @pyqtSlot(int)
    def setAutoReset(self, autoReset):
        """
        :param autoReset: (int) ms
        :return:
        """
        self.__m_autoReset = max(0, int(autoReset))  # type: int

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(460, 260)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(220, 140)

    def resizeEvent(self, event):
        """
        :param event: QResizeEvent
        :return:
        """
        super(RunawayButtonWidget, self).resizeEvent(event)
        if self.__m_pos.x() >= 0:
            self.__m_pos = self._clampCentre(self.__m_pos)  # type: QPointF
            self.__m_target = self._clampCentre(self.__m_target)  # type: QPointF

    def mouseMoveEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        self._ensurePos()
        self.__m_mouse = eventPos(e)  # type: QPointF
        rect = self._buttonRect()  # type: QRectF
        self.__m_hover = rect.contains(self.__m_mouse)  # type: bool
        if self.__m_caughtAt < 0 and not self._isTired():
            # Distance from cursor to the button rectangle (0 when inside).
            dx = max(rect.left() - self.__m_mouse.x(), 0.0, self.__m_mouse.x() - rect.right())  # type: float
            dy = max(rect.top() - self.__m_mouse.y(), 0.0, self.__m_mouse.y() - rect.bottom())  # type: float
            moving = hypot(self.__m_vel.x(), self.__m_vel.y()) > 250.0  # type: bool
            if hypot(dx, dy) < self.__m_dodgeRadius and not moving:
                self._escape(self.__m_mouse)
        super(RunawayButtonWidget, self).mouseMoveEvent(e)

    def leaveEvent(self, e):
        """
        :param e: QEvent
        :return:
        """
        self.__m_hover = False  # type: bool
        self.__m_mouse = QPointF(-999, -999)  # type: QPointF
        super(RunawayButtonWidget, self).leaveEvent(e)

    def mousePressEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if e.button() == Qt.LeftButton and self._buttonRect().contains(eventPos(e)):
            self.__m_pressed = True  # type: bool
        super(RunawayButtonWidget, self).mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if self.__m_pressed and self._buttonRect().contains(eventPos(e)):
            self.clicked.emit()
            if self.__m_caughtAt < 0:
                self.__m_caughtAt = self._now()  # type: float
                self.__m_taunt = 'You got me!'  # type: str
                self.__m_tauntUntil = self._now() + 2.0  # type: float
                self._burst(self.__m_pos)
                self.caught.emit(self.__m_escapes)
        self.__m_pressed = False  # type: bool
        super(RunawayButtonWidget, self).mouseReleaseEvent(e)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(RunawayButtonWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(RunawayButtonWidget, self).hideEvent(event)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        self._ensurePos()
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        # Under-damped spring = cartoon overshoot.
        k = 160.0  # type: float
        c = 11.0  # type: float
        ax = (self.__m_target.x() - self.__m_pos.x()) * k - self.__m_vel.x() * c  # type: float
        ay = (self.__m_target.y() - self.__m_pos.y()) * k - self.__m_vel.y() * c  # type: float
        self.__m_vel = QPointF(self.__m_vel.x() + ax * dt, self.__m_vel.y() + ay * dt)  # type: QPointF
        self.__m_pos = QPointF(self.__m_pos.x() + self.__m_vel.x() * dt,
                               self.__m_pos.y() + self.__m_vel.y() * dt)  # type: QPointF
        # Confetti.
        alive = []  # type: list[Particle]
        for pt in self.__m_particles:
            pt.vy += 700.0 * dt
            pt.vx *= 0.99
            pt.x += pt.vx * dt
            pt.y += pt.vy * dt
            pt.rot += pt.vrot * dt
            pt.life -= dt
            if pt.life > 0 and pt.y < self.height() + 20:
                alive.append(pt)
        self.__m_particles = alive  # type: list[Particle]
        if self.__m_caughtAt >= 0 and self.__m_autoReset and now - self.__m_caughtAt > self.__m_autoReset / 1000.0:
            self.reset()
        self.update()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        self._ensurePos()
        now = self._now()  # type: float
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        tired = self._isTired()  # type: bool
        caught = self.__m_caughtAt >= 0  # type: bool
        vx = self.__m_vel.x()  # type: float
        vy = self.__m_vel.y()  # type: float
        speed = hypot(vx, vy)  # type: float
        # Shadow on the floor.
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 40))
        p.drawEllipse(QPointF(self.__m_pos.x(), self.__m_pos.y() + self.BTN_H * 0.62),
                      self.BTN_W * 0.42, 6.0)
        p.save()
        p.translate(self.__m_pos)
        # Squash & stretch along the velocity direction.
        stretch = clamp(speed / 1800.0, 0.0, 0.35)  # type: float
        ang = degrees(atan2(vy, vx)) if speed > 1 else 0.0  # type: float
        p.rotate(ang)
        p.scale(1.0 + stretch, 1.0 - stretch * 0.6)
        p.rotate(-ang)
        if tired and not caught:
            p.rotate(6.0 * sin(now * 2.0))  # sleepy sway
            p.translate(0, 4.0)
        bob = 0.0 if tired or caught else 2.5 * sin(now * 6.0)  # type: float
        p.translate(0, bob)
        if self.__m_pressed:
            p.scale(0.94, 0.9)
        rect = QRectF(-self.BTN_W / 2.0, -self.BTN_H / 2.0, self.BTN_W, self.BTN_H)  # type: QRectF
        base = QColor('#3BCEAC') if caught else (self.__m_color.darker(115) if tired else self.__m_color)  # type: QColor
        grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())  # type: QLinearGradient
        grad.setColorAt(0.0, base.lighter(118 if self.__m_hover else 108))
        grad.setColorAt(1.0, base.darker(112))
        path = QPainterPath()  # type: QPainterPath
        path.addRoundedRect(rect, self.BTN_H / 2.0, self.BTN_H / 2.0)
        p.fillPath(path, grad)
        p.setPen(QPen(base.darker(140), 1.5))
        p.drawPath(path)
        # Little face on the left of the pill.
        ex = rect.left() + 26.0  # type: float
        look = QPointF(clamp((self.__m_mouse.x() - self.__m_pos.x()) / 80.0, -1.5, 1.5),
                       clamp((self.__m_mouse.y() - self.__m_pos.y()) / 80.0, -1.5, 1.5))  # type: QPointF
        p.setPen(Qt.NoPen)
        for dx in (-7.0, 7.0):
            if tired and not caught:
                p.setPen(QPen(QColor('#FFFFFF'), 2.0, Qt.SolidLine, Qt.RoundCap))
                p.drawLine(QPointF(ex + dx - 3.0, -4.0), QPointF(ex + dx + 3.0, -4.0))
                p.setPen(Qt.NoPen)
            else:
                p.setBrush(QColor('#FFFFFF'))
                p.drawEllipse(QPointF(ex + dx, -4.0), 5.0, 5.0)
                p.setBrush(QColor('#1A1A1A'))
                p.drawEllipse(QPointF(ex + dx + look.x() * 1.5, -4.0 + look.y() * 1.5), 2.4, 2.4)
        mp = QPen(QColor('#FFFFFF'), 2.0, Qt.SolidLine, Qt.RoundCap)  # type: QPen
        p.setPen(mp)
        p.setBrush(Qt.NoBrush)
        if caught:
            p.drawArc(QRectF(ex - 6.0, 0.0, 12.0, 9.0), 180 * 16, 180 * 16)
        elif tired:
            p.drawEllipse(QPointF(ex, 8.0), 3.0, 3.5)
        else:
            p.drawArc(QRectF(ex - 6.0, 1.0, 12.0, 8.0), 200 * 16, 140 * 16)
        # Label.
        f = QFont(self.font())  # type: QFont
        f.setBold(True)
        f.setPointSizeF(10.5)
        p.setFont(f)
        p.setPen(self.__m_textColor)
        label = 'Yay!' if caught else (self.__m_tiredText if tired else self.__m_text)  # type: str
        p.drawText(QRectF(rect.left() + 42.0, rect.top(), rect.width() - 50.0, rect.height()),
                   Qt.AlignVCenter | Qt.AlignHCenter, label)
        p.restore()
        # Sweat drops when tired.
        if tired and not caught:
            for i in range(2):
                t = (now * 0.9 + i * 0.5) % 1.0  # type: float
                sx = self.__m_pos.x() + self.BTN_W * 0.5 - 4.0 + i * 9.0  # type: float
                sy = self.__m_pos.y() - self.BTN_H * 0.4 + t * 26.0  # type: float
                c = QColor('#7FD6FF')  # type: QColor
                c.setAlpha(int(255 * (1.0 - t)))
                drop = QPainterPath()  # type: QPainterPath
                drop.moveTo(sx, sy - 6.0)
                drop.quadTo(sx + 4.0, sy, sx, sy + 3.5)
                drop.quadTo(sx - 4.0, sy, sx, sy - 6.0)
                p.fillPath(drop, c)
        # Speech bubble.
        if now < self.__m_tauntUntil and self.__m_taunt:
            self._drawBubble(p, self.__m_taunt, now)
        # Confetti.
        p.setPen(Qt.NoPen)
        for pt in self.__m_particles:
            c = QColor(pt.color)  # type: QColor
            c.setAlpha(int(255 * clamp(pt.life, 0.0, 1.0)))
            p.save()
            p.translate(pt.x, pt.y)
            p.rotate(pt.rot)
            p.setBrush(c)
            p.drawRect(QRectF(-4, -2, 8, 4))
            p.restore()
        # Escape counter.
        if self.__m_maxEscapes:
            f2 = QFont(self.font())  # type: QFont
            f2.setPointSizeF(8.5)
            p.setFont(f2)
            p.setPen(self.palette().text().color())
            p.drawText(QRectF(8, self.height() - 22, self.width() - 16, 18), Qt.AlignRight | Qt.AlignVCenter,
                       'Escapes: {} / {}'.format(min(self.__m_escapes, self.__m_maxEscapes), self.__m_maxEscapes))
        p.end()

    def _drawBubble(self, p, text, now):
        """
        :param p: QPainter
        :param text: str | unicode | QString
        :param now: qreal | float | int
        :return:
        """
        f = QFont(self.font())  # type: QFont
        f.setBold(True)
        f.setPointSizeF(9.5)
        fm = QFontMetricsF(f)  # type: QFontMetricsF
        tw = fm.horizontalAdvance(text) if hasattr(fm, 'horizontalAdvance') else fm.width(text)  # type: float
        bw = tw + 22.0  # type: float
        bh = fm.height() + 12.0  # type: float
        left = self.__m_tauntUntil - now  # type: float
        pop = clamp((1.1 - left) * 8.0, 0.0, 1.0) if left > 0.2 else clamp(left * 5.0, 0.0, 1.0)  # type: float
        bx = clamp(self.__m_pos.x() - bw / 2.0, 4.0, self.width() - bw - 4.0)  # type: float
        by = max(2.0, self.__m_pos.y() - self.BTN_H / 2.0 - bh - 14.0)  # type: float
        p.save()
        p.setOpacity(pop)
        p.translate(bx + bw / 2.0, by + bh)
        p.scale(0.6 + 0.4 * pop, 0.6 + 0.4 * pop)
        p.translate(-(bx + bw / 2.0), -(by + bh))
        path = QPainterPath()  # type: QPainterPath
        path.addRoundedRect(QRectF(bx, by, bw, bh), 10, 10)
        tail = QPainterPath()  # type: QPainterPath
        tx = clamp(self.__m_pos.x(), bx + 14.0, bx + bw - 14.0)  # type: float
        tail.moveTo(tx - 7.0, by + bh - 1.0)
        tail.lineTo(tx, by + bh + 9.0)
        tail.lineTo(tx + 7.0, by + bh - 1.0)
        tail.closeSubpath()
        path = path.united(tail)  # type: QPainterPath
        p.setPen(QPen(QColor(20, 20, 30, 70), 1.2))
        p.setBrush(QColor('#FFFFFF'))
        p.drawPath(path)
        p.setFont(f)
        p.setPen(QColor('#22222A'))
        p.drawText(QRectF(bx, by, bw, bh), Qt.AlignCenter, text)
        p.restore()

    # ---------- Properties ----------
    text = pyqtProperty('QString', fget=getText, fset=setText)  # type: pyqtProperty
    tiredText = pyqtProperty('QString', fget=getTiredText, fset=setTiredText)  # type: pyqtProperty
    color = pyqtProperty(QColor, fget=getColor, fset=setColor)  # type: pyqtProperty
    textColor = pyqtProperty(QColor, fget=getTextColor, fset=setTextColor)  # type: pyqtProperty
    taunts = pyqtProperty('QStringList', fget=getTaunts, fset=setTaunts)  # type: pyqtProperty
    dodgeRadius = pyqtProperty('qreal', fget=getDodgeRadius, fset=setDodgeRadius)  # type: pyqtProperty
    maxEscapes = pyqtProperty(int, fget=getMaxEscapes, fset=setMaxEscapes)  # type: pyqtProperty
    autoReset = pyqtProperty(int, fget=getAutoReset, fset=setAutoReset)  # type: pyqtProperty
