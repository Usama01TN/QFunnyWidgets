# -*- coding: utf-8 -*-
"""
PigeonToast: toast notifications delivered by carrier pigeon. Attach it to any widget; each message
is flown in by a flapping pigeon carrying a banner on two strings, held up while the pigeon hovers
(losing a feather or two) and then flown away. Messages are queued. The overlay follows the parent's
size and never blocks the mouse.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QRectF, QPointF, QEvent, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QFontMetricsF, QLinearGradient
from ManyQt.QtWidgets import QWidget
from random import uniform
from math import sin, pi


def clamp(x, a, b):
    """
    :param x: qreal | float | int
    :param a: qreal | float | int
    :param b: qreal | float | int
    :return: qreal | float | int
    """
    return a if x < a else b if x > b else x


def easeOutBack(t):
    """
    :param t: (qreal | float | int) 0..1
    :return: qreal | float | int
    """
    c1 = 1.4  # type: float
    t -= 1.0
    return 1.0 + (c1 + 1.0) * t * t * t + c1 * t * t


def easeInCubic(t):
    """
    :param t: (qreal | float | int) 0..1
    :return: qreal | float | int
    """
    return t * t * t


class Feather(object):
    """
    A falling feather.
    """

    def __init__(self, x=0.0, y=0.0, life=2.0, phase=0.0):
        """
        :param x: qreal | float | int
        :param y: qreal | float | int
        :param life: (qreal | float | int) s
        :param phase: (qreal | float | int) sway phase
        """
        self.x = float(x)  # type: float
        self.y = float(y)  # type: float
        self.life = float(life)  # type: float
        self.maxLife = float(life)  # type: float
        self.phase = float(phase)  # type: float


class PigeonToast(QWidget):
    """
    Carrier-pigeon toast overlay.
    """
    FLY_IN = 1.1  # type: float
    FLY_OUT = 1.0  # type: float
    messageShown = pyqtSignal('QString')  # type: pyqtSignal
    messageFinished = pyqtSignal('QString')  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param duration: (int) ms each message is held up.
        :param bannerColor: QColor | Qt.GlobalColor | int | str | QString
        :param textColor: QColor | Qt.GlobalColor | int | str | QString
        :param pigeonColor: QColor | Qt.GlobalColor | int | str | QString
        :param caption: (str | unicode | QString) Small line above the message; empty hides it.
        :param margin: (int) px from the parent's top-right corner.
        :param messageShown: callable | None
        :param messageFinished: callable | None
        :param args: any
        :param kwargs: any
        """
        duration = kwargs.pop('duration', 2600)  # type: int
        bannerColor = kwargs.pop('bannerColor', '#FFFFFF')  # type: QColor
        textColor = kwargs.pop('textColor', '#22222A')  # type: QColor
        pigeonColor = kwargs.pop('pigeonColor', '#9AA5B1')  # type: QColor
        caption = kwargs.pop('caption', 'Delivered by pigeon')  # type: str
        margin = kwargs.pop('margin', 24)  # type: int
        messageShown = kwargs.pop('messageShown', None)  # type: callable | None
        messageFinished = kwargs.pop('messageFinished', None)  # type: callable | None
        super(PigeonToast, self).__init__(*args, **kwargs)
        # Options.
        self.__m_duration = max(300, int(duration))  # type: int
        self.__m_bannerColor = QColor(bannerColor)  # type: QColor
        self.__m_textColor = QColor(textColor)  # type: QColor
        self.__m_pigeonColor = QColor(pigeonColor)  # type: QColor
        self.__m_caption = caption  # type: str
        self.__m_margin = max(0, int(margin))  # type: int
        if callable(messageShown):
            self.messageShown.connect(messageShown)
        if callable(messageFinished):
            self.messageFinished.connect(messageFinished)
        # Overlay flags.
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.NoFocus)
        if self.parentWidget() is not None:
            self.parentWidget().installEventFilter(self)
            self.setGeometry(self.parentWidget().rect())
        # State.
        self.__m_queue = []  # type: list[tuple]
        self.__m_current = None  # type: tuple | None
        self.__m_start = 0.0  # type: float
        self.__m_holdEnd = 0.0  # type: float
        self.__m_pos = QPointF(-999, -999)  # type: QPointF
        self.__m_vx = 0.0  # type: float
        self.__m_swing = 0.0  # type: float
        self.__m_swingVel = 0.0  # type: float
        self.__m_feathers = []  # type: list[Feather]
        self.__m_dropped = False  # type: bool
        self.__m_last = 0.0  # type: float
        # Timing.
        self.__m_clock = QElapsedTimer()  # type: QElapsedTimer
        self.__m_clock.start()
        self.__m_timer = QTimer(self)  # type: QTimer
        self.__m_timer.timeout.connect(self._tick)
        self.hide()

    # ---------- Helpers ----------
    def _now(self):
        """
        :return: qreal | float | int
        """
        return self.__m_clock.elapsed() / 1000.0

    def _bannerSize(self, text):
        """
        :param text: str | unicode | QString
        :return: (tuple) width float, height float, message rect height float
        """
        f = QFont(self.font())  # type: QFont
        f.setPointSizeF(10.0)
        fm = QFontMetricsF(f)  # type: QFontMetricsF
        maxW = clamp(self.width() * 0.45, 140.0, 280.0)  # type: float
        br = fm.boundingRect(QRectF(0, 0, maxW, 1000), Qt.TextWordWrap, text)  # type: QRectF
        capH = 16.0 if self.__m_caption else 0.0  # type: float
        return br.width() + 28.0, br.height() + capH + 20.0, br.height()

    def _next(self):
        """
        Start the next queued message.
        :return:
        """
        if not self.__m_queue:
            self.__m_current = None  # type: tuple | None
            if not self.__m_feathers:
                self.__m_timer.stop()
                self.hide()
            return
        self.__m_current = self.__m_queue.pop(0)  # type: tuple
        self.__m_start = self._now()  # type: float
        self.__m_holdEnd = self.__m_start + self.FLY_IN + self.__m_current[1] / 1000.0  # type: float
        self.__m_dropped = False  # type: bool
        self.__m_pos = QPointF(-999, -999)  # type: QPointF

    def _path(self, now):
        """
        :param now: qreal | float | int
        :return: (tuple) pigeon position QPointF, phase str ('in', 'hold', 'out', 'done')
        """
        text, dur = self.__m_current
        bw, bh, mh = self._bannerSize(text)
        w = float(self.width())  # type: float
        s = 46.0  # type: float
        land = QPointF(w - self.__m_margin - bw / 2.0, self.__m_margin + s * 0.5)  # type: QPointF
        startPt = QPointF(w + bw / 2.0 + 40.0, land.y() + 30.0)  # type: QPointF
        endPt = QPointF(-bw / 2.0 - 60.0, land.y() - 20.0)  # type: QPointF
        t = now - self.__m_start  # type: float
        if t < self.FLY_IN:
            k = easeOutBack(t / self.FLY_IN)  # type: float
            arc = sin(t / self.FLY_IN * pi) * -40.0  # type: float
            return QPointF(startPt.x() + (land.x() - startPt.x()) * k, startPt.y() + (land.y() - startPt.y()) * k + arc), 'in'
        if now < self.__m_holdEnd:
            return QPointF(land.x(), land.y() + sin(now * 3.0) * 4.0), 'hold'
        t2 = (now - self.__m_holdEnd) / self.FLY_OUT  # type: float
        if t2 < 1.0:
            k = easeInCubic(t2)  # type: float
            return QPointF(land.x() + (endPt.x() - land.x()) * k, land.y() + (endPt.y() - land.y()) * k
                           - sin(t2 * pi) * 30.0), 'out'
        return endPt, 'done'

    # ---------- Public API ----------
    @pyqtSlot('QString')
    @pyqtSlot(str)
    @pyqtSlot('QString', int)
    @pyqtSlot(str, int)
    def showMessage(self, text, duration=-1):
        """
        Queue a message for delivery.

        :param text: str | unicode | QString
        :param duration: (int) ms to hold it up; -1 uses the default duration.
        :return:
        """
        self.__m_queue.append((text, self.__m_duration if duration is None or duration < 0 else int(duration)))
        if self.parentWidget() is not None:
            self.setGeometry(self.parentWidget().rect())
        self.show()
        self.raise_()
        if not self.__m_timer.isActive():
            self.__m_last = self._now()  # type: float
            self.__m_timer.start(16)
        if self.__m_current is None:
            self._next()

    @pyqtSlot()
    def dismiss(self):
        """
        Send the current pigeon on its way immediately.
        :return:
        """
        now = self._now()  # type: float
        if self.__m_current is not None and now < self.__m_holdEnd:
            self.__m_holdEnd = max(now, self.__m_start + self.FLY_IN)  # type: float
            self.update()

    def getPending(self):
        """
        :return: (int) Messages waiting, including the one in flight.
        """
        return len(self.__m_queue) + (1 if self.__m_current is not None else 0)

    def getDuration(self):
        """
        :return: int
        """
        return self.__m_duration

    @pyqtSlot(int)
    def setDuration(self, duration):
        """
        :param duration: (int) ms
        :return:
        """
        self.__m_duration = max(300, int(duration))  # type: int

    def getBannerColor(self):
        """
        :return: QColor
        """
        return self.__m_bannerColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setBannerColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        self.__m_bannerColor = color  # type: QColor
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
        self.__m_textColor = color  # type: QColor
        self.update()

    def getPigeonColor(self):
        """
        :return: QColor
        """
        return self.__m_pigeonColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setPigeonColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        self.__m_pigeonColor = color  # type: QColor
        self.update()

    def getCaption(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_caption

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setCaption(self, caption):
        """
        :param caption: str | unicode | QString
        :return:
        """
        self.__m_caption = caption  # type: str

    def getMargin(self):
        """
        :return: int
        """
        return self.__m_margin

    @pyqtSlot(int)
    def setMargin(self, margin):
        """
        :param margin: (int) px
        :return:
        """
        self.__m_margin = max(0, int(margin))  # type: int

    # ---------- Qt overrides ----------
    def eventFilter(self, obj, event):
        """
        Keep covering the parent when it is resized.

        :param obj: QObject
        :param event: QEvent
        :return: bool
        """
        if obj is self.parentWidget() and event.type() == QEvent.Resize:
            self.setGeometry(self.parentWidget().rect())
        return super(PigeonToast, self).eventFilter(obj, event)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.001, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        if self.__m_current is not None:
            pos, phase = self._path(now)
            if self.__m_pos.x() > -900:
                vx = (pos.x() - self.__m_pos.x()) / dt  # type: float
                self.__m_vx += (vx - self.__m_vx) * min(1.0, dt * 10.0)
            self.__m_pos = pos  # type: QPointF
            if phase in ('in', 'hold') and not self.__m_dropped and now - self.__m_start > self.FLY_IN * 0.85:
                self.__m_dropped = True  # type: bool
                self.messageShown.emit(self.__m_current[0])
                for _ in range(3):
                    self.__m_feathers.append(Feather(pos.x() + uniform(-15, 15), pos.y() + uniform(-5, 10),
                                                     uniform(1.8, 2.6), uniform(0, 2 * pi)))
            if phase == 'done':
                self.messageFinished.emit(self.__m_current[0])
                self._next()
        # Banner swings like a pendulum, pushed by the flight speed.
        self.__m_swingVel += ((-self.__m_vx * 0.03 - self.__m_swing) * 60.0 - self.__m_swingVel * 4.0) * dt
        self.__m_swing = clamp(self.__m_swing + self.__m_swingVel * dt, -25.0, 25.0)  # type: float
        alive = []  # type: list[Feather]
        for f in self.__m_feathers:
            f.y += 28.0 * dt
            f.x += sin(now * 2.5 + f.phase) * 30.0 * dt
            f.life -= dt
            if f.life > 0:
                alive.append(f)
        self.__m_feathers = alive  # type: list[Feather]
        if self.__m_current is None and not self.__m_feathers:
            self.__m_timer.stop()
            self.hide()
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
        # Feathers.
        for f in self.__m_feathers:
            a = clamp(f.life / f.maxLife, 0.0, 1.0)  # type: float
            p.save()
            p.translate(f.x, f.y)
            p.rotate(sin(now * 2.5 + f.phase) * 35.0)
            p.setOpacity(a)
            self._drawFeather(p)
            p.restore()
        if self.__m_current is not None and self.__m_pos.x() > -900:
            pos = self.__m_pos  # type: QPointF
            text = self.__m_current[0]  # type: str
            self._drawBanner(p, pos, text)
            flap = 20.0 if abs(self.__m_vx) > 30 else 13.0  # type: float
            self._drawPigeon(p, pos, 46.0, sin(now * flap), self.__m_vx)
        p.end()

    def _drawBanner(self, p, pos, text):
        """
        :param p: QPainter
        :param pos: (QPointF) pigeon position
        :param text: str | unicode | QString
        :return:
        """
        bw, bh, mh = self._bannerSize(text)
        hang = QPointF(pos.x(), pos.y() + 20.0)  # type: QPointF
        p.save()
        p.translate(hang)
        p.rotate(self.__m_swing)
        top = 22.0  # type: float
        rect = QRectF(-bw / 2.0, top, bw, bh)  # type: QRectF
        # Strings.
        p.setPen(QPen(QColor(120, 110, 100), 1.2))
        p.drawLine(QPointF(-4.0, 0), QPointF(rect.left() + 16.0, rect.top()))
        p.drawLine(QPointF(4.0, 0), QPointF(rect.right() - 16.0, rect.top()))
        # Shadow + banner.
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 50))
        p.drawRoundedRect(rect.translated(0, 4), 10, 10)
        p.setBrush(self.__m_bannerColor)
        p.setPen(QPen(QColor(0, 0, 0, 35), 1.0))
        p.drawRoundedRect(rect, 10, 10)
        p.setBrush(QColor('#C47F3A'))
        p.setPen(Qt.NoPen)
        for x in (rect.left() + 16.0, rect.right() - 16.0):
            p.drawEllipse(QPointF(x, rect.top() + 4.0), 2.6, 2.6)
        y = rect.top() + 10.0  # type: float
        if self.__m_caption:
            cf = QFont(self.font())  # type: QFont
            cf.setPointSizeF(7.5)
            cf.setItalic(True)
            p.setFont(cf)
            cc = QColor(self.__m_textColor)  # type: QColor
            cc.setAlpha(130)
            p.setPen(cc)
            p.drawText(QRectF(rect.left() + 14.0, y, bw - 28.0, 14.0), Qt.AlignLeft | Qt.AlignVCenter, self.__m_caption)
            y += 16.0
        mf = QFont(self.font())  # type: QFont
        mf.setPointSizeF(10.0)
        p.setFont(mf)
        p.setPen(self.__m_textColor)
        p.drawText(QRectF(rect.left() + 14.0, y, bw - 28.0, mh + 2.0), Qt.TextWordWrap, text)
        p.restore()

    def _drawPigeon(self, p, pos, s, flap, vx):
        """
        Pigeon facing left.

        :param p: QPainter
        :param pos: QPointF
        :param s: (qreal | float | int) size
        :param flap: (qreal | float | int) -1..1 wing phase
        :param vx: (qreal | float | int) horizontal speed
        :return:
        """
        pc = self.__m_pigeonColor  # type: QColor
        ink = QColor('#1E1E24')  # type: QColor
        p.save()
        p.translate(pos)
        p.rotate(clamp(vx * 0.02, -12.0, 12.0))
        outline = QPen(pc.darker(150), 1.2)  # type: QPen
        # Feet holding the strings.
        p.setPen(QPen(QColor('#E58C8A'), 2.0, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(-4.0, s * 0.25), QPointF(-4.0, s * 0.44))
        p.drawLine(QPointF(4.0, s * 0.25), QPointF(4.0, s * 0.44))
        # Far wing (behind body).
        p.setPen(outline)
        p.setBrush(pc.darker(120))
        self._drawWing(p, s, -flap * 0.8 + 0.3, True)
        # Tail.
        tail = QPainterPath()  # type: QPainterPath
        tail.moveTo(s * 0.3, -s * 0.02)
        tail.lineTo(s * 0.72, -s * 0.12)
        tail.lineTo(s * 0.75, s * 0.12)
        tail.closeSubpath()
        p.setBrush(pc.darker(130))
        p.drawPath(tail)
        # Body.
        grad = QLinearGradient(QPointF(0, -s * 0.3), QPointF(0, s * 0.3))  # type: QLinearGradient
        grad.setColorAt(0.0, pc.lighter(110))
        grad.setColorAt(1.0, pc.darker(105))
        p.setBrush(grad)
        p.drawEllipse(QPointF(0, s * 0.02), s * 0.42, s * 0.26)
        # Iridescent neck.
        neck = QLinearGradient(QPointF(-s * 0.4, -s * 0.2), QPointF(-s * 0.15, s * 0.1))  # type: QLinearGradient
        neck.setColorAt(0.0, QColor('#7A5BA8'))
        neck.setColorAt(1.0, QColor('#3E9C7A'))
        p.setPen(Qt.NoPen)
        p.setBrush(neck)
        p.drawEllipse(QPointF(-s * 0.3, -s * 0.06), s * 0.15, s * 0.17)
        # Head.
        p.setPen(outline)
        p.setBrush(pc.lighter(105))
        hc = QPointF(-s * 0.42, -s * 0.22)  # type: QPointF
        p.drawEllipse(hc, s * 0.17, s * 0.16)
        # Beak.
        beak = QPainterPath()  # type: QPainterPath
        beak.moveTo(hc.x() - s * 0.14, hc.y() - s * 0.02)
        beak.lineTo(hc.x() - s * 0.3, hc.y() + s * 0.03)
        beak.lineTo(hc.x() - s * 0.14, hc.y() + s * 0.06)
        beak.closeSubpath()
        p.setPen(Qt.NoPen)
        p.setBrush(QColor('#3A3A40'))
        p.drawPath(beak)
        p.setBrush(QColor('#F2F2F2'))
        p.drawEllipse(QPointF(hc.x() - s * 0.13, hc.y() - s * 0.01), s * 0.035, s * 0.025)
        # Eye: orange ring, slightly crazed.
        p.setBrush(QColor('#F28C28'))
        p.drawEllipse(QPointF(hc.x() - s * 0.03, hc.y() - s * 0.03), s * 0.055, s * 0.055)
        p.setBrush(ink)
        p.drawEllipse(QPointF(hc.x() - s * 0.04, hc.y() - s * 0.03), s * 0.028, s * 0.028)
        # Near wing (in front).
        p.setPen(outline)
        p.setBrush(pc)
        self._drawWing(p, s, flap, False)
        p.restore()

    @staticmethod
    def _drawWing(p, s, flap, far):
        """
        :param p: QPainter
        :param s: qreal | float | int
        :param flap: (qreal | float | int) -1..1
        :param far: bool
        :return:
        """
        p.save()
        p.translate(s * 0.02, -s * (0.1 if not far else 0.14))
        p.rotate(-25.0 - flap * 45.0)
        wing = QPainterPath()  # type: QPainterPath
        wing.moveTo(-s * 0.15, 0)
        wing.cubicTo(-s * 0.1, -s * 0.35, s * 0.35, -s * 0.5, s * 0.5, -s * 0.42)
        wing.cubicTo(s * 0.35, -s * 0.2, s * 0.2, -s * 0.02, s * 0.15, 0)
        wing.closeSubpath()
        p.drawPath(wing)
        p.restore()

    def _drawFeather(self, p):
        """
        :param p: QPainter
        :return:
        """
        pc = self.__m_pigeonColor  # type: QColor
        path = QPainterPath()  # type: QPainterPath
        path.moveTo(0, -8.0)
        path.quadTo(5.0, 0, 0, 8.0)
        path.quadTo(-5.0, 0, 0, -8.0)
        p.setPen(QPen(pc.darker(140), 0.8))
        p.setBrush(pc.lighter(115))
        p.drawPath(path)
        p.drawLine(QPointF(0, -8.0), QPointF(0, 10.0))

    # ---------- Properties ----------
    duration = pyqtProperty(int, fget=getDuration, fset=setDuration)  # type: pyqtProperty
    bannerColor = pyqtProperty(QColor, fget=getBannerColor, fset=setBannerColor)  # type: pyqtProperty
    textColor = pyqtProperty(QColor, fget=getTextColor, fset=setTextColor)  # type: pyqtProperty
    pigeonColor = pyqtProperty(QColor, fget=getPigeonColor, fset=setPigeonColor)  # type: pyqtProperty
    caption = pyqtProperty('QString', fget=getCaption, fset=setCaption)  # type: pyqtProperty
    margin = pyqtProperty(int, fget=getMargin, fset=setMargin)  # type: pyqtProperty
