# -*- coding: utf-8 -*-
"""
StarRatingWidget: a star rating control where every star has feelings. Hover previews the mood,
clicking sends a bouncy wave through the stars, a 1-star rating makes the empty stars cry and a
5-star rating gets all of them dancing with sparkles.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QRadialGradient
from ManyQt.QtWidgets import QWidget
from math import sin, cos, pi
from random import uniform


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


def starPath(c, r, inner=0.5, points=5):
    """
    :param c: (QPointF) center
    :param r: (qreal | float | int) outer radius
    :param inner: (qreal | float | int) inner radius ratio
    :param points: (int) number of spikes
    :return: QPainterPath
    """
    path = QPainterPath()  # type: QPainterPath
    for j in range(points * 2):
        rr = r if j % 2 == 0 else r * inner  # type: float
        a = -pi / 2.0 + j * pi / points  # type: float
        pt = QPointF(c.x() + cos(a) * rr, c.y() + sin(a) * rr)  # type: QPointF
        if j == 0:
            path.moveTo(pt)
        else:
            path.lineTo(pt)
    path.closeSubpath()
    return path


DEFAULT_LABELS = ['Awful', 'Not great', 'Okay', 'Great', 'Life-changing!']  # type: list[str]


class StarState(object):
    """
    Animation state of one star.
    """

    def __init__(self, scale=1.0, vel=0.0, kickAt=-1.0):
        """
        :param scale: (qreal | float | int) Bounce offset (1.0 = rest).
        :param vel: qreal | float | int
        :param kickAt: (qreal | float | int) Time in s of a pending bounce, < 0 when none.
        """
        self.scale = float(scale)  # type: float
        self.vel = float(vel)  # type: float
        self.kickAt = float(kickAt)  # type: float


class Particle(object):
    """
    A teardrop or a sparkle.
    """

    def __init__(self, x=0.0, y=0.0, vx=0.0, vy=0.0, life=1.0, kind=0):
        """
        :param x: qreal | float | int
        :param y: qreal | float | int
        :param vx: qreal | float | int
        :param vy: qreal | float | int
        :param life: (qreal | float | int) s
        :param kind: (int) 0 = tear, 1 = sparkle
        """
        self.x = float(x)  # type: float
        self.y = float(y)  # type: float
        self.vx = float(vx)  # type: float
        self.vy = float(vy)  # type: float
        self.life = float(life)  # type: float
        self.maxLife = float(life)  # type: float
        self.kind = int(kind)  # type: int


class StarRatingWidget(QWidget):
    """
    Emotional star rating control.
    """
    ratingChanged = pyqtSignal(int)  # type: pyqtSignal
    hovered = pyqtSignal(int)  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param rating: (int) 0 = not rated.
        :param maxRating: (int) Number of stars (3..10).
        :param starColor: QColor | Qt.GlobalColor | int | str | QString
        :param emptyColor: QColor | Qt.GlobalColor | int | str | QString
        :param labels: (list[str | unicode | QString]) One label per rating value, worst first.
        :param placeholder: (str | unicode | QString) Label shown while not rated.
        :param showLabel: bool
        :param allowClear: (bool) Clicking the current rating clears it.
        :param ratingChanged: callable | None
        :param hovered: callable | None
        :param args: any
        :param kwargs: any
        """
        rating = kwargs.pop('rating', 0)  # type: int
        maxRating = kwargs.pop('maxRating', 5)  # type: int
        starColor = kwargs.pop('starColor', '#FFC93C')  # type: QColor
        emptyColor = kwargs.pop('emptyColor', '#C9CCD6')  # type: QColor
        labels = kwargs.pop('labels', DEFAULT_LABELS)  # type: list[str]
        placeholder = kwargs.pop('placeholder', 'Rate us (we have feelings)')  # type: str
        showLabel = kwargs.pop('showLabel', True)  # type: bool
        allowClear = kwargs.pop('allowClear', True)  # type: bool
        ratingChanged = kwargs.pop('ratingChanged', None)  # type: callable | None
        hovered = kwargs.pop('hovered', None)  # type: callable | None
        super(StarRatingWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_maxRating = int(clamp(int(maxRating), 3, 10))  # type: int
        self.__m_rating = int(clamp(int(rating), 0, self.__m_maxRating))  # type: int
        self.__m_starColor = QColor(starColor)  # type: QColor
        self.__m_emptyColor = QColor(emptyColor)  # type: QColor
        self.__m_labels = list(labels) or list(DEFAULT_LABELS)  # type: list[str]
        self.__m_placeholder = placeholder  # type: str
        self.__m_showLabel = bool(showLabel)  # type: bool
        self.__m_allowClear = bool(allowClear)  # type: bool
        if callable(ratingChanged):
            self.ratingChanged.connect(ratingChanged)
        if callable(hovered):
            self.hovered.connect(hovered)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.PointingHandCursor)
        # State.
        self.__m_hover = 0  # type: int
        self.__m_stars = [StarState() for _ in range(self.__m_maxRating)]  # type: list[StarState]
        self.__m_particles = []  # type: list[Particle]
        self.__m_spawn = 0.0  # type: float
        self.__m_starRects = []  # type: list[QRectF]
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

    def _shown(self):
        """
        :return: (int) Rating currently displayed (hover preview wins).
        """
        return self.__m_hover if self.__m_hover > 0 else self.__m_rating

    def _layout(self):
        """
        :return: (tuple) star radius float, list of centres list[QPointF]
        """
        n = self.__m_maxRating  # type: int
        w = float(self.width())  # type: float
        h = float(self.height())  # type: float
        labelH = 30.0 if self.__m_showLabel else 0.0  # type: float
        r = max(6.0, min(w / (n * 2.35), (h - labelH - 16.0) / 2.3))  # type: float
        gap = r * 2.35  # type: float
        x0 = (w - gap * (n - 1)) / 2.0  # type: float
        cy = (h - labelH) / 2.0 + r * 0.08  # type: float
        return r, [QPointF(x0 + i * gap, cy) for i in range(n)]

    def _indexAt(self, pos):
        """
        :param pos: QPointF
        :return: (int) 1-based star index under pos, 0 if none.
        """
        r, centres = self._layout()
        for i, c in enumerate(centres):
            if abs(pos.x() - c.x()) <= r * 1.17 and abs(pos.y() - c.y()) <= r * 1.3:
                return i + 1
        return 0

    def _labelFor(self, value):
        """
        :param value: int
        :return: str | unicode | QString
        """
        if value <= 0:
            return self.__m_placeholder
        n = len(self.__m_labels)  # type: int
        idx = int(round((value - 1) * (n - 1) / float(max(1, self.__m_maxRating - 1))))  # type: int
        return self.__m_labels[int(clamp(idx, 0, n - 1))]

    def _wave(self):
        """
        Schedule a staggered bounce through the stars.
        :return:
        """
        now = self._now()  # type: float
        for i, st in enumerate(self.__m_stars):
            st.kickAt = now + i * 0.06

    # ---------- Public API ----------
    def getRating(self):
        """
        :return: int
        """
        return self.__m_rating

    @pyqtSlot(int)
    def setRating(self, rating):
        """
        :param rating: int
        :return:
        """
        rating = int(clamp(int(rating), 0, self.__m_maxRating))  # type: int
        if rating != self.__m_rating:
            self.__m_rating = rating  # type: int
            self._wave()
            self.ratingChanged.emit(rating)
            self.update()

    def getMaxRating(self):
        """
        :return: int
        """
        return self.__m_maxRating

    @pyqtSlot(int)
    def setMaxRating(self, maxRating):
        """
        :param maxRating: (int) 3..10
        :return:
        """
        maxRating = int(clamp(int(maxRating), 3, 10))  # type: int
        if maxRating != self.__m_maxRating:
            self.__m_maxRating = maxRating  # type: int
            self.__m_stars = [StarState() for _ in range(maxRating)]  # type: list[StarState]
            self.setRating(min(self.__m_rating, maxRating))
            self.update()

    def getStarColor(self):
        """
        :return: QColor
        """
        return self.__m_starColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setStarColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        if self.__m_starColor != color:
            self.__m_starColor = color  # type: QColor
            self.update()

    def getEmptyColor(self):
        """
        :return: QColor
        """
        return self.__m_emptyColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setEmptyColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        if self.__m_emptyColor != color:
            self.__m_emptyColor = color  # type: QColor
            self.update()

    def getLabels(self):
        """
        :return: list[str | unicode | QString]
        """
        return list(self.__m_labels)

    @pyqtSlot(list)
    def setLabels(self, labels):
        """
        :param labels: list[str]
        :return:
        """
        self.__m_labels = list(labels) or list(DEFAULT_LABELS)  # type: list[str]
        self.update()

    def getPlaceholder(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_placeholder

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setPlaceholder(self, placeholder):
        """
        :param placeholder: str | unicode | QString
        :return:
        """
        self.__m_placeholder = placeholder  # type: str
        self.update()

    def isShowLabel(self):
        """
        :return: bool
        """
        return self.__m_showLabel

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setShowLabel(self, showLabel):
        """
        :param showLabel: bool
        :return:
        """
        self.__m_showLabel = bool(showLabel)  # type: bool
        self.update()

    def isAllowClear(self):
        """
        :return: bool
        """
        return self.__m_allowClear

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setAllowClear(self, allowClear):
        """
        :param allowClear: bool
        :return:
        """
        self.__m_allowClear = bool(allowClear)  # type: bool

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
        return QSize(150, 50)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(StarRatingWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(StarRatingWidget, self).hideEvent(event)

    def mouseMoveEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        idx = self._indexAt(eventPos(e))  # type: int
        if idx != self.__m_hover:
            self.__m_hover = idx  # type: int
            if idx > 0:
                self.__m_stars[idx - 1].vel += 4.0
            self.hovered.emit(idx)
        super(StarRatingWidget, self).mouseMoveEvent(e)

    def leaveEvent(self, e):
        """
        :param e: QEvent
        :return:
        """
        self.__m_hover = 0  # type: int
        self.hovered.emit(0)
        super(StarRatingWidget, self).leaveEvent(e)

    def mouseReleaseEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if e.button() == Qt.LeftButton:
            idx = self._indexAt(eventPos(e))  # type: int
            if idx > 0:
                if idx == self.__m_rating and self.__m_allowClear:
                    self.setRating(0)
                else:
                    self.setRating(idx)
        super(StarRatingWidget, self).mouseReleaseEvent(e)

    def keyPressEvent(self, e):
        """
        :param e: QKeyEvent
        :return:
        """
        k = e.key()  # type: int
        if k in (Qt.Key_Right, Qt.Key_Up):
            self.setRating(self.__m_rating + 1)
        elif k in (Qt.Key_Left, Qt.Key_Down):
            self.setRating(self.__m_rating - 1)
        elif Qt.Key_0 <= k <= Qt.Key_9:
            self.setRating(k - Qt.Key_0)
        else:
            super(StarRatingWidget, self).keyPressEvent(e)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        for st in self.__m_stars:
            if 0 <= st.kickAt <= now:
                st.vel += 9.0
                st.kickAt = -1.0
            st.vel += ((1.0 - st.scale) * 320.0 - st.vel * 13.0) * dt
            st.scale += st.vel * dt
        # Tears for a 1-star rating, sparkles for a perfect score.
        shown = self._shown()  # type: int
        r, centres = self._layout()
        if shown == 1 or shown == self.__m_maxRating:
            self.__m_spawn += dt * (6.0 if shown == 1 else 9.0)
            while self.__m_spawn > 1.0:
                self.__m_spawn -= 1.0
                if shown == 1:
                    i = int(uniform(1, self.__m_maxRating))  # type: int
                    c = centres[min(i, len(centres) - 1)]  # type: QPointF
                    side = -1.0 if uniform(0, 1) < 0.5 else 1.0  # type: float
                    self.__m_particles.append(Particle(c.x() + side * r * 0.24, c.y() + r * 0.02,
                                                       side * uniform(5, 20), uniform(5, 25), 0.9, 0))
                else:
                    c = centres[int(uniform(0, len(centres) - 0.01))]  # type: QPointF
                    a = uniform(0, 2.0 * pi)  # type: float
                    self.__m_particles.append(Particle(c.x() + cos(a) * r * 1.2, c.y() + sin(a) * r * 1.2,
                                                       0, -uniform(10, 30), 0.7, 1))
        alive = []  # type: list[Particle]
        for pt in self.__m_particles:
            if pt.kind == 0:
                pt.vy += 220.0 * dt
            pt.x += pt.vx * dt
            pt.y += pt.vy * dt
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
        r, centres = self._layout()
        shown = self._shown()  # type: int
        n = self.__m_maxRating  # type: int
        perfect = shown == n  # type: bool
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        for i, c in enumerate(centres):
            st = self.__m_stars[i]  # type: StarState
            filled = i < shown  # type: bool
            p.save()
            p.translate(c)
            # Dance when perfect, otherwise just the bounce.
            hop = 0.0  # type: float
            if perfect:
                ph = now * 9.0 + i * 0.9  # type: float
                p.rotate(12.0 * sin(ph))
                hop = -abs(sin(ph)) * r * 0.22  # type: float
            p.translate(0, hop)
            s = max(0.3, st.scale)  # type: float
            p.scale(s, s)
            self._drawStar(p, r, i, filled, shown, now)
            p.restore()
        # Particles.
        p.setPen(Qt.NoPen)
        for pt in self.__m_particles:
            a = clamp(pt.life / pt.maxLife, 0.0, 1.0)  # type: float
            if pt.kind == 0:
                col = QColor('#5AB9FF')  # type: QColor
                col.setAlpha(int(230 * a))
                drop = QPainterPath()  # type: QPainterPath
                ds = max(2.0, r * 0.09)  # type: float
                drop.moveTo(pt.x, pt.y - ds * 1.6)
                drop.quadTo(pt.x + ds, pt.y, pt.x, pt.y + ds)
                drop.quadTo(pt.x - ds, pt.y, pt.x, pt.y - ds * 1.6)
                p.fillPath(drop, col)
            else:
                col = QColor('#FFF3B0')  # type: QColor
                col.setAlpha(int(255 * a))
                p.fillPath(starPath(QPointF(pt.x, pt.y), r * 0.16 * (0.5 + a), 0.3, 4), col)
        # Label.
        if self.__m_showLabel:
            f = QFont(self.font())  # type: QFont
            f.setPointSizeF(10.5)
            f.setBold(shown > 0)
            p.setFont(f)
            tc = QColor(self.palette().text().color())  # type: QColor
            if shown == 0:
                tc.setAlpha(150)
            p.setPen(tc)
            top = centres[0].y() + r * 1.25 if centres else 0.0  # type: float
            p.drawText(QRectF(0, top, self.width(), 26), Qt.AlignHCenter | Qt.AlignTop, self._labelFor(shown))
        p.end()

    def _drawStar(self, p, r, i, filled, shown, now):
        """
        :param p: QPainter
        :param r: (qreal | float | int) Radius.
        :param i: (int) star index
        :param filled: bool
        :param shown: (int) Displayed rating.
        :param now: qreal | float | int
        :return:
        """
        base = self.__m_starColor if filled else self.__m_emptyColor  # type: QColor
        path = starPath(QPointF(0, 0), r, 0.52)  # type: QPainterPath
        grad = QRadialGradient(QPointF(-r * 0.3, -r * 0.35), r * 1.6)  # type: QRadialGradient
        grad.setColorAt(0.0, base.lighter(118))
        grad.setColorAt(1.0, base.darker(112))
        pen = QPen(base.darker(135), max(1.5, r * 0.12))  # type: QPen
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.setBrush(grad)
        p.drawPath(path)
        ink = QColor('#3A2E1F') if filled else QColor('#6B6F7C')  # type: QColor
        fp = QPen(ink, max(1.0, r * 0.075), Qt.SolidLine, Qt.RoundCap)  # type: QPen
        ex = r * 0.22  # type: float
        ey = -r * 0.04  # type: float
        n = self.__m_maxRating  # type: int
        if filled:
            perfect = shown == n  # type: bool
            # Happy closed eyes when perfect, nervous dots for a 1-star score.
            if perfect:
                p.setPen(fp)
                p.setBrush(Qt.NoBrush)
                for d in (-1.0, 1.0):
                    p.drawArc(QRectF(d * ex - r * 0.09, ey - r * 0.04, r * 0.18, r * 0.16), 0, 180 * 16)
            else:
                p.setPen(Qt.NoPen)
                p.setBrush(ink)
                for d in (-1.0, 1.0):
                    p.drawEllipse(QPointF(d * ex, ey), r * 0.065, r * 0.085)
            mood = shown / float(n)  # type: float
            p.setPen(fp)
            mouth = QPainterPath()  # type: QPainterPath
            mw = r * (0.16 + 0.12 * mood)  # type: float
            my = r * 0.17  # type: float
            mouth.moveTo(-mw, my)
            if shown == 1:
                # Awkward wavy smile.
                mouth.cubicTo(-mw * 0.3, my - r * 0.06, mw * 0.3, my + r * 0.06, mw, my)
                p.setBrush(Qt.NoBrush)
            else:
                mouth.quadTo(0, my + r * (0.08 + 0.22 * mood), mw, my)
                if perfect:
                    mouth.closeSubpath()
                    p.setBrush(QColor('#C2412D'))
                else:
                    p.setBrush(Qt.NoBrush)
            p.drawPath(mouth)
            if mood > 0.5:
                bc = QColor('#FF8A7A')  # type: QColor
                bc.setAlpha(140)
                p.setPen(Qt.NoPen)
                p.setBrush(bc)
                for d in (-1.0, 1.0):
                    p.drawEllipse(QPointF(d * r * 0.36, r * 0.12), r * 0.08, r * 0.05)
        else:
            # Empty stars: hopeful when unrated, sad when left out.
            p.setPen(Qt.NoPen)
            p.setBrush(ink)
            sad = shown > 0  # type: bool
            for d in (-1.0, 1.0):
                if sad:
                    p.setPen(fp)
                    # Sad brows: inner ends raised.
                    p.drawLine(QPointF(d * (ex + r * 0.09), ey - r * 0.12),
                               QPointF(d * (ex - r * 0.07), ey - r * 0.19))
                    p.setPen(Qt.NoPen)
                p.drawEllipse(QPointF(d * ex, ey), r * 0.055, r * 0.07)
            p.setPen(fp)
            p.setBrush(Qt.NoBrush)
            mouth = QPainterPath()  # type: QPainterPath
            my = r * 0.2  # type: float
            if sad:
                depth = 0.12 if shown == 1 else 0.07  # type: float
                mouth.moveTo(-r * 0.13, my + r * 0.04)
                mouth.quadTo(0, my - r * depth, r * 0.13, my + r * 0.04)
            else:
                wob = sin(now * 3.0 + i) * r * 0.02  # type: float
                mouth.moveTo(-r * 0.1, my)
                mouth.quadTo(0, my + r * 0.06 + wob, r * 0.1, my)
            p.drawPath(mouth)

    # ---------- Properties ----------
    rating = pyqtProperty(int, fget=getRating, fset=setRating, notify=ratingChanged)  # type: pyqtProperty
    maxRating = pyqtProperty(int, fget=getMaxRating, fset=setMaxRating)  # type: pyqtProperty
    starColor = pyqtProperty(QColor, fget=getStarColor, fset=setStarColor)  # type: pyqtProperty
    emptyColor = pyqtProperty(QColor, fget=getEmptyColor, fset=setEmptyColor)  # type: pyqtProperty
    labels = pyqtProperty('QStringList', fget=getLabels, fset=setLabels)  # type: pyqtProperty
    placeholder = pyqtProperty('QString', fget=getPlaceholder, fset=setPlaceholder)  # type: pyqtProperty
    showLabel = pyqtProperty(bool, fget=isShowLabel, fset=setShowLabel)  # type: pyqtProperty
    allowClear = pyqtProperty(bool, fget=isAllowClear, fset=setAllowClear)  # type: pyqtProperty
