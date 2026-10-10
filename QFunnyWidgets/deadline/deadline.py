# -*- coding: utf-8 -*-
"""
DeadlineCountdownWidget: a countdown timer hosted by a tear-off calendar with escalating feelings.
Plenty of time: sunglasses, very chill. Half way: focused. Getting close: sweating. Last 10 %: full
panic with shaking red digits. Overdue: the calendar sits calmly in flames and says "This is fine"
while the overdue timer counts up. extend() buys time (and relief).
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QFontMetricsF
from ManyQt.QtWidgets import QWidget
from random import uniform
from math import sin


def clamp(x, a, b):
    """
    :param x: qreal | float | int
    :param a: qreal | float | int
    :param b: qreal | float | int
    :return: qreal | float | int
    """
    return a if x < a else b if x > b else x


def formatTime(seconds):
    """
    :param seconds: (qreal | float | int) >= 0
    :return: str | unicode | QString
    """
    s = int(seconds)  # type: int
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return '{:d}:{:02d}:{:02d}'.format(h, m, sec) if h else '{:02d}:{:02d}'.format(m, sec)


class Flame(object):
    """
    One rising flame particle.
    """

    def __init__(self, x=0.0, y=0.0, vy=0.0, size=6.0, life=0.8):
        """
        :param x: qreal | float | int
        :param y: qreal | float | int
        :param vy: qreal | float | int
        :param size: qreal | float | int
        :param life: (qreal | float | int) s
        """
        self.x = float(x)  # type: float
        self.y = float(y)  # type: float
        self.vy = float(vy)  # type: float
        self.size = float(size)  # type: float
        self.life = float(life)  # type: float
        self.maxLife = float(life)  # type: float


class DeadlineCountdownWidget(QWidget):
    """
    Countdown timer with a calendar that copes about as well as we do.
    """
    expired = pyqtSignal()  # type: pyqtSignal
    remainingChanged = pyqtSignal(int)  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param duration: (int) Seconds from start to deadline.
        :param title: (str | unicode | QString) What is due.
        :param timeScale: (qreal | float | int) Clock speed multiplier (handy for demos).
        :param autoStart: (bool) Start counting immediately.
        :param accentColor: QColor | Qt.GlobalColor | int | str | QString
        :param expired: callable | None
        :param remainingChanged: callable | None
        :param args: any
        :param kwargs: any
        """
        duration = kwargs.pop('duration', 60)  # type: int
        title = kwargs.pop('title', 'Quarterly report due')  # type: str
        timeScale = kwargs.pop('timeScale', 1.0)  # type: float
        autoStart = kwargs.pop('autoStart', True)  # type: bool
        accentColor = kwargs.pop('accentColor', '#E63946')  # type: QColor
        expired = kwargs.pop('expired', None)  # type: callable | None
        remainingChanged = kwargs.pop('remainingChanged', None)  # type: callable | None
        super(DeadlineCountdownWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_duration = max(1, int(duration))  # type: int
        self.__m_title = title  # type: str
        self.__m_timeScale = max(0.01, float(timeScale))  # type: float
        self.__m_accentColor = QColor(accentColor)  # type: QColor
        if callable(expired):
            self.expired.connect(expired)
        if callable(remainingChanged):
            self.remainingChanged.connect(remainingChanged)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        # State.
        self.__m_clock = QElapsedTimer()  # type: QElapsedTimer
        self.__m_clock.start()
        self.__m_base = float(self.__m_duration)  # type: float  # remaining at last (re)start
        self.__m_runFrom = 0.0  # type: float
        self.__m_running = False  # type: bool
        self.__m_expiredSent = False  # type: bool
        self.__m_lastWhole = -999999  # type: int
        self.__m_reliefAt = -10.0  # type: float
        self.__m_flames = []  # type: list[Flame]
        self.__m_flameAcc = 0.0  # type: float
        self.__m_last = 0.0  # type: float
        self.__m_timer = QTimer(self)  # type: QTimer
        self.__m_timer.timeout.connect(self._tick)
        self.__m_timer.start(16)
        if autoStart:
            self.start()

    # ---------- Helpers ----------
    def _now(self):
        """
        :return: qreal | float | int
        """
        return self.__m_clock.elapsed() / 1000.0

    # ---------- Public API ----------
    def getRemaining(self):
        """
        :return: (qreal | float | int) Seconds left; negative when overdue.
        """
        if not self.__m_running:
            return self.__m_base
        return self.__m_base - (self._now() - self.__m_runFrom) * self.__m_timeScale

    @pyqtSlot()
    @pyqtSlot(int)
    def start(self, seconds=-1):
        """
        (Re)start the countdown.
        :param seconds: (int) New duration; -1 keeps the current one.
        :return:
        """
        if seconds is not None and seconds >= 0:
            self.__m_duration = max(1, int(seconds))  # type: int
        self.__m_base = float(self.__m_duration)  # type: float
        self.__m_runFrom = self._now()  # type: float
        self.__m_running = True  # type: bool
        self.__m_expiredSent = False  # type: bool
        self.__m_flames = []  # type: list[Flame]
        self.update()

    @pyqtSlot()
    def pause(self):
        """
        :return:
        """
        if self.__m_running:
            self.__m_base = self.getRemaining()  # type: float
            self.__m_running = False  # type: bool

    @pyqtSlot()
    def resume(self):
        """
        :return:
        """
        if not self.__m_running:
            self.__m_runFrom = self._now()  # type: float
            self.__m_running = True  # type: bool

    @pyqtSlot(int)
    def extend(self, seconds):
        """
        Push the deadline back. Everyone relaxes.
        :param seconds: int
        :return:
        """
        rem = self.getRemaining()  # type: float
        self.__m_base = max(rem, 0.0) + max(0, int(seconds))  # type: float
        self.__m_runFrom = self._now()  # type: float
        self.__m_duration = max(self.__m_duration, int(self.__m_base))  # type: int
        self.__m_expiredSent = False  # type: bool
        self.__m_reliefAt = self._now()  # type: float
        self.__m_flames = []  # type: list[Flame]

    def isRunning(self):
        """
        :return: bool
        """
        return self.__m_running

    def getDuration(self):
        """
        :return: int
        """
        return self.__m_duration

    @pyqtSlot(int)
    def setDuration(self, duration):
        """
        :param duration: (int) s; restarts the countdown.
        :return:
        """
        self.start(max(1, int(duration)))

    def getTitle(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_title

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setTitle(self, title):
        """
        :param title: str | unicode | QString
        :return:
        """
        self.__m_title = title  # type: str
        self.update()

    def getTimeScale(self):
        """
        :return: qreal | float | int
        """
        return self.__m_timeScale

    @pyqtSlot('qreal')
    @pyqtSlot(float)
    @pyqtSlot(int)
    def setTimeScale(self, timeScale):
        """
        :param timeScale: qreal | float | int
        :return:
        """
        rem = self.getRemaining()  # type: float
        self.__m_timeScale = max(0.01, float(timeScale))  # type: float
        self.__m_base = rem  # type: float
        self.__m_runFrom = self._now()  # type: float

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
        return QSize(440, 170)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(260, 110)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(DeadlineCountdownWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(DeadlineCountdownWidget, self).hideEvent(event)

    # ---------- Animation tick ----------
    def _calRect(self):
        """
        :return: QRectF
        """
        h = float(self.height())  # type: float
        ch = h * 0.72  # type: float
        cw = ch * 0.82  # type: float
        return QRectF(14.0, (h - ch) / 2.0 + h * 0.06, cw, ch)

    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        rem = self.getRemaining()  # type: float
        whole = int(rem) if rem >= 0 else -int(-rem) - 1  # type: int
        if whole != self.__m_lastWhole:
            self.__m_lastWhole = whole  # type: int
            self.remainingChanged.emit(whole)
        if rem <= 0 and not self.__m_expiredSent:
            self.__m_expiredSent = True  # type: bool
            self.expired.emit()
        if rem <= 0:
            cal = self._calRect()  # type: QRectF
            self.__m_flameAcc += dt * 40.0
            while self.__m_flameAcc > 1.0:
                self.__m_flameAcc -= 1.0
                self.__m_flames.append(Flame(uniform(cal.left() + 4, cal.right() - 4), cal.top() + cal.height() * 0.15,
                                             -uniform(40, 90), uniform(5, 11) * cal.width() / 90.0, uniform(0.5, 0.9)))
        alive = []  # type: list[Flame]
        for f in self.__m_flames:
            f.y += f.vy * dt
            f.x += sin(now * 9.0 + f.y * 0.1) * 12.0 * dt
            f.life -= dt
            if f.life > 0:
                alive.append(f)
        self.__m_flames = alive  # type: list[Flame]
        self.update()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        now = self._now()  # type: float
        rem = self.getRemaining()  # type: float
        frac = rem / float(self.__m_duration)  # type: float
        relieved = now - self.__m_reliefAt < 1.8  # type: bool
        cal = self._calRect()  # type: QRectF
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        # Flames behind the calendar.
        self._drawFlames(p, back=True)
        p.save()
        if 0 < frac < 0.1:
            p.translate(uniform(-1.5, 1.5), uniform(-1.5, 1.5))
        self._drawCalendar(p, cal, frac, rem, relieved, now)
        p.restore()
        self._drawFlames(p, back=False)
        # Text block.
        x0 = cal.right() + 22.0  # type: float
        tw = self.width() - x0 - 10.0  # type: float
        tc = QColor(self.palette().text().color())  # type: QColor
        tf = QFont(self.font())  # type: QFont
        tf.setPointSizeF(9.5)
        tf.setBold(True)
        p.setFont(tf)
        sub = QColor(tc)  # type: QColor
        sub.setAlpha(170)
        p.setPen(sub)
        y = cal.top()  # type: float
        p.drawText(QRectF(x0, y, tw, 18), Qt.AlignLeft | Qt.AlignVCenter, self.__m_title.upper())
        # Big digits.
        df = QFont('Monospace')  # type: QFont
        df.setStyleHint(QFont.TypeWriter)
        df.setBold(True)
        df.setPointSizeF(clamp(cal.height() * 0.24, 14.0, 34.0))
        p.setFont(df)
        overdue = rem <= 0  # type: bool
        if overdue:
            digits = '+' + formatTime(-rem)  # type: str
            dc = QColor(self.__m_accentColor)  # type: QColor
        else:
            digits = formatTime(rem + 0.999)  # type: str
            dc = QColor(self.__m_accentColor) if frac < 0.1 else QColor(
                '#FF9F1C') if frac < 0.25 else QColor(tc)  # type: QColor
        dfm = QFontMetricsF(df)  # type: QFontMetricsF
        dy = y + 20.0  # type: float
        if 0 < frac < 0.1:
            # Each digit trembles on its own.
            x = x0  # type: float
            p.setPen(dc)
            for ch in digits:
                adv = dfm.horizontalAdvance(ch) if hasattr(dfm, 'horizontalAdvance') else dfm.width(ch)  # type: float
                p.drawText(QPointF(x + uniform(-1.5, 1.5), dy + dfm.ascent() + uniform(-2, 2)), ch)
                x += adv
        else:
            p.setPen(dc)
            p.drawText(QRectF(x0, dy, tw, dfm.height()), Qt.AlignLeft | Qt.AlignVCenter, digits)
        # Progress bar.
        by = dy + dfm.height() + 8.0  # type: float
        bar = QRectF(x0, by, min(tw, 260.0), 6.0)  # type: QRectF
        track = QColor(tc)  # type: QColor
        track.setAlpha(40)
        p.setPen(Qt.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(bar, 3, 3)
        p.setBrush(dc if not overdue else self.__m_accentColor)
        p.drawRoundedRect(QRectF(bar.left(), bar.top(), bar.width() * clamp(frac, 0.0, 1.0), bar.height()), 3, 3)
        # Status line.
        if relieved:
            status = self.tr('Deadline extended! Phew.')  # type: str
        elif overdue:
            status = self.tr('This is fine.')  # type: str
        elif frac > 0.5:
            status = self.tr('Plenty of time. Coffee first.')  # type: str
        elif frac > 0.25:
            status = self.tr('Okay, focusing now.')  # type: str
        elif frac > 0.1:
            status = self.tr('Why did I check email.')  # type: str
        else:
            status = self.tr('AAAAAAAAAA')  # type: str
        sf = QFont(self.font())  # type: QFont
        sf.setPointSizeF(9.0)
        sf.setItalic(True)
        p.setFont(sf)
        p.setPen(sub)
        p.drawText(QRectF(x0, by + 12.0, tw, 18), Qt.AlignLeft | Qt.AlignVCenter, status)
        p.end()

    def _drawFlames(self, p, back):
        """
        :param p: QPainter
        :param back: (bool) Draw the back half (behind the calendar) or the front half.
        :return:
        """
        p.setPen(Qt.NoPen)
        for i, f in enumerate(self.__m_flames):
            if (i % 2 == 0) != back:
                continue
            k = clamp(f.life / f.maxLife, 0.0, 1.0)  # type: float
            col = QColor(255, int(80 + 150 * k), int(30 * k))  # type: QColor
            col.setAlpha(int(220 * k))
            r = f.size * (0.5 + 0.5 * k)  # type: float
            flame = QPainterPath()  # type: QPainterPath
            flame.moveTo(f.x, f.y - r * 2.0)
            flame.cubicTo(f.x + r, f.y - r * 0.6, f.x + r, f.y + r * 0.8, f.x, f.y + r)
            flame.cubicTo(f.x - r, f.y + r * 0.8, f.x - r, f.y - r * 0.6, f.x, f.y - r * 2.0)
            p.fillPath(flame, col)

    def _drawCalendar(self, p, cal, frac, rem, relieved, now):
        """
        :param p: QPainter
        :param cal: QRectF
        :param frac: (qreal | float | int) remaining fraction
        :param rem: (qreal | float | int) remaining seconds
        :param relieved: bool
        :param now: qreal | float | int
        :return:
        """
        ink = QColor('#23232B')  # type: QColor
        r = cal.width() * 0.12  # type: float
        # Page stack shadow.
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 50))
        p.drawRoundedRect(cal.translated(4, 5), r, r)
        p.setBrush(QColor('#E7E3DA'))
        p.drawRoundedRect(cal.translated(2, 2.5), r, r)
        # Page.
        scorched = rem <= 0  # type: bool
        page = QColor('#FFFDF7') if not scorched else QColor('#F3E2C8')  # type: QColor
        p.setPen(QPen(QColor(0, 0, 0, 40), 1.0))
        p.setBrush(page)
        p.drawRoundedRect(cal, r, r)
        # Binding.
        band = QRectF(cal.left(), cal.top(), cal.width(), cal.height() * 0.22)  # type: QRectF
        bp = QPainterPath()  # type: QPainterPath
        bp.addRoundedRect(band, r, r)
        bp.addRect(QRectF(band.left(), band.center().y(), band.width(), band.height() / 2.0))
        p.setPen(Qt.NoPen)
        p.fillPath(bp.simplified(), self.__m_accentColor)
        # Rings.
        p.setBrush(QColor('#B9BCC6'))
        for k in (0.3, 0.7):
            p.drawRoundedRect(QRectF(cal.left() + cal.width() * k - 3.0, cal.top() - 6.0, 6.0, 14.0), 3, 3)
        # Month label on the binding.
        f = QFont(self.font())  # type: QFont
        f.setBold(True)
        f.setPixelSize(max(7, int(band.height() * 0.55)))
        p.setFont(f)
        p.setPen(QColor('#FFFFFF'))
        p.drawText(band.adjusted(0, 3, 0, 0), Qt.AlignCenter, self.tr('DUE'))
        # Scorch marks.
        if scorched:
            p.setBrush(QColor(60, 30, 10, 60))
            p.drawEllipse(QPointF(cal.left() + cal.width() * 0.25, cal.bottom() - cal.height() * 0.15),
                          cal.width() * 0.12, cal.height() * 0.06)
            p.drawEllipse(QPointF(cal.right() - cal.width() * 0.2, cal.top() + cal.height() * 0.32),
                          cal.width() * 0.08, cal.height() * 0.05)
        # Face.
        fc = QPointF(cal.center().x(), cal.top() + cal.height() * 0.58)  # type: QPointF
        s = cal.width() * 0.5  # type: float
        ex = s * 0.38  # type: float
        ey = fc.y() - s * 0.2  # type: float
        pen = QPen(ink, max(1.5, s * 0.07), Qt.SolidLine, Qt.RoundCap)  # type: QPen
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        my = fc.y() + s * 0.35  # type: float
        if relieved:
            for d in (-1.0, 1.0):
                p.drawArc(QRectF(fc.x() + d * ex - s * 0.13, ey - s * 0.05, s * 0.26, s * 0.16), 180 * 16, 180 * 16)
            p.drawArc(QRectF(fc.x() - s * 0.22, my - s * 0.2, s * 0.44, s * 0.28), 200 * 16, 140 * 16)
            # Exhale puff.
            pc = QColor('#C9D6E8')  # type: QColor
            p.setPen(Qt.NoPen)
            p.setBrush(pc)
            k = (now - self.__m_reliefAt) / 1.8  # type: float
            p.drawEllipse(QPointF(fc.x() + s * 0.35 + k * s * 0.5, my - k * s * 0.2), s * 0.08 * (1 + k), s * 0.06 * (1 + k))
        elif scorched:
            # "This is fine": calm closed eyes, gentle smile.
            for d in (-1.0, 1.0):
                p.drawArc(QRectF(fc.x() + d * ex - s * 0.13, ey - s * 0.02, s * 0.26, s * 0.16), 180 * 16, 180 * 16)
            p.drawArc(QRectF(fc.x() - s * 0.18, my - s * 0.18, s * 0.36, s * 0.22), 200 * 16, 140 * 16)
        elif frac > 0.5:
            # Sunglasses, smirk.
            p.setPen(QPen(ink, max(1.2, s * 0.05)))
            p.drawLine(QPointF(fc.x() - ex - s * 0.2, ey - s * 0.05), QPointF(fc.x() + ex + s * 0.2, ey - s * 0.05))
            p.setPen(Qt.NoPen)
            p.setBrush(ink)
            for d in (-1.0, 1.0):
                lens = QPainterPath()  # type: QPainterPath
                lens.addRoundedRect(QRectF(fc.x() + d * ex - s * 0.2, ey - s * 0.08, s * 0.4, s * 0.24), s * 0.08, s * 0.1)
                p.drawPath(lens)
            p.setBrush(QColor(255, 255, 255, 120))
            p.drawRect(QRectF(fc.x() - ex - s * 0.12, ey - s * 0.04, s * 0.08, s * 0.04))
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            sm = QPainterPath()  # type: QPainterPath
            sm.moveTo(fc.x() - s * 0.18, my)
            sm.quadTo(fc.x() + s * 0.05, my + s * 0.12, fc.x() + s * 0.24, my - s * 0.08)
            p.drawPath(sm)
        elif frac > 0.1:
            nervous = frac <= 0.25  # type: bool
            look = sin(now * 6.0) * s * 0.05 if nervous else 0.0  # type: float
            p.setPen(Qt.NoPen)
            p.setBrush(ink)
            for d in (-1.0, 1.0):
                p.drawEllipse(QPointF(fc.x() + d * ex + look, ey), s * 0.08, s * 0.1)
            p.setPen(pen)
            for d in (-1.0, 1.0):
                if nervous:
                    p.drawLine(QPointF(fc.x() + d * (ex + s * 0.14), ey - s * 0.2),
                               QPointF(fc.x() + d * (ex - s * 0.12), ey - s * 0.28))
                else:
                    p.drawLine(QPointF(fc.x() + d * (ex + s * 0.14), ey - s * 0.28),
                               QPointF(fc.x() + d * (ex - s * 0.12), ey - s * 0.2))
            if nervous:
                m = QPainterPath()  # type: QPainterPath
                m.moveTo(fc.x() - s * 0.2, my)
                for k in range(1, 7):
                    m.lineTo(fc.x() - s * 0.2 + k * s * 0.4 / 6.0, my + (s * 0.04 if k % 2 else -s * 0.04))
                p.drawPath(m)
                dc = QColor('#7FD6FF')  # type: QColor
                k = (now * 0.9) % 1.0  # type: float
                dc.setAlpha(int(255 * (1.0 - k)))
                x = fc.x() + s * 0.62  # type: float
                yy = ey - s * 0.2 + k * s * 0.5  # type: float
                drop = QPainterPath()  # type: QPainterPath
                drop.moveTo(x, yy - 6.0)
                drop.quadTo(x + 4.0, yy + 1.0, x, yy + 3.5)
                drop.quadTo(x - 4.0, yy + 1.0, x, yy - 6.0)
                p.fillPath(drop, dc)
            else:
                p.drawLine(QPointF(fc.x() - s * 0.16, my), QPointF(fc.x() + s * 0.16, my))
        else:
            # Panic.
            for d in (-1.0, 1.0):
                p.setPen(QPen(ink, max(1.0, s * 0.04)))
                p.setBrush(QColor('#FFFFFF'))
                p.drawEllipse(QPointF(fc.x() + d * ex, ey), s * 0.17, s * 0.19)
                p.setPen(Qt.NoPen)
                p.setBrush(ink)
                p.drawEllipse(QPointF(fc.x() + d * ex + uniform(-1, 1), ey + uniform(-1, 1)), s * 0.04, s * 0.04)
            p.setPen(pen)
            p.setBrush(QColor('#7A1F1F'))
            o = 1.0 + 0.15 * sin(now * 25.0)  # type: float
            p.drawEllipse(QPointF(fc.x(), my + s * 0.02), s * 0.16, s * 0.18 * o)

    # ---------- Properties ----------
    duration = pyqtProperty(int, fget=getDuration, fset=setDuration)  # type: pyqtProperty
    title = pyqtProperty('QString', fget=getTitle, fset=setTitle)  # type: pyqtProperty
    timeScale = pyqtProperty('qreal', fget=getTimeScale, fset=setTimeScale)  # type: pyqtProperty
    accentColor = pyqtProperty(QColor, fget=getAccentColor, fset=setAccentColor)  # type: pyqtProperty
