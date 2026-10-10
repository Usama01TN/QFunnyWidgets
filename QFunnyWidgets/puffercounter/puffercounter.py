# -*- coding: utf-8 -*-
"""
PufferCounterWidget: a text area with a character limit, supervised by a pufferfish. It swims calmly
while you have room, inflates as you approach the limit, grows spikes near it and turns red, angry
and shaky once you go over. Delete text and it deflates with a relieved "pfff".
PufferFooterWidget is the painted counter bar and can be used on its own.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QRadialGradient
from ManyQt.QtWidgets import QWidget, QPlainTextEdit, QVBoxLayout
from math import sin, cos, pi
from random import uniform


def clamp(x, a, b):
    """
    :param x: qreal | float | int
    :param a: qreal | float | int
    :param b: qreal | float | int
    :return: qreal | float | int
    """
    return a if x < a else b if x > b else x


def lerpColor(a, b, t):
    """
    :param a: QColor
    :param b: QColor
    :param t: qreal | float | int
    :return: QColor
    """
    t = clamp(t, 0.0, 1.0)  # type: float
    return QColor(int(a.red() + (b.red() - a.red()) * t), int(a.green() + (b.green() - a.green()) * t),
                  int(a.blue() + (b.blue() - a.blue()) * t))


class Bubble(object):
    """
    A rising bubble.
    """

    def __init__(self, x=0.0, y=0.0, r=2.0, life=1.2):
        """
        :param x: qreal | float | int
        :param y: qreal | float | int
        :param r: qreal | float | int
        :param life: (qreal | float | int) s
        """
        self.x = float(x)  # type: float
        self.y = float(y)  # type: float
        self.r = float(r)  # type: float
        self.life = float(life)  # type: float
        self.maxLife = float(life)  # type: float


class PufferFooterWidget(QWidget):
    """
    Counter bar with the pufferfish.
    """

    def __init__(self, *args, **kwargs):
        """
        :param count: int
        :param maxLength: int
        :param fishColor: QColor | Qt.GlobalColor | int | str | QString
        :param args: any
        :param kwargs: any
        """
        count = kwargs.pop('count', 0)  # type: int
        maxLength = kwargs.pop('maxLength', 280)  # type: int
        fishColor = kwargs.pop('fishColor', '#FFD166')  # type: QColor
        super(PufferFooterWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_count = max(0, int(count))  # type: int
        self.__m_maxLength = max(1, int(maxLength))  # type: int
        self.__m_fishColor = QColor(fishColor)  # type: QColor
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedHeight(64)
        # State.
        self.__m_puff = self.__m_count / float(self.__m_maxLength)  # type: float  # animated inflation
        self.__m_puffVel = 0.0  # type: float
        self.__m_deflateAt = -10.0  # type: float
        self.__m_bubbles = []  # type: list[Bubble]
        self.__m_bubbleAcc = 0.0  # type: float
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
        return self.__m_count / float(self.__m_maxLength)

    # ---------- Public API ----------
    def getCount(self):
        """
        :return: int
        """
        return self.__m_count

    @pyqtSlot(int)
    def setCount(self, count):
        """
        :param count: int
        :return:
        """
        count = max(0, int(count))  # type: int
        if count != self.__m_count:
            if self.__m_count > self.__m_maxLength >= count:
                self.__m_deflateAt = self._now()  # type: float
            self.__m_count = count  # type: int
            self.update()

    def getMaxLength(self):
        """
        :return: int
        """
        return self.__m_maxLength

    @pyqtSlot(int)
    def setMaxLength(self, maxLength):
        """
        :param maxLength: int
        :return:
        """
        self.__m_maxLength = max(1, int(maxLength))  # type: int
        self.update()

    def getFishColor(self):
        """
        :return: QColor
        """
        return self.__m_fishColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setFishColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        self.__m_fishColor = color  # type: QColor
        self.update()

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(360, 64)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(PufferFooterWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(PufferFooterWidget, self).hideEvent(event)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        target = clamp(self._ratio(), 0.0, 1.3)  # type: float
        self.__m_puffVel += ((target - self.__m_puff) * 140.0 - self.__m_puffVel * 9.0) * dt
        self.__m_puff += self.__m_puffVel * dt
        fx = self.width() - 46.0  # type: float
        fy = self.height() / 2.0  # type: float
        self.__m_bubbleAcc += dt * (1.2 + (6.0 if now - self.__m_deflateAt < 0.8 else 0.0))
        while self.__m_bubbleAcc > 1.0:
            self.__m_bubbleAcc -= 1.0
            self.__m_bubbles.append(Bubble(fx + 20.0 + uniform(-4, 6), fy - 4.0, uniform(1.5, 3.5), uniform(0.8, 1.4)))
        alive = []  # type: list[Bubble]
        for b in self.__m_bubbles:
            b.y -= 22.0 * dt
            b.x += sin(now * 4.0 + b.y * 0.2) * 6.0 * dt
            b.life -= dt
            if b.life > 0:
                alive.append(b)
        self.__m_bubbles = alive  # type: list[Bubble]
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
        ratio = self._ratio()  # type: float
        over = self.__m_count > self.__m_maxLength  # type: bool
        tc = QColor(self.palette().text().color())  # type: QColor
        # Counter text + mini progress line.
        f = QFont(self.font())  # type: QFont
        f.setBold(True)
        f.setPointSizeF(10.0)
        p.setFont(f)
        remaining = self.__m_maxLength - self.__m_count  # type: int
        if over:
            col = QColor('#E63946')  # type: QColor
        elif ratio > 0.8:
            col = QColor('#FF9F1C')  # type: QColor
        else:
            col = QColor(tc)  # type: QColor
        p.setPen(col)
        p.drawText(QRectF(4, 6, 220, 20), Qt.AlignLeft | Qt.AlignVCenter, '{} / {}'.format(self.__m_count, self.__m_maxLength))
        f2 = QFont(self.font())  # type: QFont
        f2.setPointSizeF(8.5)
        f2.setItalic(True)
        p.setFont(f2)
        sub = QColor(col)  # type: QColor
        if not over:
            sub.setAlpha(160)
        p.setPen(sub)
        if over:
            msg = self.tr('{} over. The fish is furious.').format(-remaining)  # type: str
        elif now - self.__m_deflateAt < 1.2:
            msg = self.tr('pfff... thank you.')  # type: str
        elif self.__m_count == 0:
            msg = self.tr('Say something. The fish is bored.')  # type: str
        elif ratio > 0.8:
            msg = self.tr('{} left. Getting puffy...').format(remaining)  # type: str
        else:
            msg = self.tr('{} characters left').format(remaining)  # type: str
        p.drawText(QRectF(4, 26, self.width() - 100, 18), Qt.AlignLeft | Qt.AlignVCenter, msg)
        bar = QRectF(4, 50, max(10.0, self.width() - 110.0), 4)  # type: QRectF
        track = QColor(tc)  # type: QColor
        track.setAlpha(35)
        p.setPen(Qt.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(bar, 2, 2)
        p.setBrush(col if (over or ratio > 0.8) else QColor('#3BCEAC'))
        p.drawRoundedRect(QRectF(bar.left(), bar.top(), bar.width() * clamp(ratio, 0.0, 1.0), 4), 2, 2)
        # Bubbles + fish.
        for b in self.__m_bubbles:
            bc = QColor('#9ED8F5')  # type: QColor
            bc.setAlpha(int(180 * clamp(b.life / b.maxLife, 0.0, 1.0)))
            p.setPen(QPen(bc, 1.0))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QPointF(b.x, b.y), b.r, b.r)
        self._drawFish(p, QPointF(self.width() - 46.0, self.height() / 2.0), now)
        p.end()

    def _drawFish(self, p, c, now):
        """
        Fish facing right.

        :param p: QPainter
        :param c: (QPointF) center
        :param now: qreal | float | int
        :return:
        """
        puff = clamp(self.__m_puff, 0.0, 1.3)  # type: float
        over = self.__m_count > self.__m_maxLength  # type: bool
        asleep = self.__m_count == 0  # type: bool
        r = 9.0 + 15.0 * min(puff, 1.15)  # type: float
        body = lerpColor(self.__m_fishColor, QColor('#E63946'), (puff - 0.9) / 0.25)  # type: QColor
        ink = QColor('#2B2B33')  # type: QColor
        p.save()
        p.translate(c.x() + (uniform(-1.5, 1.5) if over else 0.0), c.y() + sin(now * 2.0) * 2.0)
        # Tail (wiggles).
        wig = sin(now * (10.0 if not asleep else 3.0)) * r * 0.15  # type: float
        tail = QPainterPath()  # type: QPainterPath
        tail.moveTo(-r * 0.85, 0)
        tail.lineTo(-r * 1.35, -r * 0.45 + wig)
        tail.lineTo(-r * 1.35, r * 0.45 + wig)
        tail.closeSubpath()
        p.setPen(QPen(body.darker(140), 1.0))
        p.setBrush(body.darker(110))
        p.drawPath(tail)
        # Spikes appear past 80 %.
        spikes = clamp((puff - 0.75) / 0.3, 0.0, 1.0)  # type: float
        if spikes > 0:
            p.setPen(QPen(body.darker(150), max(1.0, r * 0.06), Qt.SolidLine, Qt.RoundCap))
            for k in range(14):
                a = k * 2.0 * pi / 14.0  # type: float
                p.drawLine(QPointF(cos(a) * r * 0.95, sin(a) * r * 0.95),
                           QPointF(cos(a) * r * (0.95 + 0.35 * spikes), sin(a) * r * (0.95 + 0.35 * spikes)))
        # Body.
        grad = QRadialGradient(QPointF(-r * 0.3, -r * 0.35), r * 1.6)  # type: QRadialGradient
        grad.setColorAt(0.0, body.lighter(120))
        grad.setColorAt(1.0, body.darker(112))
        p.setPen(QPen(body.darker(145), 1.2))
        p.setBrush(grad)
        p.drawEllipse(QPointF(0, 0), r, r * 0.92)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 60))
        p.drawEllipse(QPointF(0, r * 0.35), r * 0.6, r * 0.35)
        # Spots.
        p.setBrush(body.darker(125))
        for sx, sy in ((-0.35, -0.4), (-0.05, -0.55), (-0.5, -0.05)):
            p.drawEllipse(QPointF(sx * r, sy * r), r * 0.08, r * 0.08)
        # Side fin.
        p.setBrush(body.darker(108))
        p.setPen(QPen(body.darker(140), 1.0))
        p.drawEllipse(QPointF(-r * 0.1, r * 0.2), r * 0.22, r * 0.12)
        # Eye.
        ex = r * 0.42  # type: float
        ey = -r * 0.22  # type: float
        if asleep:
            p.setPen(QPen(ink, 1.4, Qt.SolidLine, Qt.RoundCap))
            p.drawArc(QRectF(ex - r * 0.15, ey - r * 0.05, r * 0.3, r * 0.18), 180 * 16, 180 * 16)
        else:
            er = r * (0.2 if not over else 0.24)  # type: float
            p.setPen(QPen(ink, 1.0))
            p.setBrush(QColor('#FFFFFF'))
            p.drawEllipse(QPointF(ex, ey), er, er)
            p.setPen(Qt.NoPen)
            p.setBrush(ink)
            pr = er * (0.55 - 0.25 * clamp(puff - 0.8, 0.0, 0.5))  # type: float
            p.drawEllipse(QPointF(ex + er * 0.2, ey), pr, pr)
            if over:
                p.setPen(QPen(ink, max(1.5, r * 0.08), Qt.SolidLine, Qt.RoundCap))
                p.drawLine(QPointF(ex - er * 1.1, ey - er * 1.3), QPointF(ex + er * 0.9, ey - er * 0.7))
        # Mouth: little "o", pursed when puffed.
        p.setPen(QPen(ink, 1.2))
        p.setBrush(QColor('#7A2E2E') if over else Qt.NoBrush)
        mo = r * (0.08 + (0.07 if over else 0.0))  # type: float
        p.drawEllipse(QPointF(r * 0.86, r * 0.12), mo, mo * (1.2 if over else 1.0))
        p.restore()
        if asleep:
            f = QFont(self.font())  # type: QFont
            f.setBold(True)
            ph = (now * 0.5) % 1.0  # type: float
            f.setPointSizeF(6.5 + 3.0 * ph)
            p.setFont(f)
            zc = QColor(self.palette().text().color())  # type: QColor
            zc.setAlpha(int(200 * sin(ph * pi)))
            p.setPen(zc)
            p.drawText(QPointF(c.x() + 10.0 + ph * 8.0, c.y() - 12.0 - ph * 12.0), 'z')

    # ---------- Properties ----------
    count = pyqtProperty(int, fget=getCount, fset=setCount)  # type: pyqtProperty
    maxLength = pyqtProperty(int, fget=getMaxLength, fset=setMaxLength)  # type: pyqtProperty
    fishColor = pyqtProperty(QColor, fget=getFishColor, fset=setFishColor)  # type: pyqtProperty


class PufferCounterWidget(QWidget):
    """
    Plain-text editor + pufferfish character counter.
    """
    textChanged = pyqtSignal('QString')  # type: pyqtSignal
    limitExceeded = pyqtSignal(bool)  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param text: str | unicode | QString
        :param placeholder: str | unicode | QString
        :param maxLength: int
        :param enforceLimit: (bool) Refuse characters beyond the limit instead of just complaining.
        :param fishColor: QColor | Qt.GlobalColor | int | str | QString
        :param textChanged: callable | None
        :param limitExceeded: callable | None
        :param args: any
        :param kwargs: any
        """
        text = kwargs.pop('text', '')  # type: str
        placeholder = kwargs.pop('placeholder', "What's happening?")  # type: str
        maxLength = kwargs.pop('maxLength', 280)  # type: int
        enforceLimit = kwargs.pop('enforceLimit', False)  # type: bool
        fishColor = kwargs.pop('fishColor', '#FFD166')  # type: QColor
        textChanged = kwargs.pop('textChanged', None)  # type: callable | None
        limitExceeded = kwargs.pop('limitExceeded', None)  # type: callable | None
        super(PufferCounterWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_enforce = bool(enforceLimit)  # type: bool
        self.__m_over = False  # type: bool
        if callable(textChanged):
            self.textChanged.connect(textChanged)
        if callable(limitExceeded):
            self.limitExceeded.connect(limitExceeded)
        # Children.
        self.__m_edit = QPlainTextEdit()  # type: QPlainTextEdit
        self.__m_edit.setObjectName('pufferEdit')
        self.__m_edit.setPlaceholderText(placeholder)
        self.__m_footer = PufferFooterWidget(maxLength=maxLength, fishColor=fishColor)  # type: PufferFooterWidget
        layout = QVBoxLayout(self)  # type: QVBoxLayout
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self.__m_edit, 1)
        layout.addWidget(self.__m_footer)
        self.__m_edit.textChanged.connect(self._onText)
        self.__m_edit.setPlainText(text)

    # ---------- Helpers ----------
    @pyqtSlot()
    def _onText(self):
        """
        :return:
        """
        text = self.__m_edit.toPlainText()  # type: str
        limit = self.__m_footer.getMaxLength()  # type: int
        if self.__m_enforce and len(text) > limit:
            cur = self.__m_edit.textCursor()
            pos = min(cur.position(), limit)  # type: int
            self.__m_edit.blockSignals(True)
            self.__m_edit.setPlainText(text[:limit])
            self.__m_edit.blockSignals(False)
            cur = self.__m_edit.textCursor()
            cur.setPosition(pos)
            self.__m_edit.setTextCursor(cur)
            text = text[:limit]  # type: str
        self.__m_footer.setCount(len(text))
        over = len(text) > limit  # type: bool
        if over != self.__m_over:
            self.__m_over = over  # type: bool
            self.limitExceeded.emit(over)
        self.textChanged.emit(text)

    # ---------- Public API ----------
    def getEditor(self):
        """
        :return: QPlainTextEdit
        """
        return self.__m_edit

    def getFooter(self):
        """
        :return: PufferFooterWidget
        """
        return self.__m_footer

    def isOverLimit(self):
        """
        :return: bool
        """
        return self.__m_over

    def getText(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_edit.toPlainText()

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setText(self, text):
        """
        :param text: str | unicode | QString
        :return:
        """
        self.__m_edit.setPlainText(text)

    def getPlaceholder(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_edit.placeholderText()

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setPlaceholder(self, placeholder):
        """
        :param placeholder: str | unicode | QString
        :return:
        """
        self.__m_edit.setPlaceholderText(placeholder)

    def getMaxLength(self):
        """
        :return: int
        """
        return self.__m_footer.getMaxLength()

    @pyqtSlot(int)
    def setMaxLength(self, maxLength):
        """
        :param maxLength: int
        :return:
        """
        self.__m_footer.setMaxLength(maxLength)
        self._onText()

    def isEnforceLimit(self):
        """
        :return: bool
        """
        return self.__m_enforce

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setEnforceLimit(self, enforceLimit):
        """
        :param enforceLimit: bool
        :return:
        """
        self.__m_enforce = bool(enforceLimit)  # type: bool
        self._onText()

    # ---------- Properties ----------
    text = pyqtProperty('QString', fget=getText, fset=setText, notify=textChanged)  # type: pyqtProperty
    placeholder = pyqtProperty('QString', fget=getPlaceholder, fset=setPlaceholder)  # type: pyqtProperty
    maxLength = pyqtProperty(int, fget=getMaxLength, fset=setMaxLength)  # type: pyqtProperty
    enforceLimit = pyqtProperty(bool, fget=isEnforceLimit, fset=setEnforceLimit)  # type: pyqtProperty
