# -*- coding: utf-8 -*-
"""
NervousHoldButtonWidget: a hold-to-confirm button for destructive actions. While you hold it the
button fills up, gets increasingly nervous (shaking, sweating, wide eyes, escalating pleas), sighs
with relief if you let go early and dramatically faints when the action is confirmed.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QLinearGradient, QCursor
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


DEFAULT_STAGES = ['Hold to delete', 'Are you sure?', 'Really, really sure?', 'No going back!!']  # type: list[str]


class Drop(object):
    """
    One sweat drop.
    """

    def __init__(self, x=0.0, y=0.0, vx=0.0, vy=0.0, life=0.6):
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


class NervousHoldButtonWidget(QWidget):
    """
    Hold-to-confirm button with stage fright.
    """
    confirmed = pyqtSignal()  # type: pyqtSignal
    cancelled = pyqtSignal(float)  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param stages: (list[str | unicode | QString]) Labels shown while holding, from calm to panic. The first one is the idle label.
        :param doneText: (str | unicode | QString) Label after confirmation.
        :param reliefText: (str | unicode | QString) Label after an early release.
        :param holdDuration: (int) ms to hold before confirming.
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :param textColor: QColor | Qt.GlobalColor | int | str | QString
        :param autoReset: (int) ms before the fainted button recovers (0 = stays fainted until reset()).
        :param confirmed: callable | None
        :param cancelled: callable | None
        :param args: any
        :param kwargs: any
        """
        stages = kwargs.pop('stages', DEFAULT_STAGES)  # type: list[str]
        doneText = kwargs.pop('doneText', 'Deleted. RIP.')  # type: str
        reliefText = kwargs.pop('reliefText', 'Phew!')  # type: str
        holdDuration = kwargs.pop('holdDuration', 1800)  # type: int
        color = kwargs.pop('color', '#E5383B')  # type: QColor
        textColor = kwargs.pop('textColor', '#FFFFFF')  # type: QColor
        autoReset = kwargs.pop('autoReset', 2500)  # type: int
        confirmed = kwargs.pop('confirmed', None)  # type: callable | None
        cancelled = kwargs.pop('cancelled', None)  # type: callable | None
        super(NervousHoldButtonWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_stages = list(stages) or list(DEFAULT_STAGES)  # type: list[str]
        self.__m_doneText = doneText  # type: str
        self.__m_reliefText = reliefText  # type: str
        self.__m_holdDuration = max(200, int(holdDuration))  # type: int
        self.__m_color = QColor(color)  # type: QColor
        self.__m_textColor = QColor(textColor)  # type: QColor
        self.__m_autoReset = max(0, int(autoReset))  # type: int
        if callable(confirmed):
            self.confirmed.connect(confirmed)
        if callable(cancelled):
            self.cancelled.connect(cancelled)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.PointingHandCursor)
        # State.
        self.__m_holding = False  # type: bool
        self.__m_progress = 0.0  # type: float
        self.__m_faintAt = -1.0  # type: float
        self.__m_reliefUntil = 0.0  # type: float
        self.__m_hover = 0.0  # type: float
        self.__m_hovered = False  # type: bool
        self.__m_squash = 0.0  # type: float
        self.__m_squashVel = 0.0  # type: float
        self.__m_drops = []  # type: list[Drop]
        self.__m_dropAcc = 0.0  # type: float
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

    def _isFainted(self):
        """
        :return: bool
        """
        return self.__m_faintAt >= 0

    def _buttonRect(self):
        """
        :return: QRectF
        """
        w = float(self.width())  # type: float
        h = float(self.height())  # type: float
        bw = min(w - 24.0, 280.0)  # type: float
        bh = min(h - 24.0, 58.0)  # type: float
        return QRectF((w - bw) / 2.0, (h - bh) / 2.0, bw, bh)

    def _label(self, now):
        """
        :param now: qreal | float | int
        :return: str | unicode | QString
        """
        if self._isFainted():
            return self.__m_doneText
        if now < self.__m_reliefUntil and not self.__m_holding:
            return self.__m_reliefText
        if not self.__m_holding:
            return self.__m_stages[0]
        n = len(self.__m_stages)  # type: int
        return self.__m_stages[int(clamp(int(self.__m_progress * n), 0, n - 1))]

    def _press(self):
        """
        :return:
        """
        if not self._isFainted():
            self.__m_holding = True  # type: bool
            self.__m_squashVel -= 4.0

    def _release(self):
        """
        :return:
        """
        if self.__m_holding:
            self.__m_holding = False  # type: bool
            if not self._isFainted() and self.__m_progress > 0.02:
                self.__m_reliefUntil = self._now() + 1.2  # type: float
                self.__m_squashVel += 6.0
                self.cancelled.emit(self.__m_progress)

    # ---------- Public API ----------
    @pyqtSlot()
    def reset(self):
        """
        Wake the button up again.
        :return:
        """
        self.__m_faintAt = -1.0  # type: float
        self.__m_progress = 0.0  # type: float
        self.__m_holding = False  # type: bool
        self.update()

    def getProgress(self):
        """
        :return: (qreal | float | int) Current hold progress 0..1.
        """
        return self.__m_progress

    def getStages(self):
        """
        :return: list[str | unicode | QString]
        """
        return list(self.__m_stages)

    @pyqtSlot(list)
    def setStages(self, stages):
        """
        :param stages: list[str]
        :return:
        """
        self.__m_stages = list(stages) or list(DEFAULT_STAGES)  # type: list[str]
        self.update()

    def getDoneText(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_doneText

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setDoneText(self, doneText):
        """
        :param doneText: str | unicode | QString
        :return:
        """
        self.__m_doneText = doneText  # type: str
        self.update()

    def getReliefText(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_reliefText

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setReliefText(self, reliefText):
        """
        :param reliefText: str | unicode | QString
        :return:
        """
        self.__m_reliefText = reliefText  # type: str
        self.update()

    def getHoldDuration(self):
        """
        :return: int
        """
        return self.__m_holdDuration

    @pyqtSlot(int)
    def setHoldDuration(self, holdDuration):
        """
        :param holdDuration: (int) ms
        :return:
        """
        self.__m_holdDuration = max(200, int(holdDuration))  # type: int

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
        return QSize(320, 110)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(180, 60)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(NervousHoldButtonWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        self._release()
        super(NervousHoldButtonWidget, self).hideEvent(event)

    def enterEvent(self, e):
        """
        :param e: QEvent
        :return:
        """
        self.__m_hovered = True  # type: bool
        super(NervousHoldButtonWidget, self).enterEvent(e)

    def leaveEvent(self, e):
        """
        :param e: QEvent
        :return:
        """
        self.__m_hovered = False  # type: bool
        super(NervousHoldButtonWidget, self).leaveEvent(e)

    def mousePressEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if e.button() == Qt.LeftButton and self._buttonRect().contains(eventPos(e)):
            self._press()
        super(NervousHoldButtonWidget, self).mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if e.button() == Qt.LeftButton:
            self._release()
        super(NervousHoldButtonWidget, self).mouseReleaseEvent(e)

    def keyPressEvent(self, e):
        """
        :param e: QKeyEvent
        :return:
        """
        if e.key() == Qt.Key_Space:
            if not e.isAutoRepeat():
                self._press()
            return
        super(NervousHoldButtonWidget, self).keyPressEvent(e)

    def keyReleaseEvent(self, e):
        """
        :param e: QKeyEvent
        :return:
        """
        if e.key() == Qt.Key_Space:
            if not e.isAutoRepeat():
                self._release()
            return
        super(NervousHoldButtonWidget, self).keyReleaseEvent(e)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        if self._isFainted():
            if self.__m_autoReset and now - self.__m_faintAt > self.__m_autoReset / 1000.0:
                self.reset()
        elif self.__m_holding:
            self.__m_progress = min(1.0, self.__m_progress + dt * 1000.0 / self.__m_holdDuration)  # type: float
            if self.__m_progress >= 1.0:
                self.__m_holding = False  # type: bool
                self.__m_faintAt = now  # type: float
                self.__m_squashVel += 10.0
                self.confirmed.emit()
        else:
            self.__m_progress = max(0.0, self.__m_progress - dt * 3.0)  # type: float
        self.__m_squashVel += (-self.__m_squash * 260.0 - self.__m_squashVel * 12.0) * dt
        self.__m_squash += self.__m_squashVel * dt
        self.__m_hover += ((1.0 if self.__m_hovered else 0.0) - self.__m_hover) * min(1.0, dt * 10.0)
        # Sweat.
        rect = self._buttonRect()  # type: QRectF
        if self.__m_holding and self.__m_progress > 0.25:
            self.__m_dropAcc += dt * self.__m_progress * 14.0
            while self.__m_dropAcc > 1.0:
                self.__m_dropAcc -= 1.0
                side = -1.0 if uniform(0, 1) < 0.5 else 1.0  # type: float
                x = rect.left() + 4.0 if side < 0 else rect.right() - 4.0  # type: float
                self.__m_drops.append(Drop(x, rect.top() + uniform(2, 14), side * uniform(30, 80),
                                           -uniform(60, 120), uniform(0.5, 0.8)))
        alive = []  # type: list[Drop]
        for d in self.__m_drops:
            d.vy += 520.0 * dt
            d.x += d.vx * dt
            d.y += d.vy * dt
            d.life -= dt
            if d.life > 0:
                alive.append(d)
        self.__m_drops = alive  # type: list[Drop]
        self.update()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        now = self._now()  # type: float
        rect = self._buttonRect()  # type: QRectF
        prog = self.__m_progress  # type: float
        fainted = self._isFainted()  # type: bool
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        c = rect.center()  # type: QPointF
        # Shadow.
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 50))
        p.drawRoundedRect(rect.translated(0, 5).adjusted(6, 0, -6, 0), rect.height() / 2.0, rect.height() / 2.0)
        p.save()
        p.translate(c)
        # Shake grows with fear (quadratic, so it starts calm).
        shake = prog * prog * 5.0 if self.__m_holding else 0.0  # type: float
        p.translate(uniform(-shake, shake), uniform(-shake, shake) * 0.6 - 2.0 * self.__m_hover)
        if fainted:
            t = clamp((now - self.__m_faintAt) / 0.35, 0.0, 1.0)  # type: float
            p.translate(0, 6.0 * t)
            p.rotate(-7.0 * t)
        sq = clamp(self.__m_squash, -0.3, 0.3)  # type: float
        p.scale(1.0 + sq * 0.5, 1.0 - sq)
        p.translate(-c)
        r = rect.height() / 2.0  # type: float
        body = QPainterPath()  # type: QPainterPath
        body.addRoundedRect(rect, r, r)
        base = QColor('#7A7F8E') if fainted else self.__m_color  # type: QColor
        grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())  # type: QLinearGradient
        grad.setColorAt(0.0, base.lighter(115))
        grad.setColorAt(1.0, base.darker(110))
        p.fillPath(body, grad)
        # Hold fill.
        if prog > 0 and not fainted:
            p.save()
            p.setClipPath(body)
            fill = QRectF(rect.left(), rect.top(), rect.width() * prog, rect.height())  # type: QRectF
            p.fillRect(fill, base.darker(150))
            p.restore()
        p.setPen(QPen(base.darker(140), 1.5))
        p.setBrush(Qt.NoBrush)
        p.drawPath(body)
        self._drawFace(p, rect, prog, fainted, now)
        # Label.
        f = QFont(self.font())  # type: QFont
        f.setBold(True)
        f.setPointSizeF(clamp(rect.height() * 0.2, 8.0, 12.0))
        p.setFont(f)
        p.setPen(self.__m_textColor)
        p.drawText(QRectF(rect.left() + r * 1.9, rect.top(), rect.width() - r * 2.3, rect.height()),
                   Qt.AlignVCenter | Qt.AlignHCenter, self._label(now))
        p.restore()
        # Sweat drops.
        for d in self.__m_drops:
            col = QColor('#7FD6FF')  # type: QColor
            col.setAlpha(int(255 * clamp(d.life / 0.6, 0.0, 1.0)))
            drop = QPainterPath()  # type: QPainterPath
            drop.moveTo(d.x, d.y - 5.0)
            drop.quadTo(d.x + 3.5, d.y + 1.0, d.x, d.y + 3.0)
            drop.quadTo(d.x - 3.5, d.y + 1.0, d.x, d.y - 5.0)
            p.fillPath(drop, col)
        p.end()

    def _drawFace(self, p, rect, prog, fainted, now):
        """
        :param p: QPainter
        :param rect: QRectF
        :param prog: (qreal | float | int) fear 0..1
        :param fainted: bool
        :param now: qreal | float | int
        :return:
        """
        r = rect.height() / 2.0  # type: float
        fx = rect.left() + r * 1.05  # type: float
        fy = rect.center().y()  # type: float
        white = QColor('#FFFFFF')  # type: QColor
        ink = QColor('#1E1E24')  # type: QColor
        er = r * (0.17 + 0.1 * prog)  # type: float  # eyes widen with fear
        ex = r * 0.3  # type: float
        ey = fy - r * 0.15  # type: float
        pen = QPen(white, max(1.5, r * 0.08), Qt.SolidLine, Qt.RoundCap)  # type: QPen
        if fainted:
            p.setPen(pen)
            for d in (-1.0, 1.0):
                x = fx + d * ex  # type: float
                k = r * 0.13  # type: float
                p.drawLine(QPointF(x - k, ey - k), QPointF(x + k, ey + k))
                p.drawLine(QPointF(x - k, ey + k), QPointF(x + k, ey - k))
            # Tongue out.
            p.drawLine(QPointF(fx - r * 0.2, fy + r * 0.32), QPointF(fx + r * 0.2, fy + r * 0.32))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor('#FF8FA3'))
            p.drawEllipse(QPointF(fx + r * 0.08, fy + r * 0.42), r * 0.1, r * 0.12)
            return
        # Eyes look at the cursor while calm, dart around when scared.
        cur = self.mapFromGlobal(QCursor.pos())  # type: QPoint
        lx = clamp((cur.x() - fx) / 120.0, -1.0, 1.0)  # type: float
        ly = clamp((cur.y() - fy) / 120.0, -1.0, 1.0)  # type: float
        if self.__m_holding and prog > 0.4:
            lx = sin(now * 17.0)  # type: float
            ly = 0.0  # type: float
        for d in (-1.0, 1.0):
            x = fx + d * ex  # type: float
            p.setPen(Qt.NoPen)
            p.setBrush(white)
            p.drawEllipse(QPointF(x, ey), er, er)
            pr = er * (0.55 - 0.25 * prog)  # type: float  # pupils shrink
            p.setBrush(ink)
            p.drawEllipse(QPointF(x + lx * (er - pr) * 0.8, ey + ly * (er - pr) * 0.8), pr, pr)
        # Worried brows.
        if prog > 0.15:
            bp = QPen(white, max(1.2, r * 0.07), Qt.SolidLine, Qt.RoundCap)  # type: QPen
            p.setPen(bp)
            lift = er + r * 0.12  # type: float
            for d in (-1.0, 1.0):
                x = fx + d * ex  # type: float
                p.drawLine(QPointF(x + d * er * 0.8, ey - lift + r * 0.04),
                           QPointF(x - d * er * 0.6, ey - lift - r * 0.08 * prog))
        # Mouth: smile -> wobbly line -> open scream.
        p.setPen(pen)
        my = fy + r * 0.38  # type: float
        mw = r * 0.26  # type: float
        if prog < 0.05:
            relieved = now < self.__m_reliefUntil  # type: bool
            p.setBrush(Qt.NoBrush)
            p.drawArc(QRectF(fx - mw, my - r * 0.22, mw * 2.0, r * 0.3), 200 * 16, 140 * 16)
            if relieved:
                p.drawLine(QPointF(fx + r * 0.62, fy - r * 0.55), QPointF(fx + r * 0.5, fy - r * 0.35))
        elif prog < 0.7:
            mouth = QPainterPath()  # type: QPainterPath
            mouth.moveTo(fx - mw, my)
            steps = 6  # type: int
            for k in range(1, steps + 1):
                x = fx - mw + 2.0 * mw * k / float(steps)  # type: float
                y = my + (r * 0.05 if k % 2 else -r * 0.05) * (1.0 + sin(now * 30.0))  # type: float
                mouth.lineTo(x, y)
            p.setBrush(Qt.NoBrush)
            p.drawPath(mouth)
        else:
            p.setBrush(ink)
            open_ = r * (0.12 + 0.05 * sin(now * 25.0))  # type: float
            p.drawEllipse(QPointF(fx, my), r * 0.13, open_)

    # ---------- Properties ----------
    stages = pyqtProperty('QStringList', fget=getStages, fset=setStages)  # type: pyqtProperty
    doneText = pyqtProperty('QString', fget=getDoneText, fset=setDoneText)  # type: pyqtProperty
    reliefText = pyqtProperty('QString', fget=getReliefText, fset=setReliefText)  # type: pyqtProperty
    holdDuration = pyqtProperty(int, fget=getHoldDuration, fset=setHoldDuration)  # type: pyqtProperty
    color = pyqtProperty(QColor, fget=getColor, fset=setColor)  # type: pyqtProperty
    textColor = pyqtProperty(QColor, fget=getTextColor, fset=setTextColor)  # type: pyqtProperty
    autoReset = pyqtProperty(int, fget=getAutoReset, fset=setAutoReset)  # type: pyqtProperty
