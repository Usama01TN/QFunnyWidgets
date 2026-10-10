# -*- coding: utf-8 -*-
"""
TypingIndicatorWidget: the chat "..." indicator, except the three dots are tiny creatures.
They bounce while typing, stare upward while thinking, vibrate furiously while deleting and fall
asleep on the keyboard when idle. autoCycle simulates a real person agonizing over a message.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty, \
    Q_ENUMS, qVersion
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont
from ManyQt.QtWidgets import QWidget
from random import uniform, choice
from enum import IntEnum
from math import sin, pi


def clamp(x, a, b):
    """
    :param x: qreal | float | int
    :param a: qreal | float | int
    :param b: qreal | float | int
    :return: qreal | float | int
    """
    return a if x < a else b if x > b else x


class TypingIndicatorWidget(QWidget):
    """
    Chat typing indicator with three expressive dots.
    """

    class States(IntEnum):
        """
        States enumeration class.
        """
        Typing = 0  # type: int
        Thinking = 1  # type: int
        Deleting = 2  # type: int
        Sleeping = 3  # type: int

    Typing = States.Typing  # type: int
    Thinking = States.Thinking  # type: int
    Deleting = States.Deleting  # type: int
    Sleeping = States.Sleeping  # type: int
    LABELS = {0: 'is typing...', 1: 'is thinking really hard...', 2: 'is deleting everything...',
              3: 'fell asleep on the keyboard'}  # type: dict
    stateChanged = pyqtSignal(int)  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param state: (States | int) Typing, Thinking, Deleting or Sleeping.
        :param name: (str | unicode | QString) Who is typing; empty hides the label.
        :param bubbleColor: QColor | Qt.GlobalColor | int | str | QString
        :param dotColor: QColor | Qt.GlobalColor | int | str | QString
        :param autoCycle: (bool) Wander between states like a real, indecisive human.
        :param stateChanged: callable | None
        :param args: any
        :param kwargs: any
        """
        state = kwargs.pop('state', TypingIndicatorWidget.Typing)  # type: int
        name = kwargs.pop('name', 'Alex')  # type: str
        bubbleColor = kwargs.pop('bubbleColor', '#E9EAF0')  # type: QColor
        dotColor = kwargs.pop('dotColor', '#7B7FFF')  # type: QColor
        autoCycle = kwargs.pop('autoCycle', False)  # type: bool
        stateChanged = kwargs.pop('stateChanged', None)  # type: callable | None
        super(TypingIndicatorWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_state = TypingIndicatorWidget.States(int(clamp(int(state), 0, 3)))  # type: TypingIndicatorWidget.States
        self.__m_name = name  # type: str
        self.__m_bubbleColor = QColor(bubbleColor)  # type: QColor
        self.__m_dotColor = QColor(dotColor)  # type: QColor
        self.__m_autoCycle = bool(autoCycle)  # type: bool
        if callable(stateChanged):
            self.stateChanged.connect(stateChanged)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        # State.
        self.__m_stateAt = 0.0  # type: float
        self.__m_nextCycle = 3.0  # type: float
        self.__m_blend = 0.0  # type: float
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

    # ---------- Public API ----------
    def getState(self):
        """
        :return: TypingIndicatorWidget.States
        """
        return self.__m_state

    @pyqtSlot(States)
    @pyqtSlot(int)
    def setState(self, state):
        """
        :param state: TypingIndicatorWidget.States | int
        :return:
        """
        state = TypingIndicatorWidget.States(int(clamp(int(state), 0, 3)))  # type: TypingIndicatorWidget.States
        if state != self.__m_state:
            self.__m_state = state  # type: TypingIndicatorWidget.States
            self.__m_stateAt = self._now()  # type: float
            self.stateChanged.emit(int(state))
            self.update()

    def getName(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_name

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setName(self, name):
        """
        :param name: str | unicode | QString
        :return:
        """
        self.__m_name = name  # type: str
        self.update()

    def getBubbleColor(self):
        """
        :return: QColor
        """
        return self.__m_bubbleColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setBubbleColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        if self.__m_bubbleColor != color:
            self.__m_bubbleColor = color  # type: QColor
            self.update()

    def getDotColor(self):
        """
        :return: QColor
        """
        return self.__m_dotColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setDotColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        if self.__m_dotColor != color:
            self.__m_dotColor = color  # type: QColor
            self.update()

    def isAutoCycle(self):
        """
        :return: bool
        """
        return self.__m_autoCycle

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setAutoCycle(self, autoCycle):
        """
        :param autoCycle: bool
        :return:
        """
        self.__m_autoCycle = bool(autoCycle)  # type: bool
        self.__m_nextCycle = self._now() + 2.0  # type: float

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(260, 90)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(90, 40)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(TypingIndicatorWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(TypingIndicatorWidget, self).hideEvent(event)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        if self.__m_autoCycle and now >= self.__m_nextCycle:
            # Typing is the hub: people type, hesitate, delete, type again... and sometimes doze off.
            if self.__m_state == self.Typing:
                nxt = choice([self.Thinking, self.Thinking, self.Deleting, self.Deleting, self.Sleeping])  # type: int
            else:
                nxt = self.Typing  # type: int
            self.setState(nxt)
            self.__m_nextCycle = now + (uniform(2.5, 4.0) if nxt == self.Typing else uniform(2.0, 3.0))  # type: float
        self.__m_blend = clamp((now - self.__m_stateAt) * 5.0, 0.0, 1.0)  # type: float
        self.update()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        now = self._now()  # type: float
        w = float(self.width())  # type: float
        h = float(self.height())  # type: float
        labelH = 22.0 if self.__m_name else 0.0  # type: float
        bh = clamp(h - labelH - 10.0, 24.0, 64.0)  # type: float
        bw = min(w - 10.0, bh * 2.6)  # type: float
        bubble = QRectF(6.0, (h - labelH - bh) / 2.0, bw, bh)  # type: QRectF
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        # Bubble with a little tail.
        path = QPainterPath()  # type: QPainterPath
        path.addRoundedRect(bubble, bh / 2.0, bh / 2.0)
        tail = QPainterPath()  # type: QPainterPath
        tail.addEllipse(QPointF(bubble.left() + bh * 0.1, bubble.bottom() - bh * 0.05), bh * 0.13, bh * 0.13)
        p.setPen(Qt.NoPen)
        p.setBrush(self.__m_bubbleColor)
        p.drawPath(path.united(tail))
        p.drawEllipse(QPointF(bubble.left() - bh * 0.05, bubble.bottom() + bh * 0.12), bh * 0.06, bh * 0.06)
        # Dots.
        st = self.__m_state  # type: int
        r = bh * 0.17  # type: float
        gap = bh * 0.55  # type: float
        cx = bubble.center().x()  # type: float
        cy = bubble.center().y()  # type: float
        since = now - self.__m_stateAt  # type: float
        for i in range(3):
            x = cx + (i - 1) * gap  # type: float
            y = cy  # type: float
            sx = 1.0  # type: float
            sy = 1.0  # type: float
            if st == self.Typing:
                ph = (now * 2.4 - i * 0.18) % 1.0  # type: float
                hop = sin(ph * 2.0 * pi) if ph < 0.5 else 0.0  # type: float
                y -= max(0.0, hop) * r * 1.2
                if ph > 0.5 and ph < 0.62:
                    sx, sy = 1.18, 0.82  # landing squash
            elif st == self.Thinking:
                y += sin(now * 1.6 + i * 0.8) * r * 0.25
            elif st == self.Deleting:
                x += uniform(-1.0, 1.0) * r * 0.25
                y += uniform(-1.0, 1.0) * r * 0.2
                # Dots get "deleted" right-to-left, then all pop back.
                ph = (since * 0.9) % 1.0  # type: float
                j = 2 - i  # type: int
                t0 = 0.15 + j * 0.22  # type: float
                if ph >= 0.88:
                    sx = clamp((ph - 0.88) * 9.0, 0.0, 1.0)  # type: float
                elif ph >= t0:
                    sx = 1.0 - clamp((ph - t0) * 12.0, 0.0, 1.0)  # type: float
                sy = sx  # type: float
            elif st == self.Sleeping:
                breathe = sin(now * 2.0 + i * 0.4)  # type: float
                sx = 1.25 + 0.05 * breathe  # type: float
                sy = 0.7 - 0.05 * breathe  # type: float
                y += r * 0.35
            if sx <= 0.01:
                continue
            self._drawDot(p, QPointF(x, y), r, sx, sy, i, st, now)
        # Thinking "?" and sleeping "z".
        f = QFont(self.font())  # type: QFont
        f.setBold(True)
        if st == self.Thinking:
            f.setPointSizeF(max(7.0, bh * 0.22))
            p.setFont(f)
            qc = QColor(self.__m_dotColor)  # type: QColor
            qc.setAlpha(int(255 * self.__m_blend))
            p.setPen(qc)
            p.drawText(QPointF(cx + gap * 1.0 - r * 0.3, bubble.top() + bh * 0.1 + sin(now * 3.0) * 2.0), '?')
        elif st == self.Sleeping:
            for k in range(2):
                ph = (now * 0.5 + k * 0.5) % 1.0  # type: float
                f.setPointSizeF(max(6.0, bh * (0.14 + 0.1 * ph)))
                p.setFont(f)
                zc = QColor(self.__m_dotColor)  # type: QColor
                zc.setAlpha(int(230 * sin(ph * pi)))
                p.setPen(zc)
                p.drawText(QPointF(bubble.right() - bh * 0.1 + ph * bh * 0.3, bubble.top() + bh * 0.2 - ph * bh * 0.45), 'z')
        # Label.
        if self.__m_name:
            lf = QFont(self.font())  # type: QFont
            lf.setPointSizeF(8.5)
            lf.setItalic(True)
            p.setFont(lf)
            tc = QColor(self.palette().text().color())  # type: QColor
            tc.setAlpha(170)
            p.setPen(tc)
            p.drawText(QRectF(bubble.left() + 4.0, bubble.bottom() + 8.0, w - 10.0, labelH),
                       Qt.AlignLeft | Qt.AlignVCenter, '{} {}'.format(self.__m_name, self.LABELS[int(st)]))
        p.end()

    def _drawDot(self, p, c, r, sx, sy, i, st, now):
        """
        :param p: QPainter
        :param c: (QPointF) center
        :param r: (qreal | float | int) radius
        :param sx: qreal | float | int
        :param sy: qreal | float | int
        :param i: (int) dot index
        :param st: (int) state
        :param now: qreal | float | int
        :return:
        """
        dc = self.__m_dotColor  # type: QColor
        p.save()
        p.translate(c)
        p.scale(sx, sy)
        p.setPen(Qt.NoPen)
        p.setBrush(dc)
        p.drawEllipse(QPointF(0, 0), r, r)
        p.setBrush(QColor(255, 255, 255, 70))
        p.drawEllipse(QPointF(-r * 0.35, -r * 0.4), r * 0.3, r * 0.2)
        ink = QColor('#FFFFFF')  # type: QColor
        ex = r * 0.38  # type: float
        er = r * 0.2  # type: float
        if st == self.Sleeping:
            p.setPen(QPen(ink, max(1.0, r * 0.14), Qt.SolidLine, Qt.RoundCap))
            p.setBrush(Qt.NoBrush)
            for d in (-1.0, 1.0):
                p.drawArc(QRectF(d * ex - er, -er * 0.4, er * 2.0, er * 1.2), 180 * 16, 180 * 16)
        elif st == self.Deleting:
            # Determined, angry little eyes.
            p.setPen(QPen(ink, max(1.0, r * 0.15), Qt.SolidLine, Qt.RoundCap))
            for d in (-1.0, 1.0):
                p.drawLine(QPointF(d * (ex + er), -er * 1.2), QPointF(d * (ex - er), -er * 0.4))
            p.setPen(Qt.NoPen)
            p.setBrush(ink)
            for d in (-1.0, 1.0):
                p.drawEllipse(QPointF(d * ex, er * 0.2), er * 0.7, er * 0.7)
        else:
            look = QPointF(0, -er * 0.6) if st == self.Thinking else QPointF(er * 0.35, 0)  # type: QPointF
            p.setBrush(ink)
            for d in (-1.0, 1.0):
                p.drawEllipse(QPointF(d * ex, -er * 0.3), er, er * 1.15)
            p.setBrush(QColor('#1E1E28'))
            for d in (-1.0, 1.0):
                p.drawEllipse(QPointF(d * ex, -er * 0.3) + look, er * 0.55, er * 0.6)
        p.restore()

    # ---------- Properties ----------
    Q_ENUMS('States' if qVersion()[0] == '4' else States)
    state = pyqtProperty(States, fget=getState, fset=setState, notify=stateChanged)  # type: pyqtProperty
    name = pyqtProperty('QString', fget=getName, fset=setName)  # type: pyqtProperty
    bubbleColor = pyqtProperty(QColor, fget=getBubbleColor, fset=setBubbleColor)  # type: pyqtProperty
    dotColor = pyqtProperty(QColor, fget=getDotColor, fset=setDotColor)  # type: pyqtProperty
    autoCycle = pyqtProperty(bool, fget=isAutoCycle, fset=setAutoCycle)  # type: pyqtProperty
