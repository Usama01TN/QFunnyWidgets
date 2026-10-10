# -*- coding: utf-8 -*-
"""
AntBreadcrumbWidget: breadcrumb navigation made of actual bread crumbs, maintained by ants. A column
of ants marches underneath the trail; navigate up and the crumbs you leave behind are lifted and
carried off by ants; go deeper and new crumbs are carried in and set down in place.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QFontMetricsF
from ManyQt.QtWidgets import QWidget
from math import sin, cos, pi
from random import Random

IN, IDLE, OUT = range(3)  # type: tuple
CARRY_SPEED = 260.0  # type: float
GAP = 24.0  # type: float


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


class Crumb(object):
    """
    One crumb of the trail.
    """

    def __init__(self, text='', x=0.0, state=IDLE, delay=0.0):
        """
        :param text: str | unicode | QString
        :param x: (qreal | float | int) current left edge
        :param state: (int) IN, IDLE or OUT
        :param delay: (qreal | float | int) s to wait before being carried
        """
        self.text = text  # type: str
        self.x = float(x)  # type: float
        self.targetX = float(x)  # type: float
        self.width = 60.0  # type: float
        self.state = int(state)  # type: int
        self.delay = float(delay)  # type: float
        self.lift = 0.0  # type: float
        self.seed = sum(ord(ch) for ch in text) or 7  # type: int


class AntBreadcrumbWidget(QWidget):
    """
    Breadcrumb trail with an ant logistics department.
    """
    crumbClicked = pyqtSignal(int)  # type: pyqtSignal
    pathChanged = pyqtSignal(list)  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param path: (list[str | unicode | QString]) Breadcrumb segments, root first.
        :param crumbColor: QColor | Qt.GlobalColor | int | str | QString
        :param antColor: QColor | Qt.GlobalColor | int | str | QString
        :param marchingAnts: (bool) Decorative ants marching under the trail.
        :param crumbClicked: callable | None
        :param pathChanged: callable | None
        :param args: any
        :param kwargs: any
        """
        path = kwargs.pop('path', ['Home', 'Projects', 'QFunnyWidgets'])  # type: list[str]
        crumbColor = kwargs.pop('crumbColor', '#E9B872')  # type: QColor
        antColor = kwargs.pop('antColor', '#2B1A12')  # type: QColor
        marchingAnts = kwargs.pop('marchingAnts', True)  # type: bool
        crumbClicked = kwargs.pop('crumbClicked', None)  # type: callable | None
        pathChanged = kwargs.pop('pathChanged', None)  # type: callable | None
        super(AntBreadcrumbWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_crumbColor = QColor(crumbColor)  # type: QColor
        self.__m_antColor = QColor(antColor)  # type: QColor
        self.__m_marching = bool(marchingAnts)  # type: bool
        if callable(crumbClicked):
            self.crumbClicked.connect(crumbClicked)
        if callable(pathChanged):
            self.pathChanged.connect(pathChanged)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        # State.
        self.__m_crumbs = [Crumb(t) for t in path]  # type: list[Crumb]
        self.__m_leaving = []  # type: list[Crumb]
        self.__m_hover = -1  # type: int
        self.__m_layoutDone = False  # type: bool
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

    def _font(self, bold=False):
        """
        :param bold: bool
        :return: QFont
        """
        f = QFont(self.font())  # type: QFont
        f.setPointSizeF(9.5)
        f.setBold(bold)
        return f

    def _layoutCrumbs(self, snap=False):
        """
        Compute target positions/widths, eliding text if the trail is too long.

        :param snap: (bool) Jump idle crumbs to their targets.
        :return:
        """
        n = len(self.__m_crumbs)  # type: int
        if not n:
            return
        avail = self.width() - 12.0 - GAP * (n - 1)  # type: float
        natural = []  # type: list[float]
        for i, c in enumerate(self.__m_crumbs):
            fm = QFontMetricsF(self._font(i == n - 1))  # type: QFontMetricsF
            tw = fm.horizontalAdvance(c.text) if hasattr(fm, 'horizontalAdvance') else fm.width(c.text)  # type: float
            natural.append(tw + 26.0)
        # Too long for the space: short crumbs keep their size, long ones share what is left (water-filling).
        widths = list(natural)  # type: list[float]
        if sum(natural) > avail:
            remaining = avail  # type: float
            left = n  # type: int
            for i in sorted(range(n), key=lambda k: natural[k]):
                share = max(36.0, remaining / left)  # type: float
                widths[i] = min(natural[i], share)
                remaining -= widths[i]
                left -= 1
        x = 6.0  # type: float
        for c, wd in zip(self.__m_crumbs, widths):
            c.width = wd
            c.targetX = x  # type float
            if snap and c.state == IDLE:
                c.x = x
            x += c.width + GAP

    def _crumbRect(self, c):
        """
        :param c: Crumb
        :return: QRectF
        """
        h = float(self.height())  # type: float
        ch = min(30.0, h - 16.0)  # type: float
        return QRectF(c.x, (h - ch) / 2.0 - 4.0 - c.lift, c.width, ch)

    # ---------- Public API ----------
    def getPath(self):
        """
        :return: list[str | unicode | QString]
        """
        return [c.text for c in self.__m_crumbs]

    @pyqtSlot(list)
    def setPath(self, path):
        """
        Change the trail: removed crumbs are carried away, new ones carried in.

        :param path: list[str]
        :return:
        """
        path = [str(t) for t in path]  # type: list[str]
        old = self.getPath()  # type: list[str]
        if path == old:
            return
        keep = 0  # type: int
        while keep < min(len(path), len(old)) and path[keep] == old[keep]:
            keep += 1
        for k, c in enumerate(self.__m_crumbs[keep:]):
            c.state = OUT  # type int
            c.delay = k * 0.08  # type float
            self.__m_leaving.append(c)
        self.__m_crumbs = self.__m_crumbs[:keep]  # type: list[Crumb]
        start = self.width() + 20.0  # type: float
        for k, t in enumerate(path[keep:]):
            self.__m_crumbs.append(Crumb(t, x=start + k * 90.0, state=IN, delay=0.25 + k * 0.15))
        self._layoutCrumbs()
        self.pathChanged.emit(self.getPath())
        self.update()

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def push(self, name):
        """
        Go one level deeper.

        :param name: str | unicode | QString
        :return:
        """
        self.setPath(self.getPath() + [name])

    @pyqtSlot(int)
    def navigateTo(self, index):
        """
        Go back up to crumb index (everything after it is carried away).

        :param index: int
        :return:
        """
        index = int(clamp(int(index), 0, len(self.__m_crumbs) - 1))  # type: int
        self.setPath(self.getPath()[:index + 1])

    def getCrumbColor(self):
        """
        :return: QColor
        """
        return self.__m_crumbColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setCrumbColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        self.__m_crumbColor = color  # type: QColor
        self.update()

    def getAntColor(self):
        """
        :return: QColor
        """
        return self.__m_antColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setAntColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        self.__m_antColor = color  # type: QColor
        self.update()

    def isMarchingAnts(self):
        """
        :return: bool
        """
        return self.__m_marching

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setMarchingAnts(self, marchingAnts):
        """
        :param marchingAnts: bool
        :return:
        """
        self.__m_marching = bool(marchingAnts)  # type: bool

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(420, 56)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(160, 44)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(AntBreadcrumbWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(AntBreadcrumbWidget, self).hideEvent(event)

    def resizeEvent(self, event):
        """
        :param event: QResizeEvent
        :return:
        """
        super(AntBreadcrumbWidget, self).resizeEvent(event)
        self._layoutCrumbs(snap=True)

    def mouseMoveEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        hover = -1  # type: int
        for i, c in enumerate(self.__m_crumbs[:-1]):
            if c.state == IDLE and self._crumbRect(c).contains(eventPos(e)):
                hover = i  # type: int
        if hover != self.__m_hover:
            self.__m_hover = hover  # type: int
            self.setCursor(Qt.PointingHandCursor if hover >= 0 else Qt.ArrowCursor)
        super(AntBreadcrumbWidget, self).mouseMoveEvent(e)

    def leaveEvent(self, e):
        """
        :param e: QEvent
        :return:
        """
        self.__m_hover = -1  # type: int
        super(AntBreadcrumbWidget, self).leaveEvent(e)

    def mouseReleaseEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if e.button() == Qt.LeftButton:
            for i, c in enumerate(self.__m_crumbs[:-1]):
                if c.state == IDLE and self._crumbRect(c).contains(eventPos(e)):
                    self.crumbClicked.emit(i)
                    self.navigateTo(i)
                    break
        super(AntBreadcrumbWidget, self).mouseReleaseEvent(e)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        if not self.__m_layoutDone and self.width() > 0:
            self._layoutCrumbs(snap=True)
            self.__m_layoutDone = True  # type: bool
        for c in self.__m_crumbs:
            if c.delay > 0:
                c.delay -= dt
                continue
            if c.state == IN:
                c.lift = 4.0  # type float
                c.x = max(c.targetX, c.x - CARRY_SPEED * dt)
                if c.x <= c.targetX + 0.5:
                    c.state = IDLE  # type int
            else:
                c.lift = max(0.0, c.lift - dt * 30.0)
                c.x += (c.targetX - c.x) * min(1.0, dt * 10.0)  # re-flow after siblings change
        alive = []  # type: list[Crumb]
        for c in self.__m_leaving:
            if c.delay > 0:
                c.delay -= dt
                c.lift = min(5.0, c.lift + dt * 40.0)
            else:
                c.lift = 5.0  # type float
                c.x += CARRY_SPEED * dt
            if c.x < self.width() + 30:
                alive.append(c)
        self.__m_leaving = alive  # type: list[Crumb]
        self.update()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        now = self._now()  # type: float
        h = float(self.height())  # type: float
        ground = h - 7.0  # type: float
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        # Marching ants underneath (crumbs are painted over them).
        if self.__m_marching:
            span = self.width() + 40.0  # type: float
            for k in range(7):
                x = ((now * 28.0 + k * span / 7.0) % span) - 20.0  # type: float
                self._drawAnt(p, QPointF(x, ground), now * 12.0 + k, 1.0)
        n = len(self.__m_crumbs)  # type: int
        # Separators.
        sep = QColor(self.palette().text().color())  # type: QColor
        sep.setAlpha(110)
        p.setPen(QPen(sep, 1.6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        for c in self.__m_crumbs[:-1]:
            if c.state != IDLE:
                continue
            r = self._crumbRect(c)  # type: QRectF
            sx = r.right() + GAP / 2.0  # type: float
            cy = r.center().y()  # type: float
            p.drawLine(QPointF(sx - 3, cy - 5), QPointF(sx + 2, cy))
            p.drawLine(QPointF(sx + 2, cy), QPointF(sx - 3, cy + 5))
        for i, c in enumerate(self.__m_crumbs):
            self._drawCrumb(p, c, i == n - 1, i == self.__m_hover, now)
        for c in self.__m_leaving:
            self._drawCrumb(p, c, False, False, now)
        p.end()

    def _drawCrumb(self, p, c, current, hovered, now):
        """
        :param p: QPainter
        :param c: Crumb
        :param current: (bool) last crumb (you are here)
        :param hovered: bool
        :param now: qreal | float | int
        :return:
        """
        r = self._crumbRect(c)  # type: QRectF
        if r.right() < -10 or r.left() > self.width() + 10:
            return
        carried = c.state in (IN, OUT) and c.delay <= 0  # type: bool
        # Ants carrying it: under the crumb, legs going.
        if carried:
            for k in range(3):
                ax = r.left() + r.width() * (0.2 + 0.3 * k)  # type: float
                self._drawAnt(p, QPointF(ax, r.bottom() + 5.0), now * 18.0 + k, 1.0)
        rnd = Random(c.seed)  # type: Random
        col = self.__m_crumbColor.lighter(110) if hovered else self.__m_crumbColor  # type: QColor
        if current:
            col = col.lighter(106)  # type: QColor
        # Slightly lumpy crumb outline.
        path = QPainterPath()  # type: QPainterPath
        steps = 22  # type: int
        cx, cy = r.center().x(), r.center().y()
        rx, ry = r.width() / 2.0, r.height() / 2.0
        for k in range(steps + 1):
            a = k / float(steps) * 2.0 * pi  # type: float
            bump = 1.0 + rnd.uniform(-0.04, 0.04)  # type: float
            # Superellipse-ish so long crumbs stay pill shaped.
            sx = (abs(cos(a)) ** 0.45) * (1 if cos(a) >= 0 else -1)  # type: float
            sy = (abs(sin(a)) ** 0.45) * (1 if sin(a) >= 0 else -1)  # type: float
            pt = QPointF(cx + sx * rx * bump, cy + sy * ry * bump)  # type: QPointF
            if k == 0:
                path.moveTo(pt)
            else:
                path.lineTo(pt)
        path.closeSubpath()
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 40))
        p.drawPath(path.translated(0, 2))
        p.setPen(QPen(QColor('#A0682C'), 1.4))
        p.setBrush(col)
        p.drawPath(path)
        # Sesame / texture dots.
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 245, 220, 150))
        for k in range(max(2, int(r.width() / 22))):
            p.drawEllipse(QPointF(r.left() + rnd.uniform(8, r.width() - 8), r.top() + rnd.uniform(4, 8)), 1.6, 1.0)
        f = self._font(current)  # type: QFont
        p.setFont(f)
        p.setPen(QColor('#4A2A10'))
        fm = QFontMetricsF(f)  # type: QFontMetricsF
        p.drawText(r.adjusted(10, 0, -10, 0), Qt.AlignCenter, fm.elidedText(c.text, Qt.ElideMiddle, r.width() - 20))
        if current and not carried:
            # "You are here" flag planted by the ants.
            fx = r.right() - 6.0  # type: float
            p.setPen(QPen(QColor('#5A3A20'), 1.2))
            p.drawLine(QPointF(fx, r.top() + 2), QPointF(fx, r.top() - 9))
            flag = QPainterPath()  # type: QPainterPath
            wave = sin(now * 6.0) * 1.2  # type: float
            flag.moveTo(fx, r.top() - 9)
            flag.lineTo(fx + 8, r.top() - 7 + wave)
            flag.lineTo(fx, r.top() - 4)
            flag.closeSubpath()
            p.setPen(Qt.NoPen)
            p.setBrush(QColor('#E63946'))
            p.drawPath(flag)

    def _drawAnt(self, p, c, phase, scale):
        """
        Tiny ant walking right.

        :param p: QPainter
        :param c: (QPointF) feet position
        :param phase: (qreal | float | int) leg phase
        :param scale: qreal | float | int
        :return:
        """
        ac = self.__m_antColor  # type: QColor
        s = 4.0 * scale  # type: float
        y = c.y() - s * 0.9  # type: float
        p.setPen(QPen(ac, 0.9, Qt.SolidLine, Qt.RoundCap))
        for k, lx in enumerate((-s * 0.4, 0.0, s * 0.4)):
            sw = sin(phase + k * 2.1) * s * 0.35  # type: float
            p.drawLine(QPointF(c.x() + lx, y), QPointF(c.x() + lx + sw, c.y()))
        p.drawLine(QPointF(c.x() + s * 1.25, y - s * 0.3), QPointF(c.x() + s * 1.7, y - s * 0.9))
        p.setPen(Qt.NoPen)
        p.setBrush(ac)
        p.drawEllipse(QPointF(c.x() - s * 0.75, y), s * 0.6, s * 0.45)
        p.drawEllipse(QPointF(c.x(), y), s * 0.35, s * 0.3)
        p.drawEllipse(QPointF(c.x() + s * 0.8, y - s * 0.1), s * 0.4, s * 0.35)

    # ---------- Properties ----------
    path = pyqtProperty('QStringList', fget=getPath, fset=setPath)  # type: pyqtProperty
    crumbColor = pyqtProperty(QColor, fget=getCrumbColor, fset=setCrumbColor)  # type: pyqtProperty
    antColor = pyqtProperty(QColor, fget=getAntColor, fset=setAntColor)  # type: pyqtProperty
    marchingAnts = pyqtProperty(bool, fget=isMarchingAnts, fset=setMarchingAnts)  # type: pyqtProperty

