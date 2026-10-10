# -*- coding: utf-8 -*-
"""
HamsterLoaderWidget: a progress indicator powered by a hamster running in a wheel. The hamster runs
faster as work speeds up, sweats near the end, cycles through silly status messages and throws a
confetti party when progress reaches 100 %. Set progress to a negative value for indeterminate mode.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QLinearGradient
from ManyQt.QtWidgets import QWidget
from random import uniform, choice
from math import sin, cos, pi


def clamp(x, a, b):
    """
    :param x: qreal | float | int
    :param a: qreal | float | int
    :param b: qreal | float | int
    :return: qreal | float | int
    """
    return a if x < a else b if x > b else x


DEFAULT_MESSAGES = ['Feeding the hamster...', 'Reticulating splines...', 'Bribing the CPU...',
                    'Asking the cloud nicely...', 'Hamster on coffee break...', 'Counting to infinity (twice)...',
                    'Untangling the internet...', 'Almost there (probably)...']  # type: list[str]
CONFETTI_COLORS = ['#FF4D6D', '#FFD23F', '#3BCEAC', '#5E60CE', '#FF9F1C', '#4CC9F0']  # type: list[str]


class Particle(object):
    """
    One confetti piece or sweat drop.
    """

    def __init__(self, x=0.0, y=0.0, vx=0.0, vy=0.0, rot=0.0, vrot=0.0, color=None, life=1.0, kind=0):
        """
        :param x: qreal | float | int
        :param y: qreal | float | int
        :param vx: qreal | float | int
        :param vy: qreal | float | int
        :param rot: (qreal | float | int) degrees
        :param vrot: (qreal | float | int) degrees/s
        :param color: QColor | None
        :param life: (qreal | float | int) s
        :param kind: (int) 0 = confetti, 1 = sweat drop
        """
        self.x = float(x)  # type: float
        self.y = float(y)  # type: float
        self.vx = float(vx)  # type: float
        self.vy = float(vy)  # type: float
        self.rot = float(rot)  # type: float
        self.vrot = float(vrot)  # type: float
        self.color = color if color is not None else QColor('#7FD6FF')  # type: QColor
        self.life = float(life)  # type: float
        self.kind = int(kind)  # type: int


class HamsterLoaderWidget(QWidget):
    """
    Hamster-wheel progress indicator.
    """
    finished = pyqtSignal()  # type: pyqtSignal
    progressChanged = pyqtSignal(float)  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param progress: (qreal | float | int) 0..1, or < 0 for indeterminate.
        :param speed: (qreal | float | int) Base running speed multiplier.
        :param hamsterColor: QColor | Qt.GlobalColor | int | str | QString
        :param wheelColor: QColor | Qt.GlobalColor | int | str | QString
        :param accentColor: (QColor | Qt.GlobalColor | int | str | QString) Progress bar color.
        :param messages: (list[str | unicode | QString]) Status messages cycled while loading.
        :param messageInterval: (int) ms per message.
        :param doneText: (str | unicode | QString) Message shown when finished.
        :param showPercent: bool
        :param finished: callable | None
        :param args: any
        :param kwargs: any
        """
        progress = kwargs.pop('progress', 0.0)  # type: float
        speed = kwargs.pop('speed', 1.0)  # type: float
        hamsterColor = kwargs.pop('hamsterColor', '#F4A261')  # type: QColor
        wheelColor = kwargs.pop('wheelColor', '#8D99AE')  # type: QColor
        accentColor = kwargs.pop('accentColor', '#5E60CE')  # type: QColor
        messages = kwargs.pop('messages', DEFAULT_MESSAGES)  # type: list[str]
        messageInterval = kwargs.pop('messageInterval', 2200)  # type: int
        doneText = kwargs.pop('doneText', 'Done! The hamster deserves a raise.')  # type: str
        showPercent = kwargs.pop('showPercent', True)  # type: bool
        finished = kwargs.pop('finished', None)  # type: callable | None
        super(HamsterLoaderWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_progress = float(min(1.0, float(progress)))  # type: float
        self.__m_speed = max(0.0, float(speed))  # type: float
        self.__m_hamsterColor = QColor(hamsterColor)  # type: QColor
        self.__m_wheelColor = QColor(wheelColor)  # type: QColor
        self.__m_accentColor = QColor(accentColor)  # type: QColor
        self.__m_messages = list(messages) or list(DEFAULT_MESSAGES)  # type: list[str]
        self.__m_messageInterval = max(300, int(messageInterval))  # type: int
        self.__m_doneText = doneText  # type: str
        self.__m_showPercent = bool(showPercent)  # type: bool
        if callable(finished):
            self.finished.connect(finished)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        # State.
        self.__m_wheelAngle = 0.0  # type: float
        self.__m_runPhase = 0.0  # type: float
        self.__m_runSpeed = 0.0  # type: float
        self.__m_shownProgress = max(0.0, self.__m_progress)  # type: float
        self.__m_doneAt = -1.0  # type: float
        self.__m_particles = []  # type: list[Particle]
        self.__m_sweatAcc = 0.0  # type: float
        self.__m_last = 0.0  # type: float
        self.__m_hamsterPos = QPointF(0, 0)  # type: QPointF
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

    def _isDone(self):
        """
        :return: bool
        """
        return self.__m_doneAt >= 0

    def _geometry(self):
        """
        :return: (tuple) wheel center QPointF, wheel radius float, bar rect QRectF
        """
        w = float(self.width())  # type: float
        h = float(self.height())  # type: float
        barH = 12.0  # type: float
        textH = 44.0  # type: float
        R = max(10.0, min(w * 0.32, (h - barH - textH - 24.0) / 2.0))  # type: float
        c = QPointF(w / 2.0, 10.0 + R)  # type: QPointF
        bw = min(w - 32.0, max(160.0, R * 3.2))  # type: float
        bar = QRectF((w - bw) / 2.0, c.y() + R + 18.0, bw, barH)  # type: QRectF
        return c, R, bar

    # ---------- Public API ----------
    @pyqtSlot()
    def reset(self):
        """
        Start over at 0 %.
        :return:
        """
        self.__m_doneAt = -1.0  # type: float
        self.__m_progress = 0.0  # type: float
        self.__m_shownProgress = 0.0  # type: float
        self.__m_particles = []  # type: list[Particle]
        self.progressChanged.emit(0.0)
        self.update()

    def getProgress(self):
        """
        :return: qreal | float | int
        """
        return self.__m_progress

    @pyqtSlot('qreal')
    @pyqtSlot(float)
    @pyqtSlot(int)
    def setProgress(self, progress):
        """
        :param progress: (qreal | float | int) 0..1, or < 0 for indeterminate.
        :return:
        """
        progress = min(1.0, float(progress))  # type: float
        if progress != self.__m_progress:
            if progress < 1.0 and self._isDone():
                self.__m_doneAt = -1.0  # type: float
            self.__m_progress = progress  # type: float
            self.progressChanged.emit(progress)
            self.update()

    def getSpeed(self):
        """
        :return: qreal | float | int
        """
        return self.__m_speed

    @pyqtSlot('qreal')
    @pyqtSlot(float)
    @pyqtSlot(int)
    def setSpeed(self, speed):
        """
        :param speed: qreal | float | int
        :return:
        """
        self.__m_speed = max(0.0, float(speed))  # type: float

    def getHamsterColor(self):
        """
        :return: QColor
        """
        return self.__m_hamsterColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setHamsterColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        if self.__m_hamsterColor != color:
            self.__m_hamsterColor = color  # type: QColor
            self.update()

    def getWheelColor(self):
        """
        :return: QColor
        """
        return self.__m_wheelColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setWheelColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        if self.__m_wheelColor != color:
            self.__m_wheelColor = color  # type: QColor
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
        if self.__m_accentColor != color:
            self.__m_accentColor = color  # type: QColor
            self.update()

    def getMessages(self):
        """
        :return: list[str | unicode | QString]
        """
        return list(self.__m_messages)

    @pyqtSlot(list)
    def setMessages(self, messages):
        """
        :param messages: list[str]
        :return:
        """
        self.__m_messages = list(messages) or list(DEFAULT_MESSAGES)  # type: list[str]

    def getMessageInterval(self):
        """
        :return: int
        """
        return self.__m_messageInterval

    @pyqtSlot(int)
    def setMessageInterval(self, messageInterval):
        """
        :param messageInterval: (int) ms
        :return:
        """
        self.__m_messageInterval = max(300, int(messageInterval))  # type: int

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

    def isShowPercent(self):
        """
        :return: bool
        """
        return self.__m_showPercent

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setShowPercent(self, showPercent):
        """
        :param showPercent: bool
        :return:
        """
        self.__m_showPercent = bool(showPercent)  # type: bool
        self.update()

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(300, 260)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(180, 160)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(HamsterLoaderWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(HamsterLoaderWidget, self).hideEvent(event)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        indeterminate = self.__m_progress < 0  # type: bool
        # Displayed progress eases toward the real one.
        if not indeterminate:
            self.__m_shownProgress += (self.__m_progress - self.__m_shownProgress) * min(1.0, dt * 6.0)
            if self.__m_progress >= 1.0 and not self._isDone() and self.__m_shownProgress > 0.995:
                self.__m_shownProgress = 1.0  # type: float
                self.__m_doneAt = now  # type: float
                c, R, bar = self._geometry()
                for _ in range(80):
                    a = uniform(-pi, 0)  # type: float
                    s = uniform(150, 420)  # type: float
                    self.__m_particles.append(Particle(c.x(), c.y() + R * 0.5, cos(a) * s, sin(a) * s, uniform(0, 360),
                                                      uniform(-720, 720), QColor(choice(CONFETTI_COLORS)),
                                                      uniform(1.2, 2.2), 0))
                self.finished.emit()
        # Running speed: faster towards the end, panics a little at 90 %+.
        p = 0.5 if indeterminate else self.__m_shownProgress  # type: float
        target = 0.0 if self._isDone() else self.__m_speed * (1.0 + 1.6 * p)  # type: float
        self.__m_runSpeed += (target - self.__m_runSpeed) * min(1.0, dt * 3.0)
        self.__m_wheelAngle = (self.__m_wheelAngle + self.__m_runSpeed * 160.0 * dt) % 360.0  # type: float
        self.__m_runPhase += self.__m_runSpeed * 14.0 * dt
        # Sweat drops when working hard.
        if not self._isDone() and p > 0.6:
            self.__m_sweatAcc += dt * (p - 0.6) * 18.0
            while self.__m_sweatAcc > 1.0:
                self.__m_sweatAcc -= 1.0
                hp = self.__m_hamsterPos  # type: QPointF
                self.__m_particles.append(Particle(hp.x() + uniform(-4, 8), hp.y() - 8, uniform(-90, -20),
                                                  uniform(-160, -80), 0, 0, QColor('#7FD6FF'), 0.7, 1))
        alive = []  # type: list[Particle]
        for pt in self.__m_particles:
            pt.vy += (650.0 if pt.kind == 0 else 500.0) * dt
            pt.x += pt.vx * dt
            pt.y += pt.vy * dt
            pt.rot += pt.vrot * dt
            pt.life -= dt
            if pt.life > 0:
                alive.append(pt)
        self.__m_particles = alive  # type: list[Particle]
        self.update()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        now = self._now()  # type: float
        c, R, bar = self._geometry()
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        wc = self.__m_wheelColor  # type: QColor
        # Stand.
        p.setPen(QPen(wc.darker(130), max(3.0, R * 0.06), Qt.SolidLine, Qt.RoundCap))
        p.drawLine(c, QPointF(c.x() - R * 0.55, c.y() + R + 6.0))
        p.drawLine(c, QPointF(c.x() + R * 0.55, c.y() + R + 6.0))
        # Wheel back rim, spokes and rungs (rotating).
        p.save()
        p.translate(c)
        p.rotate(self.__m_wheelAngle)
        spoke = QPen(wc, max(1.5, R * 0.025))  # type: QPen
        p.setPen(spoke)
        for i in range(8):
            a = i * pi / 4.0  # type: float
            p.drawLine(QPointF(0, 0), QPointF(cos(a) * R, sin(a) * R))
        rung = QPen(wc.lighter(115), max(1.5, R * 0.035), Qt.SolidLine, Qt.RoundCap)  # type: QPen
        p.setPen(rung)
        for i in range(24):
            a = i * 2.0 * pi / 24.0  # type: float
            p.drawLine(QPointF(cos(a) * (R - 5.0), sin(a) * (R - 5.0)), QPointF(cos(a) * R, sin(a) * R))
        p.restore()
        rim = QPen(wc, max(3.0, R * 0.07))  # type: QPen
        p.setPen(rim)
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(c, R, R)
        p.setPen(Qt.NoPen)
        p.setBrush(wc.darker(140))
        p.drawEllipse(c, R * 0.08, R * 0.08)
        # Hamster.
        self._drawHamster(p, c, R, now)
        # Particles.
        p.setPen(Qt.NoPen)
        for pt in self.__m_particles:
            col = QColor(pt.color)  # type: QColor
            col.setAlpha(int(255 * clamp(pt.life * 1.5, 0.0, 1.0)))
            if pt.kind == 0:
                p.save()
                p.translate(pt.x, pt.y)
                p.rotate(pt.rot)
                p.setBrush(col)
                p.drawRect(QRectF(-4, -2, 8, 4))
                p.restore()
            else:
                drop = QPainterPath()  # type: QPainterPath
                drop.moveTo(pt.x, pt.y - 4.0)
                drop.quadTo(pt.x + 3.0, pt.y + 1.0, pt.x, pt.y + 2.5)
                drop.quadTo(pt.x - 3.0, pt.y + 1.0, pt.x, pt.y - 4.0)
                p.fillPath(drop, col)
        # Progress bar.
        indeterminate = self.__m_progress < 0  # type: bool
        track = QPainterPath()  # type: QPainterPath
        track.addRoundedRect(bar, bar.height() / 2.0, bar.height() / 2.0)
        p.fillPath(track, QColor(127, 127, 127, 60))
        p.save()
        p.setClipPath(track)
        if indeterminate:
            seg = bar.width() * 0.3  # type: float
            x = bar.left() - seg + ((now * 0.8) % 1.0) * (bar.width() + seg)  # type: float
            fill = QRectF(x, bar.top(), seg, bar.height())  # type: QRectF
        else:
            fill = QRectF(bar.left(), bar.top(), bar.width() * self.__m_shownProgress, bar.height())  # type: QRectF
        grad = QLinearGradient(fill.topLeft(), fill.topRight())  # type: QLinearGradient
        ac = QColor('#3BCEAC') if self._isDone() else self.__m_accentColor  # type: QColor
        grad.setColorAt(0.0, ac.lighter(125))
        grad.setColorAt(1.0, ac)
        fp = QPainterPath()  # type: QPainterPath
        fp.addRoundedRect(fill, bar.height() / 2.0, bar.height() / 2.0)
        p.fillPath(fp, grad)
        # Moving stripes on the filled part.
        p.setClipPath(fp, Qt.IntersectClip)
        sp = QPen(QColor(255, 255, 255, 50), 4.0)  # type: QPen
        p.setPen(sp)
        off = (now * 30.0) % 14.0  # type: float
        x = bar.left() - 14.0 + off  # type: float
        while x < bar.right() + 14.0:
            p.drawLine(QPointF(x, bar.bottom()), QPointF(x + 10.0, bar.top()))
            x += 14.0
        p.restore()
        # Texts.
        txt = self.palette().text().color()  # type: QColor
        f = QFont(self.font())  # type: QFont
        f.setPointSizeF(9.5)
        p.setFont(f)
        if self._isDone():
            msg = self.__m_doneText  # type: str
        else:
            idx = int((now * 1000.0) / self.__m_messageInterval) % len(self.__m_messages)  # type: int
            msg = self.__m_messages[idx]  # type: str
        sub = QColor(txt)  # type: QColor
        sub.setAlpha(200)
        p.setPen(sub)
        p.drawText(QRectF(0, bar.bottom() + 6.0, self.width(), 20.0), Qt.AlignHCenter | Qt.AlignTop, msg)
        if self.__m_showPercent and not indeterminate:
            f.setBold(True)
            p.setFont(f)
            p.setPen(txt)
            p.drawText(QRectF(bar.right() - 60.0, bar.top() - 20.0, 60.0, 18.0), Qt.AlignRight | Qt.AlignVCenter,
                       '{}%'.format(int(round(self.__m_shownProgress * 100))))
        p.end()

    def _drawHamster(self, p, c, R, now):
        """
        :param p: QPainter
        :param c: (QPointF) wheel center
        :param R: (qreal | float | int) wheel radius
        :param now: qreal | float | int
        :return:
        """
        s = R / 70.0  # type: float  # scale everything to the wheel
        done = self._isDone()  # type: bool
        ph = self.__m_runPhase  # type: float
        hc = self.__m_hamsterColor  # type: QColor
        ink = QColor('#2B2B33')  # type: QColor
        jump = 0.0  # type: float
        if done:
            t = now - self.__m_doneAt  # type: float
            jump = abs(sin(t * 6.0)) * 22.0 * s * max(0.0, 1.0 - t / 3.0) + (6.0 * s if t < 3.0 else 0.0)  # type: float
        bob = abs(sin(ph)) * 3.0 * s if not done else 0.0  # type: float
        base = QPointF(c.x(), c.y() + R - 26.0 * s - bob - jump)  # type: QPointF
        self.__m_hamsterPos = QPointF(base.x() + 18.0 * s, base.y() - 4.0 * s)  # type: QPointF
        p.save()
        p.translate(base)
        lean = 0.0 if done else clamp(self.__m_runSpeed * 4.0, 0.0, 12.0)  # type: float
        p.rotate(lean)
        # Legs (behind body).
        legPen = QPen(hc.darker(150), 4.0 * s, Qt.SolidLine, Qt.RoundCap)  # type: QPen
        p.setPen(legPen)
        for k, (lx, off) in enumerate(((-12.0, 0.0), (12.0, pi))):
            a = sin(ph + off) * (0.9 if not done else 0.0)  # type: float
            p.drawLine(QPointF(lx * s, 10.0 * s), QPointF(lx * s + sin(a) * 11.0 * s, 10.0 * s + cos(a) * 14.0 * s))
        # Tail.
        p.setPen(QPen(hc.darker(120), 3.0 * s, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(-24.0 * s, 0), QPointF(-30.0 * s, -3.0 * s + sin(ph * 2.0) * 2.0 * s))
        # Body.
        p.setPen(QPen(hc.darker(135), 1.5 * s))
        p.setBrush(hc)
        p.drawEllipse(QPointF(0, 0), 26.0 * s, 18.0 * s)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor('#FFF1E0'))
        p.drawEllipse(QPointF(6.0 * s, 6.0 * s), 15.0 * s, 9.0 * s)
        # Head.
        hx = 22.0 * s  # type: float
        hy = -8.0 * s  # type: float
        p.setPen(QPen(hc.darker(135), 1.5 * s))
        p.setBrush(hc)
        p.drawEllipse(QPointF(hx - 6.0 * s, hy - 13.0 * s), 6.0 * s, 6.0 * s)  # ear
        p.drawEllipse(QPointF(hx, hy), 14.0 * s, 12.0 * s)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor('#FFB3C1'))
        p.drawEllipse(QPointF(hx - 6.0 * s, hy - 13.0 * s), 3.0 * s, 3.0 * s)
        p.drawEllipse(QPointF(hx + 3.0 * s, hy + 5.0 * s), 4.0 * s, 2.5 * s)  # cheek
        p.setBrush(ink)
        p.drawEllipse(QPointF(hx + 13.0 * s, hy + 1.0 * s), 2.2 * s, 2.0 * s)  # nose
        if done:
            # Happy ^ ^ eyes.
            p.setPen(QPen(ink, 1.8 * s, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(hx + 1.0 * s, hy - 2.0 * s), QPointF(hx + 4.0 * s, hy - 5.0 * s))
            p.drawLine(QPointF(hx + 4.0 * s, hy - 5.0 * s), QPointF(hx + 7.0 * s, hy - 2.0 * s))
        else:
            p.drawEllipse(QPointF(hx + 4.0 * s, hy - 3.0 * s), 2.6 * s, 2.8 * s)
            p.setBrush(QColor('#FFFFFF'))
            p.drawEllipse(QPointF(hx + 4.8 * s, hy - 4.0 * s), 0.9 * s, 0.9 * s)
            # Determined eyebrow when going fast.
            if self.__m_runSpeed > 1.8:
                p.setPen(QPen(ink, 1.5 * s, Qt.SolidLine, Qt.RoundCap))
                p.drawLine(QPointF(hx + 1.0 * s, hy - 8.5 * s), QPointF(hx + 7.0 * s, hy - 6.5 * s))
        # Whiskers.
        p.setPen(QPen(QColor(60, 60, 70, 150), 0.8 * s))
        for dy in (-1.5, 1.5):
            p.drawLine(QPointF(hx + 12.0 * s, hy + 2.0 * s), QPointF(hx + 21.0 * s, hy + 2.0 * s + dy * 2.0 * s))
        p.restore()

    # ---------- Properties ----------
    progress = pyqtProperty('qreal', fget=getProgress, fset=setProgress, notify=progressChanged)  # type: pyqtProperty
    speed = pyqtProperty('qreal', fget=getSpeed, fset=setSpeed)  # type: pyqtProperty
    hamsterColor = pyqtProperty(QColor, fget=getHamsterColor, fset=setHamsterColor)  # type: pyqtProperty
    wheelColor = pyqtProperty(QColor, fget=getWheelColor, fset=setWheelColor)  # type: pyqtProperty
    accentColor = pyqtProperty(QColor, fget=getAccentColor, fset=setAccentColor)  # type: pyqtProperty
    messages = pyqtProperty('QStringList', fget=getMessages, fset=setMessages)  # type: pyqtProperty
    messageInterval = pyqtProperty(int, fget=getMessageInterval, fset=setMessageInterval)  # type: pyqtProperty
    doneText = pyqtProperty('QString', fget=getDoneText, fset=setDoneText)  # type: pyqtProperty
    showPercent = pyqtProperty(bool, fget=isShowPercent, fset=setShowPercent)  # type: pyqtProperty
