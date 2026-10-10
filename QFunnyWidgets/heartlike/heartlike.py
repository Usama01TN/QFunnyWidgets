# -*- coding: utf-8 -*-
"""
HeartLikeButtonWidget: a like button with a heart that has a heart. Liking it makes it pop, burst
mini hearts and keep a happy heartbeat; un-liking cracks it (it gets a bandage afterward); toggling
too often makes it dizzy ("Make up your mind!"). The counter rolls like an odometer.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QFontMetricsF, QRadialGradient
from ManyQt.QtWidgets import QWidget
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


def heartPath(c, s):
    """
    :param c: (QPointF) center
    :param s: (qreal | float | int) half width
    :return: QPainterPath
    """
    x = c.x()  # type: float
    y = c.y()  # type: float
    path = QPainterPath()  # type: QPainterPath
    path.moveTo(x, y + s * 0.95)
    path.cubicTo(x - s * 1.55, y + s * 0.05, x - s * 0.95, y - s * 1.15, x, y - s * 0.45)
    path.cubicTo(x + s * 0.95, y - s * 1.15, x + s * 1.55, y + s * 0.05, x, y + s * 0.95)
    return path


class MiniHeart(object):
    """
    A small heart from the like burst.
    """

    def __init__(self, x=0.0, y=0.0, vx=0.0, vy=0.0, life=0.8, size=5.0):
        """
        :param x: qreal | float | int
        :param y: qreal | float | int
        :param vx: qreal | float | int
        :param vy: qreal | float | int
        :param life: (qreal | float | int) s
        :param size: qreal | float | int
        """
        self.x = float(x)  # type: float
        self.y = float(y)  # type: float
        self.vx = float(vx)  # type: float
        self.vy = float(vy)  # type: float
        self.life = float(life)  # type: float
        self.maxLife = float(life)  # type: float
        self.size = float(size)  # type: float


class HeartLikeButtonWidget(QWidget):
    """
    Like button with feelings.
    """
    likedChanged = pyqtSignal(bool)  # type: pyqtSignal
    countChanged = pyqtSignal(int)  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param liked: bool
        :param count: (int) Number of likes shown next to the heart.
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :param showCount: bool
        :param likedChanged: callable | None
        :param countChanged: callable | None
        :param args: any
        :param kwargs: any
        """
        liked = kwargs.pop('liked', False)  # type: bool
        count = kwargs.pop('count', 41)  # type: int
        color = kwargs.pop('color', '#FF4D6D')  # type: QColor
        showCount = kwargs.pop('showCount', True)  # type: bool
        likedChanged = kwargs.pop('likedChanged', None)  # type: callable | None
        countChanged = kwargs.pop('countChanged', None)  # type: callable | None
        super(HeartLikeButtonWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_liked = bool(liked)  # type: bool
        self.__m_count = max(0, int(count))  # type: int
        self.__m_color = QColor(color)  # type: QColor
        self.__m_showCount = bool(showCount)  # type: bool
        if callable(likedChanged):
            self.likedChanged.connect(likedChanged)
        if callable(countChanged):
            self.countChanged.connect(countChanged)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        # State.
        self.__m_pop = 1.0  # type: float
        self.__m_popVel = 0.0  # type: float
        self.__m_unlikedAt = -10.0  # type: float
        self.__m_toggles = []  # type: list[float]
        self.__m_dizzyUntil = 0.0  # type: float
        self.__m_minis = []  # type: list[MiniHeart]
        self.__m_ringAt = -10.0  # type: float
        self.__m_oldCount = self.__m_count  # type: int
        self.__m_countAt = -10.0  # type: float
        self.__m_hovered = False  # type: bool
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

    def _heartGeom(self):
        """
        :return: (tuple) center QPointF, half width float
        """
        h = float(self.height())  # type: float
        w = float(self.width())  # type: float
        s = clamp(min(h * 0.3, w * 0.22), 10.0, 60.0)  # type: float
        cx = s * 1.6 + 4.0 if self.__m_showCount else w / 2.0  # type: float
        return QPointF(cx, h / 2.0 + s * 0.05), s

    def _setCount(self, count):
        """
        :param count: int
        :return:
        """
        count = max(0, int(count))  # type: int
        if count != self.__m_count:
            self.__m_oldCount = self.__m_count  # type: int
            self.__m_count = count  # type: int
            self.__m_countAt = self._now()  # type: float
            self.countChanged.emit(count)

    # ---------- Public API ----------
    @pyqtSlot()
    def toggle(self):
        """
        :return:
        """
        self.setLiked(not self.__m_liked)

    def isLiked(self):
        """
        :return: bool
        """
        return self.__m_liked

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setLiked(self, liked):
        """
        :param liked: bool
        :return:
        """
        liked = bool(liked)  # type: bool
        if liked == self.__m_liked:
            return
        now = self._now()  # type: float
        self.__m_liked = liked  # type: bool
        self.__m_toggles = [t for t in self.__m_toggles if now - t < 2.0] + [now]  # type: list[float]
        if len(self.__m_toggles) >= 4:
            self.__m_dizzyUntil = now + 2.0  # type: float
        c, s = self._heartGeom()
        if liked:
            self.__m_popVel += 14.0
            self.__m_ringAt = now  # type: float
            for k in range(9):
                a = -pi / 2.0 + (k - 4) * 0.36 + uniform(-0.1, 0.1)  # type: float
                sp = uniform(90, 160)  # type: float
                self.__m_minis.append(MiniHeart(c.x(), c.y() - s * 0.2, cos(a) * sp, sin(a) * sp, uniform(0.6, 0.9),
                                                s * uniform(0.12, 0.2)))
            self._setCount(self.__m_count + 1)
        else:
            self.__m_unlikedAt = now  # type: float
            self.__m_popVel -= 6.0
            self._setCount(self.__m_count - 1)
        self.likedChanged.emit(liked)
        self.update()

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
        self._setCount(count)

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
        self.__m_color = color  # type: QColor
        self.update()

    def isShowCount(self):
        """
        :return: bool
        """
        return self.__m_showCount

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setShowCount(self, showCount):
        """
        :param showCount: bool
        :return:
        """
        self.__m_showCount = bool(showCount)  # type: bool
        self.update()

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(200, 120)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(60, 50)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(HeartLikeButtonWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(HeartLikeButtonWidget, self).hideEvent(event)

    def enterEvent(self, e):
        """
        :param e: QEvent
        :return:
        """
        self.__m_hovered = True  # type: bool
        super(HeartLikeButtonWidget, self).enterEvent(e)

    def leaveEvent(self, e):
        """
        :param e: QEvent
        :return:
        """
        self.__m_hovered = False  # type: bool
        super(HeartLikeButtonWidget, self).leaveEvent(e)

    def mouseReleaseEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if e.button() == Qt.LeftButton and self.rect().contains(e.pos()):
            self.toggle()
        super(HeartLikeButtonWidget, self).mouseReleaseEvent(e)

    def keyPressEvent(self, e):
        """
        :param e: QKeyEvent
        :return:
        """
        if e.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
            self.toggle()
            return
        super(HeartLikeButtonWidget, self).keyPressEvent(e)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        self.__m_popVel += ((1.0 - self.__m_pop) * 340.0 - self.__m_popVel * 11.0) * dt
        self.__m_pop += self.__m_popVel * dt
        alive = []  # type: list[MiniHeart]
        for m in self.__m_minis:
            m.vy += 220.0 * dt
            m.vx *= 0.98
            m.x += m.vx * dt
            m.y += m.vy * dt
            m.life -= dt
            if m.life > 0:
                alive.append(m)
        self.__m_minis = alive  # type: list[MiniHeart]
        self.update()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        now = self._now()  # type: float
        c, s = self._heartGeom()
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        liked = self.__m_liked  # type: bool
        dizzy = now < self.__m_dizzyUntil  # type: bool
        sinceUnlike = now - self.__m_unlikedAt  # type: float
        cracking = (not liked) and sinceUnlike < 0.9  # type: bool
        # Burst ring.
        rs = now - self.__m_ringAt  # type: float
        if rs < 0.45:
            rc = QColor(self.__m_color)  # type: QColor
            rc.setAlpha(int(200 * (1.0 - rs / 0.45)))
            p.setPen(QPen(rc, max(1.5, s * 0.08 * (1.0 - rs / 0.45))))
            p.setBrush(Qt.NoBrush)
            rr = s * (0.6 + 1.2 * rs / 0.45)  # type: float
            p.drawEllipse(c, rr, rr)
        # Heartbeat (lub-dub) when liked.
        beat = 1.0  # type: float
        if liked:
            ph = now % 1.3  # type: float
            beat += 0.07 * max(0.0, sin(ph / 0.15 * pi)) if ph < 0.15 else 0.0
            beat += 0.05 * max(0.0, sin((ph - 0.22) / 0.15 * pi)) if 0.22 <= ph < 0.37 else 0.0
        k = max(0.3, self.__m_pop) * beat  # type: float
        if dizzy:
            p.save()
            p.translate(c)
            p.rotate(sin(now * 9.0) * 12.0)
            p.translate(-c)
        p.save()
        p.translate(c)
        p.scale(k, k)
        p.translate(-c)
        if cracking:
            self._drawCracked(p, c, s, sinceUnlike)
        else:
            self._drawHeart(p, c, s, liked)
        self._drawFace(p, c, s, liked, dizzy, cracking, now)
        p.restore()
        if dizzy:
            p.restore()
        # Bandage after a break-up (fades away).
        if not liked and 0.9 <= sinceUnlike < 4.5:
            a = clamp((4.5 - sinceUnlike) / 1.0, 0.0, 1.0)  # type: float
            p.save()
            p.setOpacity(a)
            p.translate(c.x() + s * 0.45, c.y() - s * 0.35)
            p.rotate(35)
            p.setPen(QPen(QColor('#C9A27E'), 1.0))
            p.setBrush(QColor('#F2D2B0'))
            p.drawRoundedRect(QRectF(-s * 0.32, -s * 0.11, s * 0.64, s * 0.22), s * 0.1, s * 0.1)
            p.setBrush(QColor('#E8C09A'))
            p.drawRect(QRectF(-s * 0.1, -s * 0.11, s * 0.2, s * 0.22))
            p.restore()
        # Mini hearts.
        p.setPen(Qt.NoPen)
        for m in self.__m_minis:
            mc = QColor(self.__m_color)  # type: QColor
            mc.setAlpha(int(255 * clamp(m.life / m.maxLife, 0.0, 1.0)))
            p.fillPath(heartPath(QPointF(m.x, m.y), m.size), mc)
        # Dizzy bubble.
        if dizzy:
            f = QFont(self.font())  # type: QFont
            f.setBold(True)
            f.setPointSizeF(8.0)
            fm = QFontMetricsF(f)  # type: QFontMetricsF
            text = self.tr('Make up your mind!')  # type: str
            tw = fm.horizontalAdvance(text) if hasattr(fm, 'horizontalAdvance') else fm.width(text)  # type: float
            bw = tw + 14.0  # type: float
            bh = fm.height() + 6.0  # type: float
            bx = clamp(c.x() - bw / 2.0, 2.0, self.width() - bw - 2.0)  # type: float
            by = max(2.0, c.y() - s * 1.25 - bh)  # type: float
            p.setPen(QPen(QColor(20, 20, 30, 60), 1.0))
            p.setBrush(QColor('#FFFFFF'))
            p.drawRoundedRect(QRectF(bx, by, bw, bh), bh / 2.0, bh / 2.0)
            p.setFont(f)
            p.setPen(QColor('#22222A'))
            p.drawText(QRectF(bx, by, bw, bh), Qt.AlignCenter, text)
        # Odometer count.
        if self.__m_showCount:
            self._drawCount(p, QRectF(c.x() + s * 1.45, c.y() - 16.0, self.width() - c.x() - s * 1.45, 32.0), now)
        p.end()

    def _drawHeart(self, p, c, s, liked):
        """
        :param p: QPainter
        :param c: QPointF
        :param s: qreal | float | int
        :param liked: bool
        :return:
        """
        path = heartPath(c, s)  # type: QPainterPath
        hc = self.__m_color  # type: QColor
        if liked:
            grad = QRadialGradient(QPointF(c.x() - s * 0.4, c.y() - s * 0.4), s * 1.8)  # type: QRadialGradient
            grad.setColorAt(0.0, hc.lighter(125))
            grad.setColorAt(1.0, hc.darker(115))
            p.setPen(QPen(hc.darker(140), max(1.2, s * 0.05)))
            p.setBrush(grad)
            p.drawPath(path)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 255, 255, 90))
            p.drawEllipse(QPointF(c.x() - s * 0.5, c.y() - s * 0.35), s * 0.18, s * 0.11)
        else:
            tc = QColor(self.palette().text().color())  # type: QColor
            line = QColor(hc) if self.__m_hovered else QColor(tc)  # type: QColor
            line.setAlpha(220 if self.__m_hovered else 130)
            fill = QColor(hc)  # type: QColor
            fill.setAlpha(35 if self.__m_hovered else 12)
            p.setPen(QPen(line, max(1.8, s * 0.08)))
            p.setBrush(fill)
            p.drawPath(path)

    def _drawCracked(self, p, c, s, since):
        """
        :param p: QPainter
        :param c: QPointF
        :param s: qreal | float | int
        :param since: (qreal | float | int) time since un-like
        :return:
        """
        gap = sin(clamp(since / 0.9, 0.0, 1.0) * pi) * s * 0.18  # type: float
        crack = QPainterPath()  # type: QPainterPath
        crack.moveTo(c.x(), c.y() - s * 0.45)
        for k, (dx, dy) in enumerate(((-0.12, -0.2), (0.1, 0.05), (-0.1, 0.3), (0.06, 0.55), (0.0, 0.95))):
            crack.lineTo(c.x() + dx * s, c.y() + dy * s)
        heart = heartPath(c, s)  # type: QPainterPath
        hc = QColor(self.__m_color)  # type: QColor
        for d in (-1.0, 1.0):
            half = QPainterPath()  # type: QPainterPath
            half.moveTo(c.x() + d * s * 2.0, c.y() - s * 2.0)
            half.lineTo(c.x(), c.y() - s * 2.0)
            half.connectPath(crack)
            half.lineTo(c.x(), c.y() + s * 2.0)
            half.lineTo(c.x() + d * s * 2.0, c.y() + s * 2.0)
            half.closeSubpath()
            piece = heart.intersected(half)  # type: QPainterPath
            p.save()
            p.translate(d * gap, 0)
            p.rotate(d * gap * 0.4)
            p.setPen(QPen(hc.darker(140), max(1.2, s * 0.05)))
            p.setBrush(hc.darker(105))
            p.drawPath(piece)
            p.restore()

    def _drawFace(self, p, c, s, liked, dizzy, cracking, now):
        """
        :param p: QPainter
        :param c: QPointF
        :param s: qreal | float | int
        :param liked: bool
        :param dizzy: bool
        :param cracking: bool
        :param now: qreal | float | int
        :return:
        """
        ink = QColor('#3A1020') if (liked or cracking) else QColor(self.palette().text().color())  # type: QColor
        if not (liked or cracking):
            ink.setAlpha(170)
        pen = QPen(ink, max(1.2, s * 0.07), Qt.SolidLine, Qt.RoundCap)  # type: QPen
        ex = s * 0.32  # type: float
        ey = c.y() - s * 0.08  # type: float
        if dizzy:
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            for d in (-1.0, 1.0):
                spiral = QPainterPath()  # type: QPainterPath
                for k in range(24):
                    a = k * 0.55 + now * 10.0 * d  # type: float
                    r = s * 0.006 * k  # type: float
                    pt = QPointF(c.x() + d * ex + cos(a) * r, ey + sin(a) * r)  # type: QPointF
                    if k == 0:
                        spiral.moveTo(pt)
                    else:
                        spiral.lineTo(pt)
                p.drawPath(spiral)
            p.drawEllipse(QPointF(c.x(), c.y() + s * 0.3), s * 0.07, s * 0.08)
            return
        if cracking:
            gap = sin(clamp((now - self.__m_unlikedAt) / 0.9, 0.0, 1.0) * pi) * s * 0.18  # type: float
            p.setPen(pen)
            for d in (-1.0, 1.0):
                x = c.x() + d * ex + d * gap  # type: float
                p.drawLine(QPointF(x - s * 0.1, ey), QPointF(x + s * 0.1, ey))
                tear = QColor('#5AB9FF')  # type: QColor
                p.setPen(Qt.NoPen)
                p.setBrush(tear)
                p.drawEllipse(QPointF(x + d * s * 0.04, ey + s * 0.12 + (now % 0.6) * s * 0.4), s * 0.05, s * 0.07)
                p.setPen(pen)
            return
        if liked:
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            for d in (-1.0, 1.0):
                p.drawArc(QRectF(c.x() + d * ex - s * 0.11, ey - s * 0.05, s * 0.22, s * 0.16), 20 * 16, 140 * 16)
            bl = QColor('#FFFFFF')  # type: QColor
            bl.setAlpha(70)
            p.setPen(Qt.NoPen)
            p.setBrush(bl)
            for d in (-1.0, 1.0):
                p.drawEllipse(QPointF(c.x() + d * s * 0.5, c.y() + s * 0.12), s * 0.11, s * 0.07)
            p.setPen(pen)
            p.setBrush(QColor('#7A1F35'))
            m = QPainterPath()  # type: QPainterPath
            m.moveTo(c.x() - s * 0.18, c.y() + s * 0.15)
            m.quadTo(c.x(), c.y() + s * 0.45, c.x() + s * 0.18, c.y() + s * 0.15)
            m.closeSubpath()
            p.drawPath(m)
        else:
            # Hopeful: looks up at you when hovered.
            look = -s * 0.04 if self.__m_hovered else 0.0  # type: float
            p.setPen(Qt.NoPen)
            p.setBrush(ink)
            for d in (-1.0, 1.0):
                p.drawEllipse(QPointF(c.x() + d * ex, ey + look), s * 0.06, s * (0.09 if self.__m_hovered else 0.07))
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            if self.__m_hovered:
                p.drawArc(QRectF(c.x() - s * 0.1, c.y() + s * 0.12, s * 0.2, s * 0.14), 200 * 16, 140 * 16)
            else:
                p.drawLine(QPointF(c.x() - s * 0.08, c.y() + s * 0.22), QPointF(c.x() + s * 0.08, c.y() + s * 0.22))

    def _drawCount(self, p, area, now):
        """
        :param p: QPainter
        :param area: QRectF
        :param now: qreal | float | int
        :return:
        """
        if area.width() < 20:
            return
        f = QFont(self.font())  # type: QFont
        f.setBold(True)
        f.setPointSizeF(13.0)
        p.setFont(f)
        tc = QColor(self.palette().text().color())  # type: QColor
        t = clamp((now - self.__m_countAt) / 0.3, 0.0, 1.0)  # type: float
        up = self.__m_count > self.__m_oldCount  # type: bool
        p.save()
        p.setClipRect(area)
        if t < 1.0:
            dy = area.height() * t  # type: float
            old = QColor(tc)  # type: QColor
            old.setAlpha(int(255 * (1.0 - t)))
            p.setPen(old)
            p.drawText(area.translated(0, -dy if up else dy), Qt.AlignLeft | Qt.AlignVCenter, str(self.__m_oldCount))
            p.setPen(self.__m_color if up else tc)
            p.drawText(area.translated(0, area.height() - dy if up else dy - area.height()), Qt.AlignLeft | Qt.AlignVCenter,
                       str(self.__m_count))
        else:
            p.setPen(self.__m_color if self.__m_liked else tc)
            p.drawText(area, Qt.AlignLeft | Qt.AlignVCenter, str(self.__m_count))
        p.restore()

    # ---------- Properties ----------
    liked = pyqtProperty(bool, fget=isLiked, fset=setLiked, notify=likedChanged)  # type: pyqtProperty
    count = pyqtProperty(int, fget=getCount, fset=setCount, notify=countChanged)  # type: pyqtProperty
    color = pyqtProperty(QColor, fget=getColor, fset=setColor)  # type: pyqtProperty
    showCount = pyqtProperty(bool, fget=isShowCount, fset=setShowCount)  # type: pyqtProperty
