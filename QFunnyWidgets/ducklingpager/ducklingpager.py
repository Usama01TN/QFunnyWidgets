# -*- coding: utf-8 -*-
"""
DucklingPagerWidget: a carousel page indicator where the pages are lily pads and the current page is
wherever mother duck is sitting. Change page and she swims over (waddling), her ducklings paddling
after her in a line; she quacks when she arrives. Click a pad, use the arrow keys or the wheel.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont
from ManyQt.QtWidgets import QWidget
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


class Swimmer(object):
    """
    Position / velocity of one duck.
    """

    def __init__(self, x=0.0, vx=0.0):
        """
        :param x: qreal | float | int
        :param vx: qreal | float | int
        """
        self.x = float(x)  # type: float
        self.vx = float(vx)  # type: float


class DucklingPagerWidget(QWidget):
    """
    Page indicator with a duck family.
    """
    currentChanged = pyqtSignal(int)  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param count: (int) Number of pages (2..12).
        :param current: (int) Current page index.
        :param ducklings: (int) Number of ducklings (0..6).
        :param wrap: (bool) next() on the last page goes back to the first.
        :param duckColor: QColor | Qt.GlobalColor | int | str | QString
        :param ducklingColor: QColor | Qt.GlobalColor | int | str | QString
        :param padColor: QColor | Qt.GlobalColor | int | str | QString
        :param currentChanged: callable | None
        :param args: any
        :param kwargs: any
        """
        count = kwargs.pop('count', 5)  # type: int
        current = kwargs.pop('current', 0)  # type: int
        ducklings = kwargs.pop('ducklings', 3)  # type: int
        wrap = kwargs.pop('wrap', True)  # type: bool
        duckColor = kwargs.pop('duckColor', '#F4F1E6')  # type: QColor
        ducklingColor = kwargs.pop('ducklingColor', '#FFD43B')  # type: QColor
        padColor = kwargs.pop('padColor', '#5FB37A')  # type: QColor
        currentChanged = kwargs.pop('currentChanged', None)  # type: callable | None
        super(DucklingPagerWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_count = int(clamp(int(count), 2, 12))  # type: int
        self.__m_current = int(clamp(int(current), 0, self.__m_count - 1))  # type: int
        self.__m_ducklings = int(clamp(int(ducklings), 0, 6))  # type: int
        self.__m_wrap = bool(wrap)  # type: bool
        self.__m_duckColor = QColor(duckColor)  # type: QColor
        self.__m_ducklingColor = QColor(ducklingColor)  # type: QColor
        self.__m_padColor = QColor(padColor)  # type: QColor
        if callable(currentChanged):
            self.currentChanged.connect(currentChanged)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.PointingHandCursor)
        # State.
        self.__m_ducks = []  # type: list[Swimmer]  # [mother, duckling1, ...]
        self.__m_facing = 1.0  # type: float
        self.__m_quackAt = -10.0  # type: float
        self.__m_moving = False  # type: bool
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

    def _layout(self):
        """
        :return: (tuple) pad xs list[float], water y float, pad radius float, duck size float
        """
        n = self.__m_count  # type: int
        w = float(self.width())  # type: float
        h = float(self.height())  # type: float
        gap = min((w - 110.0) / max(1, n - 1), 70.0)  # type: float  # side room for the ducks
        x0 = w / 2.0 - gap * (n - 1) / 2.0  # type: float
        y = h * 0.66  # type: float
        padR = clamp(gap * 0.32, 7.0, 20.0)  # type: float
        size = clamp(gap * 0.6, 16.0, 40.0)  # type: float
        return [x0 + i * gap for i in range(n)], y, padR, size

    def _ensureDucks(self):
        """
        :return:
        """
        if len(self.__m_ducks) != self.__m_ducklings + 1:
            xs, y, padR, size = self._layout()
            mx = xs[self.__m_current]  # type: float
            self.__m_ducks = [Swimmer(mx - self.__m_facing * k * size * 0.75) for k in range(self.__m_ducklings + 1)]

    # ---------- Public API ----------
    @pyqtSlot()
    def next(self):
        """
        :return:
        """
        if self.__m_current + 1 < self.__m_count:
            self.setCurrent(self.__m_current + 1)
        elif self.__m_wrap:
            self.setCurrent(0)

    @pyqtSlot()
    def previous(self):
        """
        :return:
        """
        if self.__m_current > 0:
            self.setCurrent(self.__m_current - 1)
        elif self.__m_wrap:
            self.setCurrent(self.__m_count - 1)

    def getCurrent(self):
        """
        :return: int
        """
        return self.__m_current

    @pyqtSlot(int)
    def setCurrent(self, current):
        """
        :param current: int
        :return:
        """
        current = int(clamp(int(current), 0, self.__m_count - 1))  # type: int
        if current != self.__m_current:
            self.__m_current = current  # type: int
            self.__m_moving = True  # type: bool
            self.currentChanged.emit(current)
            self.update()

    def getCount(self):
        """
        :return: int
        """
        return self.__m_count

    @pyqtSlot(int)
    def setCount(self, count):
        """
        :param count: (int) 2..12
        :return:
        """
        self.__m_count = int(clamp(int(count), 2, 12))  # type: int
        if self.__m_current >= self.__m_count:
            self.setCurrent(self.__m_count - 1)
        self.update()

    def getDucklings(self):
        """
        :return: int
        """
        return self.__m_ducklings

    @pyqtSlot(int)
    def setDucklings(self, ducklings):
        """
        :param ducklings: (int) 0..6
        :return:
        """
        self.__m_ducklings = int(clamp(int(ducklings), 0, 6))  # type: int
        self.update()

    def isWrap(self):
        """
        :return: bool
        """
        return self.__m_wrap

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setWrap(self, wrap):
        """
        :param wrap: bool
        :return:
        """
        self.__m_wrap = bool(wrap)  # type: bool

    def getDuckColor(self):
        """
        :return: QColor
        """
        return self.__m_duckColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setDuckColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        self.__m_duckColor = color  # type: QColor
        self.update()

    def getDucklingColor(self):
        """
        :return: QColor
        """
        return self.__m_ducklingColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setDucklingColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        self.__m_ducklingColor = color  # type: QColor
        self.update()

    def getPadColor(self):
        """
        :return: QColor
        """
        return self.__m_padColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setPadColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        self.__m_padColor = color  # type: QColor
        self.update()

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(360, 100)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(160, 70)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(DucklingPagerWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(DucklingPagerWidget, self).hideEvent(event)

    def resizeEvent(self, event):
        """
        :param event: QResizeEvent
        :return:
        """
        super(DucklingPagerWidget, self).resizeEvent(event)
        self.__m_ducks = []  # type: list[Swimmer]  # re-line up for the new size

    def mouseReleaseEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if e.button() == Qt.LeftButton:
            xs, y, padR, size = self._layout()
            best = min(range(len(xs)), key=lambda i: abs(xs[i] - eventPos(e).x()))  # type: int
            if abs(xs[best] - eventPos(e).x()) < max(padR * 1.6, 14.0):
                self.setCurrent(best)
        super(DucklingPagerWidget, self).mouseReleaseEvent(e)

    def wheelEvent(self, e):
        """
        :param e: QWheelEvent
        :return:
        """
        if e.angleDelta().y() < 0:
            self.next()
        else:
            self.previous()
        e.accept()

    def keyPressEvent(self, e):
        """
        :param e: QKeyEvent
        :return:
        """
        if e.key() in (Qt.Key_Right, Qt.Key_Down):
            self.next()
        elif e.key() in (Qt.Key_Left, Qt.Key_Up):
            self.previous()
        elif e.key() == Qt.Key_Home:
            self.setCurrent(0)
        elif e.key() == Qt.Key_End:
            self.setCurrent(self.__m_count - 1)
        else:
            super(DucklingPagerWidget, self).keyPressEvent(e)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        self._ensureDucks()
        xs, y, padR, size = self._layout()
        mother = self.__m_ducks[0]  # type: Swimmer
        target = xs[self.__m_current]  # type: float
        # Mother swims with a capped speed (ducks do not teleport).
        maxV = size * 6.0  # type: float
        desired = clamp((target - mother.x) * 4.0, -maxV, maxV)  # type: float
        mother.vx += (desired - mother.vx) * min(1.0, dt * 6.0)
        mother.x += mother.vx * dt
        if abs(mother.vx) > size * 0.3:
            self.__m_facing = 1.0 if mother.vx > 0 else -1.0  # type: float
        if self.__m_moving and abs(target - mother.x) < 1.5 and abs(mother.vx) < size * 0.5:
            self.__m_moving = False  # type: bool
            self.__m_quackAt = now  # type: float
        # Ducklings follow the one in front of them.
        for k in range(1, len(self.__m_ducks)):
            front = self.__m_ducks[k - 1]  # type: Swimmer
            d = self.__m_ducks[k]  # type: Swimmer
            tgt = front.x - self.__m_facing * size * (0.85 if k == 1 else 0.6)  # type: float
            tgt = clamp(tgt, size * 0.4, self.width() - size * 0.4)  # type: float  # huddle at the edges
            d.vx += ((tgt - d.x) * 30.0 - d.vx * 8.0) * dt
            d.x += d.vx * dt
        self.update()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        now = self._now()  # type: float
        self._ensureDucks()
        xs, y, padR, size = self._layout()
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        # Water ripples line.
        wc = QColor('#4CC9F0')  # type: QColor
        wc.setAlpha(70)
        p.setPen(QPen(wc, 1.5))
        p.setBrush(Qt.NoBrush)
        wave = QPainterPath()  # type: QPainterPath
        left = xs[0] - padR * 2.5  # type: float
        right = xs[-1] + padR * 2.5  # type: float
        steps = 60  # type: int
        for k in range(steps + 1):
            x = left + (right - left) * k / float(steps)  # type: float
            yy = y + padR * 0.55 + sin(x * 0.08 + now * 2.0) * 2.0  # type: float
            if k == 0:
                wave.moveTo(x, yy)
            else:
                wave.lineTo(x, yy)
        p.drawPath(wave)
        # Lily pads.
        for i, x in enumerate(xs):
            cur = i == self.__m_current  # type: bool
            r = padR * (1.15 if cur else 1.0)  # type: float
            pc = self.__m_padColor.lighter(115) if cur else self.__m_padColor  # type: QColor
            pad = QPainterPath()  # type: QPainterPath
            pad.moveTo(x, y)
            pad.arcTo(QRectF(x - r, y - r * 0.45, r * 2, r * 0.9), 20 + i * 37 % 60, 320)
            pad.closeSubpath()
            p.setPen(QPen(pc.darker(130), 1.0))
            p.setBrush(pc)
            p.drawPath(pad)
            if cur:
                fl = QColor('#FF8FB1')  # type: QColor
                p.setPen(Qt.NoPen)
                p.setBrush(fl)
                p.drawEllipse(QPointF(x + r * 0.55, y - r * 0.1), r * 0.18, r * 0.12)
        # Ducklings first (behind mother), then mother.
        for k in range(len(self.__m_ducks) - 1, -1, -1):
            d = self.__m_ducks[k]  # type: Swimmer
            s = size if k == 0 else size * 0.55  # type: float
            moving = abs(d.vx) > size * 0.25  # type: bool
            ph = now * 14.0 + k * 1.3  # type: float
            bob = -abs(sin(ph)) * s * 0.08 if moving else sin(now * 2.0 + k) * s * 0.02  # type: float
            rot = sin(ph) * 9.0 if moving else 0.0  # type: float
            self._drawDuck(p, QPointF(d.x, y - s * 0.22 + bob), s, rot, k == 0)
        # Quack.
        since = now - self.__m_quackAt  # type: float
        if since < 0.9:
            f = QFont(self.font())  # type: QFont
            f.setBold(True)
            f.setPointSizeF(max(7.0, size * 0.25))
            p.setFont(f)
            qc = QColor(self.palette().text().color())  # type: QColor
            qc.setAlpha(int(255 * (1.0 - since / 0.9)))
            p.setPen(qc)
            m = self.__m_ducks[0]  # type: Swimmer
            p.drawText(QRectF(m.x - 40, y - size * 1.25 - since * 10.0, 80, 18), Qt.AlignCenter, self.tr('Quack!'))
        if self.hasFocus():
            fc = QColor(self.palette().text().color())  # type: QColor
            fc.setAlpha(50)
            p.setPen(QPen(fc, 1.0, Qt.DashLine))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(QRectF(self.rect()).adjusted(2, 2, -2, -2), 10, 10)
        p.end()

    def _drawDuck(self, p, c, s, rot, mother):
        """
        Duck facing the current swim direction.

        :param p: QPainter
        :param c: (QPointF) body center
        :param s: (qreal | float | int) size
        :param rot: (qreal | float | int) waddle rotation
        :param mother: bool
        :return:
        """
        col = self.__m_duckColor if mother else self.__m_ducklingColor  # type: QColor
        p.save()
        p.translate(c)
        p.scale(self.__m_facing, 1.0)
        p.rotate(rot)
        outline = QPen(col.darker(150), max(1.0, s * 0.03))  # type: QPen
        p.setPen(outline)
        p.setBrush(col)
        # Body with tail.
        body = QPainterPath()  # type: QPainterPath
        body.moveTo(-s * 0.55, -s * 0.28)
        body.quadTo(-s * 0.45, -s * 0.05, -s * 0.38, -s * 0.02)
        body.cubicTo(-s * 0.5, s * 0.3, s * 0.4, s * 0.32, s * 0.45, s * 0.02)
        body.cubicTo(s * 0.45, -s * 0.18, -s * 0.1, -s * 0.12, -s * 0.55, -s * 0.28)
        p.drawPath(body)
        p.setBrush(col.darker(108))
        p.drawEllipse(QPointF(-s * 0.04, s * 0.04), s * 0.2, s * 0.1)
        # Head.
        p.setBrush(col)
        hc = QPointF(s * 0.3, -s * 0.3)  # type: QPointF
        p.drawEllipse(hc, s * 0.2, s * 0.19)
        # Beak.
        p.setPen(QPen(QColor('#C76A12'), max(0.8, s * 0.02)))
        p.setBrush(QColor('#FF9F1C'))
        beak = QPainterPath()  # type: QPainterPath
        beak.moveTo(hc.x() + s * 0.15, hc.y() - s * 0.02)
        beak.quadTo(hc.x() + s * 0.36, hc.y() + s * 0.0, hc.x() + s * 0.33, hc.y() + s * 0.06)
        beak.quadTo(hc.x() + s * 0.22, hc.y() + s * 0.09, hc.x() + s * 0.14, hc.y() + s * 0.06)
        beak.closeSubpath()
        p.drawPath(beak)
        # Eye.
        p.setPen(Qt.NoPen)
        p.setBrush(QColor('#1E1E24'))
        p.drawEllipse(QPointF(hc.x() + s * 0.06, hc.y() - s * 0.05), s * 0.04, s * 0.045)
        if mother:
            # A little blue speculum and a bonnet-ish tuft for character.
            p.setBrush(QColor('#4C6FE0'))
            p.drawEllipse(QPointF(-s * 0.05, s * 0.0), s * 0.08, s * 0.035)
            p.setBrush(col.darker(115))
            p.drawEllipse(QPointF(hc.x() - s * 0.05, hc.y() - s * 0.19), s * 0.06, s * 0.035)
        p.restore()

    # ---------- Properties ----------
    current = pyqtProperty(int, fget=getCurrent, fset=setCurrent, notify=currentChanged)  # type: pyqtProperty
    count = pyqtProperty(int, fget=getCount, fset=setCount)  # type: pyqtProperty
    ducklings = pyqtProperty(int, fget=getDucklings, fset=setDucklings)  # type: pyqtProperty
    wrap = pyqtProperty(bool, fget=isWrap, fset=setWrap)  # type: pyqtProperty
    duckColor = pyqtProperty(QColor, fget=getDuckColor, fset=setDuckColor)  # type: pyqtProperty
    ducklingColor = pyqtProperty(QColor, fget=getDucklingColor, fset=setDucklingColor)  # type: pyqtProperty
    padColor = pyqtProperty(QColor, fget=getPadColor, fset=setPadColor)  # type: pyqtProperty
