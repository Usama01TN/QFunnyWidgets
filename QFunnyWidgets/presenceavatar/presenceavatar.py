# -*- coding: utf-8 -*-
"""
PresenceAvatarWidget: a user avatar (initials + color derived from the name) whose online status
is also its personality. Online: eyes follow the cursor and the ring pulses. Away: dozing with a moon
badge. Busy: headphones on, focused frown. Offline: it turns into a translucent floating ghost.
Hover it and it says something in character.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty, \
    Q_ENUMS, qVersion
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QFontMetricsF, QRadialGradient, QCursor
from ManyQt.QtWidgets import QWidget
from random import uniform
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


def initialsOf(name):
    """
    :param name: str | unicode | QString
    :return: (str | unicode | QString) Up to two initials.
    """
    words = [w for w in name.replace('-', ' ').split() if w]  # type: list[str]
    if not words:
        return '?'
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[-1][0]).upper()


def colorOf(name):
    """
    :param name: str | unicode | QString
    :return: (QColor) Stable pleasant color for a name.
    """
    h = 0  # type: int
    for ch in name:
        h = (h * 31 + ord(ch)) & 0xFFFFFF
    return QColor.fromHsv(h % 360, 120, 215)


class PresenceAvatarWidget(QWidget):
    """
    Avatar whose presence status is a mood.
    """

    class Status(IntEnum):
        """
        Status enumeration class.
        """
        Online = 0  # type: int
        Away = 1  # type: int
        Busy = 2  # type: int
        Offline = 3  # type: int

    Online = Status.Online  # type: int
    Away = Status.Away  # type: int
    Busy = Status.Busy  # type: int
    Offline = Status.Offline  # type: int
    STATUS_COLORS = {0: '#3BCEAC', 1: '#FFC93C', 2: '#E63946', 3: '#8B8FA3'}  # type: dict
    GREETINGS = {0: 'Hi!', 1: 'zzz... 5 more min', 2: 'Busy. Shoo.', 3: '...boo.'}  # type: dict
    clicked = pyqtSignal()  # type: pyqtSignal
    statusChanged = pyqtSignal(int)  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param name: (str | unicode | QString) Full name; initials and color are derived from it.
        :param status: (Status | int) Online, Away, Busy or Offline.
        :param color: (QColor | Qt.GlobalColor | int | str | QString | None) None = derived from the name.
        :param badgeBorderColor: (QColor | Qt.GlobalColor | int | str | QString) Ring around the status badge.
        :param clicked: callable | None
        :param statusChanged: callable | None
        :param args: any
        :param kwargs: any
        """
        name = kwargs.pop('name', 'Ada Lovelace')  # type: str
        status = kwargs.pop('status', PresenceAvatarWidget.Online)  # type: int
        color = kwargs.pop('color', None)  # type: QColor | None
        badgeBorderColor = kwargs.pop('badgeBorderColor', '#FFFFFF')  # type: QColor
        clicked = kwargs.pop('clicked', None)  # type: callable | None
        statusChanged = kwargs.pop('statusChanged', None)  # type: callable | None
        super(PresenceAvatarWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_name = name  # type: str
        self.__m_status = PresenceAvatarWidget.Status(int(clamp(int(status), 0, 3)))  # type: PresenceAvatarWidget.Status
        self.__m_color = QColor(color) if color is not None else QColor()  # type: QColor
        self.__m_badgeBorderColor = QColor(badgeBorderColor)  # type: QColor
        if callable(clicked):
            self.clicked.connect(clicked)
        if callable(statusChanged):
            self.statusChanged.connect(statusChanged)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setCursor(Qt.PointingHandCursor)
        self._updateToolTip()
        # State.
        self.__m_hover = 0.0  # type: float
        self.__m_hovered = False  # type: bool
        self.__m_clickAt = -10.0  # type: float
        self.__m_blinkAt = 1.5 + uniform(0, 2)  # type: float
        self.__m_last = 0.0  # type: float
        # Timing.
        self.__m_clock = QElapsedTimer()  # type: QElapsedTimer
        self.__m_clock.start()
        self.__m_phase = uniform(0, 6.0)  # type: float  # so a row of avatars does not move in sync
        self.__m_timer = QTimer(self)  # type: QTimer
        self.__m_timer.timeout.connect(self._tick)
        self.__m_timer.start(16)

    # ---------- Helpers ----------
    def _now(self):
        """
        :return: qreal | float | int
        """
        return self.__m_clock.elapsed() / 1000.0 + self.__m_phase

    def _updateToolTip(self):
        """
        :return:
        """
        self.setToolTip('{} ({})'.format(self.__m_name, self.__m_status.name.lower()))

    def _baseColor(self):
        """
        :return: QColor
        """
        return QColor(self.__m_color) if self.__m_color.isValid() else colorOf(self.__m_name)

    # ---------- Public API ----------
    def getInitials(self):
        """
        :return: str | unicode | QString
        """
        return initialsOf(self.__m_name)

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
        self._updateToolTip()
        self.update()

    def getStatus(self):
        """
        :return: PresenceAvatarWidget.Status
        """
        return self.__m_status

    @pyqtSlot(Status)
    @pyqtSlot(int)
    def setStatus(self, status):
        """
        :param status: PresenceAvatarWidget.Status | int
        :return:
        """
        status = PresenceAvatarWidget.Status(int(clamp(int(status), 0, 3)))  # type: PresenceAvatarWidget.Status
        if status != self.__m_status:
            self.__m_status = status  # type: PresenceAvatarWidget.Status
            self._updateToolTip()
            self.statusChanged.emit(int(status))
            self.update()

    def getColor(self):
        """
        :return: QColor
        """
        return self._baseColor()

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

    def getBadgeBorderColor(self):
        """
        :return: QColor
        """
        return self.__m_badgeBorderColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setBadgeBorderColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        self.__m_badgeBorderColor = color  # type: QColor
        self.update()

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(130, 150)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(48, 56)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(PresenceAvatarWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(PresenceAvatarWidget, self).hideEvent(event)

    def enterEvent(self, e):
        """
        :param e: QEvent
        :return:
        """
        self.__m_hovered = True  # type: bool
        super(PresenceAvatarWidget, self).enterEvent(e)

    def leaveEvent(self, e):
        """
        :param e: QEvent
        :return:
        """
        self.__m_hovered = False  # type: bool
        super(PresenceAvatarWidget, self).leaveEvent(e)

    def mouseReleaseEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if e.button() == Qt.LeftButton and self.rect().contains(e.pos()):
            self.__m_clickAt = self._now()  # type: float
            self.clicked.emit()
        super(PresenceAvatarWidget, self).mouseReleaseEvent(e)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        self.__m_hover += ((1.0 if self.__m_hovered else 0.0) - self.__m_hover) * min(1.0, dt * 10.0)
        if now >= self.__m_blinkAt + 0.14:
            self.__m_blinkAt = now + uniform(2.0, 5.0)  # type: float
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
        st = int(self.__m_status)  # type: int
        R = max(10.0, min(w * 0.38, h * 0.33))  # type: float
        c = QPointF(w / 2.0, h - R * 1.2 - 4.0)  # type: QPointF
        hop = -abs(sin(now * 9.0)) * R * 0.08 * self.__m_hover if st != self.Offline else 0.0  # type: float
        if st == self.Offline:
            hop = sin(now * 1.8) * R * 0.08  # type: float  # ghostly float
        c = QPointF(c.x(), c.y() + hop)  # type: QPointF
        sc = QColor(self.STATUS_COLORS[st])  # type: QColor
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        # Status ring (pulses when online).
        if st != self.Offline:
            ring = QColor(sc)  # type: QColor
            if st == self.Online:
                ring.setAlpha(int(140 + 115 * (0.5 + 0.5 * sin(now * 3.0))))
            p.setPen(QPen(ring, max(2.0, R * 0.08)))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(c, R * 1.12, R * 1.12)
        base = self._baseColor()  # type: QColor
        p.save()
        if st == self.Offline:
            p.setOpacity(0.6)
            g = int(base.red() * 0.3 + base.green() * 0.59 + base.blue() * 0.11)  # type: int
            base = QColor(g, g, int(g * 1.05) if g < 243 else g)  # type: QColor
        # Head (a ghost when offline).
        head = QPainterPath()  # type: QPainterPath
        if st == self.Offline:
            head.moveTo(-R, 0)
            head.arcTo(QRectF(-R, -R, 2 * R, 2 * R), 180, -180)
            head.lineTo(R, R * 0.75)
            n = 4  # type: int
            for k in range(n):
                x0 = R - k * (2 * R / n)  # type: float
                wob = sin(now * 4.0 + k) * R * 0.06  # type: float
                head.quadTo(x0 - R / n * 0.5, R * 1.05 + wob, x0 - R / n, R * 0.75)
            head.closeSubpath()
        else:
            head.addEllipse(QPointF(0, 0), R, R)
        head.translate(c)
        grad = QRadialGradient(QPointF(c.x() - R * 0.35, c.y() - R * 0.4), R * 1.7)  # type: QRadialGradient
        grad.setColorAt(0.0, base.lighter(118))
        grad.setColorAt(1.0, base.darker(118))
        p.setPen(QPen(base.darker(135), max(1.0, R * 0.03)))
        p.setBrush(grad)
        p.drawPath(head)
        self._drawFace(p, c, R, st, now)
        # Initials.
        f = QFont(self.font())  # type: QFont
        f.setBold(True)
        f.setPointSizeF(max(6.0, R * 0.36))
        p.setFont(f)
        p.setPen(QColor(255, 255, 255, 235))
        p.drawText(QRectF(c.x() - R, c.y() + R * 0.05, 2 * R, R * 0.6), Qt.AlignCenter, initialsOf(self.__m_name))
        if st == self.Busy:
            self._drawHeadphones(p, c, R)
        p.restore()
        # Status badge.
        self._drawBadge(p, QPointF(c.x() + R * 0.78, c.y() + R * 0.78), R * 0.27, st, sc)
        # Hover bubble.
        if self.__m_hover > 0.05:
            self._drawBubble(p, QPointF(c.x() + R * 0.35, c.y() - R * 1.2), self.GREETINGS[st])
        p.end()

    def _drawFace(self, p, c, R, st, now):
        """
        :param p: QPainter
        :param c: QPointF
        :param R: qreal | float | int
        :param st: int
        :param now: qreal | float | int
        :return:
        """
        ink = QColor('#1E1E28')  # type: QColor
        ex = R * 0.33  # type: float
        ey = c.y() - R * 0.3  # type: float
        er = R * 0.17  # type: float
        pen = QPen(ink, max(1.2, R * 0.06), Qt.SolidLine, Qt.RoundCap)  # type: QPen
        waving = now - self.__m_clickAt < 1.0  # type: bool
        if st == self.Away or (st == self.Online and waving):
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            span = (180 * 16, 180 * 16) if st == self.Away else (20 * 16, 140 * 16)  # type: tuple
            for d in (-1.0, 1.0):
                p.drawArc(QRectF(c.x() + d * ex - er, ey - er * 0.5, er * 2, er * 1.2), span[0], span[1])
            if st == self.Away:
                f = QFont(self.font())  # type: QFont
                f.setBold(True)
                ph = (now * 0.6) % 1.0  # type: float
                f.setPointSizeF(max(5.0, R * (0.18 + 0.12 * ph)))
                p.setFont(f)
                zc = QColor(self.palette().text().color())  # type: QColor
                zc.setAlpha(int(220 * sin(ph * pi)))
                p.setPen(zc)
                p.drawText(QPointF(c.x() - R * 0.9 - ph * R * 0.3, c.y() - R * 0.7 - ph * R * 0.5), 'z')
            return
        if st == self.Offline:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(40, 40, 50, 200))
            for d in (-1.0, 1.0):
                p.drawEllipse(QPointF(c.x() + d * ex, ey), er * 0.7, er * 1.1)
            return
        blinking = self.__m_blinkAt <= now < self.__m_blinkAt + 0.14  # type: bool
        cur = self.mapFromGlobal(QCursor.pos())  # type: QPoint
        lx = clamp((cur.x() - c.x()) / 150.0, -1.0, 1.0)  # type: float
        ly = clamp((cur.y() - ey) / 150.0, -1.0, 1.0)  # type: float
        if st == self.Busy:
            lx, ly = 0.0, 0.6  # eyes on the work
        for d in (-1.0, 1.0):
            x = c.x() + d * ex  # type: float
            if blinking:
                p.setPen(pen)
                p.drawLine(QPointF(x - er, ey), QPointF(x + er, ey))
                continue
            p.setPen(Qt.NoPen)
            p.setBrush(QColor('#FFFFFF'))
            p.drawEllipse(QPointF(x, ey), er, er * 1.1)
            p.setBrush(ink)
            p.drawEllipse(QPointF(x + lx * er * 0.45, ey + ly * er * 0.45), er * 0.52, er * 0.56)
        if st == self.Busy:
            p.setPen(pen)
            for d in (-1.0, 1.0):
                x = c.x() + d * ex  # type: float
                p.drawLine(QPointF(x + d * er * 1.1, ey - er * 1.7), QPointF(x - d * er * 0.9, ey - er * 1.2))

    @staticmethod
    def _drawHeadphones(p, c, R):
        """
        :param p: QPainter
        :param c: QPointF
        :param R: qreal | float | int
        :return:
        """
        dark = QColor('#2B2D36')  # type: QColor
        p.setPen(QPen(dark, max(2.0, R * 0.12), Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        p.drawArc(QRectF(c.x() - R * 1.02, c.y() - R * 1.12, R * 2.04, R * 1.9), 10 * 16, 160 * 16)
        p.setPen(Qt.NoPen)
        p.setBrush(dark)
        for d in (-1.0, 1.0):
            p.drawRoundedRect(QRectF(c.x() + d * R * 0.98 - R * 0.17, c.y() - R * 0.42, R * 0.34, R * 0.55), R * 0.12, R * 0.12)
        p.setBrush(QColor('#E63946'))
        for d in (-1.0, 1.0):
            p.drawEllipse(QPointF(c.x() + d * R * 0.98, c.y() - R * 0.15), R * 0.06, R * 0.06)

    def _drawBadge(self, p, c, r, st, sc):
        """
        :param p: QPainter
        :param c: QPointF
        :param r: qreal | float | int
        :param st: int
        :param sc: QColor
        :return:
        """
        p.setPen(QPen(self.__m_badgeBorderColor, max(1.5, r * 0.3)))
        p.setBrush(sc if st != self.Offline else self.__m_badgeBorderColor)
        p.drawEllipse(c, r, r)
        if st == self.Away:
            # Crescent moon cut-out.
            p.setPen(Qt.NoPen)
            p.setBrush(self.__m_badgeBorderColor)
            p.drawEllipse(QPointF(c.x() - r * 0.35, c.y() - r * 0.3), r * 0.62, r * 0.62)
        elif st == self.Busy:
            p.setPen(QPen(QColor('#FFFFFF'), max(1.5, r * 0.3), Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(c.x() - r * 0.45, c.y()), QPointF(c.x() + r * 0.45, c.y()))
        elif st == self.Offline:
            p.setPen(QPen(sc, max(1.5, r * 0.28)))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(c, r * 0.5, r * 0.5)

    def _drawBubble(self, p, anchor, text):
        """
        :param p: QPainter
        :param anchor: (QPointF) bubble tail tip
        :param text: str | unicode | QString
        :return:
        """
        f = QFont(self.font())  # type: QFont
        f.setBold(True)
        f.setPointSizeF(8.0)
        fm = QFontMetricsF(f)  # type: QFontMetricsF
        tw = fm.horizontalAdvance(text) if hasattr(fm, 'horizontalAdvance') else fm.width(text)  # type: float
        bw = tw + 16.0  # type: float
        bh = fm.height() + 8.0  # type: float
        bx = clamp(anchor.x() - bw * 0.3, 2.0, self.width() - bw - 2.0)  # type: float
        by = max(2.0, anchor.y() - bh - 6.0)  # type: float
        p.save()
        p.setOpacity(self.__m_hover)
        path = QPainterPath()  # type: QPainterPath
        path.addRoundedRect(QRectF(bx, by, bw, bh), bh / 2.0, bh / 2.0)
        tail = QPainterPath()  # type: QPainterPath
        tx = clamp(anchor.x(), bx + 8.0, bx + bw - 8.0)  # type: float
        tail.moveTo(tx - 5.0, by + bh - 1.0)
        tail.lineTo(tx - 2.0, by + bh + 6.0)
        tail.lineTo(tx + 5.0, by + bh - 1.0)
        tail.closeSubpath()
        p.setPen(QPen(QColor(20, 20, 30, 60), 1.0))
        p.setBrush(QColor('#FFFFFF'))
        p.drawPath(path.united(tail))
        p.setFont(f)
        p.setPen(QColor('#22222A'))
        p.drawText(QRectF(bx, by, bw, bh), Qt.AlignCenter, text)
        p.restore()

    # ---------- Properties ----------
    Q_ENUMS('Status' if qVersion()[0] == '4' else Status)
    name = pyqtProperty('QString', fget=getName, fset=setName)  # type: pyqtProperty
    status = pyqtProperty(Status, fget=getStatus, fset=setStatus, notify=statusChanged)  # type: pyqtProperty
    color = pyqtProperty(QColor, fget=getColor, fset=setColor)  # type: pyqtProperty
    badgeBorderColor = pyqtProperty(QColor, fget=getBadgeBorderColor, fset=setBadgeBorderColor)  # type: pyqtProperty
