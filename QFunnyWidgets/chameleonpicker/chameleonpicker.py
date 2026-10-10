# -*- coding: utf-8 -*-
"""
ChameleonColorPickerWidget: a swatch color picker with a chameleon on a branch. One turret eye
follows the swatch you hover while the other wanders off independently. Click a swatch and the
tongue shoots out, grabs the color and reels it in, then the new color washes over the chameleon
from head to tail.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QLinearGradient, QBrush
from ManyQt.QtWidgets import QWidget
from math import sin, cos, pi, atan2, ceil
from random import uniform

DEFAULT_COLORS = ['#E63946', '#FF9F1C', '#FFD23F', '#9BDB4D', '#3BCEAC', '#4CC9F0',
                  '#4361EE', '#7B5CFF', '#C77DFF', '#FF70A6', '#8D6E63', '#495057']  # type: list[str]
TONGUE_OUT = 0.16  # type: float
TONGUE_HOLD = 0.3  # type: float
TONGUE_IN = 0.5  # type: float
WIPE_START = 0.42  # type: float
WIPE_END = 1.1  # type: float


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


class ChameleonColorPickerWidget(QWidget):
    """
    Color picker that a chameleon takes very personally.
    """
    colorChanged = pyqtSignal(QColor)  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param colors: (list[str | unicode | QString]) Swatch colours.
        :param color: (QColor | Qt.GlobalColor | int | str | QString) Initial color.
        :param columns: (int) Swatch grid columns.
        :param showHex: (bool) Show the hex code under the chameleon.
        :param branchColor: QColor | Qt.GlobalColor | int | str | QString
        :param colorChanged: callable | None
        :param args: any
        :param kwargs: any
        """
        colors = kwargs.pop('colors', DEFAULT_COLORS)  # type: list[str]
        color = kwargs.pop('color', '#3BCEAC')  # type: QColor
        columns = kwargs.pop('columns', 4)  # type: int
        showHex = kwargs.pop('showHex', True)  # type: bool
        branchColor = kwargs.pop('branchColor', '#8B5E3C')  # type: QColor
        colorChanged = kwargs.pop('colorChanged', None)  # type: callable | None
        super(ChameleonColorPickerWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_colors = [QColor(c) for c in (colors or DEFAULT_COLORS)]  # type: list[QColor]
        self.__m_color = QColor(color)  # type: QColor
        self.__m_columns = int(clamp(int(columns), 1, 8))  # type: int
        self.__m_showHex = bool(showHex)  # type: bool
        self.__m_branchColor = QColor(branchColor)  # type: QColor
        if callable(colorChanged):
            self.colorChanged.connect(colorChanged)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        # State.
        self.__m_prevColor = QColor(self.__m_color)  # type: QColor
        self.__m_pickAt = -10.0  # type: float
        self.__m_target = -1  # type: int
        self.__m_hover = -1  # type: int
        self.__m_lookAng = 0.0  # type: float
        self.__m_wanderAng = 0.0  # type: float
        self.__m_wanderTarget = 0.0  # type: float
        self.__m_nextWander = 1.0  # type: float
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
        :return: (tuple) chameleon center QPointF, size float, list of swatch QRectF
        """
        w = float(self.width())  # type: float
        h = float(self.height())  # type: float
        leftW = w * 0.48  # type: float
        hexH = 26.0 if self.__m_showHex else 0.0  # type: float
        # The chameleon spans about 1.7 s from tail curl to snout.
        s = max(30.0, min((leftW - 8.0) / 1.72, (h - hexH) * 0.95))  # type: float
        c = QPointF(s * 0.92 + 6.0, (h - hexH) / 2.0 + s * 0.02)  # type: QPointF
        n = len(self.__m_colors)  # type: int
        cols = self.__m_columns  # type: int
        rows = int(ceil(n / float(cols)))  # type: int
        gap = 8.0  # type: float
        areaW = w - leftW - 12.0  # type: float
        cell = max(12.0, min((areaW - gap * (cols - 1)) / cols, (h - 16.0 - gap * (rows - 1)) / rows, 52.0))  # type: float
        gridW = cell * cols + gap * (cols - 1)  # type: float
        gridH = cell * rows + gap * (rows - 1)  # type: float
        x0 = leftW + (areaW - gridW) / 2.0 + 6.0  # type: float
        y0 = (h - gridH) / 2.0  # type: float
        rects = [QRectF(x0 + (i % cols) * (cell + gap), y0 + (i // cols) * (cell + gap), cell, cell) for i in range(n)]
        return c, s, rects

    def _mouth(self, c, s):
        """
        :param c: QPointF
        :param s: qreal | float | int
        :return: QPointF
        """
        return QPointF(c.x() + s * 0.66, c.y() - s * 0.02)

    def _eye(self, c, s):
        """
        :param c: QPointF
        :param s: qreal | float | int
        :return: QPointF
        """
        return QPointF(c.x() + s * 0.44, c.y() - s * 0.14)

    def _pick(self, index):
        """
        :param index: int
        :return:
        """
        if not 0 <= index < len(self.__m_colors):
            return
        self.__m_prevColor = self._bodyColorAt(1.0)  # type: QColor  # whatever it currently looks like
        self.__m_target = index  # type: int
        self.__m_pickAt = self._now()  # type: float
        self.__m_color = QColor(self.__m_colors[index])  # type: QColor
        self.colorChanged.emit(QColor(self.__m_color))

    def _wipe(self):
        """
        :return: (qreal | float | int) 0 = old color everywhere .. 1 = new color everywhere
        """
        since = self._now() - self.__m_pickAt  # type: float
        return clamp((since - WIPE_START) / (WIPE_END - WIPE_START), 0.0, 1.0)

    def _bodyColorAt(self, pos):
        """
        :param pos: (qreal | float | int) 0 = snout .. 1 = tail tip
        :return: QColor
        """
        return QColor(self.__m_color) if pos <= self._wipe() else QColor(self.__m_prevColor)

    # ---------- Public API ----------
    def getColor(self):
        """
        :return: QColor
        """
        return QColor(self.__m_color)

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setColor(self, color):
        """
        Set the color directly (no tongue involved).
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        if color != self.__m_color:
            self.__m_prevColor = QColor(self.__m_color)  # type: QColor
            self.__m_color = QColor(color)  # type: QColor
            self.__m_target = -1  # type: int
            self.__m_pickAt = self._now() - WIPE_START  # type: float
            self.colorChanged.emit(QColor(color))

    def getColors(self):
        """
        :return: list[str | unicode | QString]
        """
        return [c.name() for c in self.__m_colors]

    @pyqtSlot(list)
    def setColors(self, colors):
        """
        :param colors: list[str]
        :return:
        """
        self.__m_colors = [QColor(c) for c in (colors or DEFAULT_COLORS)]  # type: list[QColor]
        self.update()

    def getColumns(self):
        """
        :return: int
        """
        return self.__m_columns

    @pyqtSlot(int)
    def setColumns(self, columns):
        """
        :param columns: (int) 1..8
        :return:
        """
        self.__m_columns = int(clamp(int(columns), 1, 8))  # type: int
        self.update()

    def isShowHex(self):
        """
        :return: bool
        """
        return self.__m_showHex

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setShowHex(self, showHex):
        """
        :param showHex: bool
        :return:
        """
        self.__m_showHex = bool(showHex)  # type: bool
        self.update()

    def getBranchColor(self):
        """
        :return: QColor
        """
        return self.__m_branchColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setBranchColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        self.__m_branchColor = color  # type: QColor
        self.update()

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(460, 220)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(260, 130)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(ChameleonColorPickerWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(ChameleonColorPickerWidget, self).hideEvent(event)

    def mouseMoveEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        c, s, rects = self._layout()
        hover = -1  # type: int
        for i, r in enumerate(rects):
            if r.contains(eventPos(e)):
                hover = i  # type: int
                break
        if hover != self.__m_hover:
            self.__m_hover = hover  # type: int
            self.setCursor(Qt.PointingHandCursor if hover >= 0 else Qt.ArrowCursor)
        super(ChameleonColorPickerWidget, self).mouseMoveEvent(e)

    def leaveEvent(self, e):
        """
        :param e: QEvent
        :return:
        """
        self.__m_hover = -1  # type: int
        super(ChameleonColorPickerWidget, self).leaveEvent(e)

    def mouseReleaseEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if e.button() == Qt.LeftButton:
            c, s, rects = self._layout()
            for i, r in enumerate(rects):
                if r.contains(eventPos(e)):
                    self._pick(i)
                    break
        super(ChameleonColorPickerWidget, self).mouseReleaseEvent(e)

    def keyPressEvent(self, e):
        """
        :param e: QKeyEvent
        :return:
        """
        n = len(self.__m_colors)  # type: int
        cur = next((i for i, c in enumerate(self.__m_colors) if c == self.__m_color), -1)  # type: int
        step = {Qt.Key_Right: 1, Qt.Key_Left: -1, Qt.Key_Down: self.__m_columns, Qt.Key_Up: -self.__m_columns}.get(e.key())
        if step is not None:
            self._pick((cur + step) % n if cur >= 0 else 0)
        else:
            super(ChameleonColorPickerWidget, self).keyPressEvent(e)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        c, s, rects = self._layout()
        eye = self._eye(c, s)  # type: QPointF
        since = now - self.__m_pickAt  # type: float
        idx = self.__m_target if since < TONGUE_IN else self.__m_hover  # type: int
        if 0 <= idx < len(rects):
            tgt = rects[idx].center()  # type: QPointF
            ang = atan2(tgt.y() - eye.y(), tgt.x() - eye.x())  # type: float
        else:
            ang = 0.0  # type: float
        self.__m_lookAng += (ang - self.__m_lookAng) * min(1.0, dt * 10.0)
        if now >= self.__m_nextWander:
            self.__m_wanderTarget = uniform(-pi, pi)  # type: float
            self.__m_nextWander = now + uniform(0.8, 2.0)  # type: float
        self.__m_wanderAng += (self.__m_wanderTarget - self.__m_wanderAng) * min(1.0, dt * 6.0)
        self.update()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        now = self._now()  # type: float
        c, s, rects = self._layout()
        since = now - self.__m_pickAt  # type: float
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        # Swatches.
        for i, r in enumerate(rects):
            col = self.__m_colors[i]  # type: QColor
            rr = QRectF(r)  # type: QRectF
            if i == self.__m_target and TONGUE_OUT * 0.8 <= since < TONGUE_IN + 0.25:
                # Bitten: shrinks, then pops back.
                k = clamp((since - TONGUE_IN) / 0.25, 0.0, 1.0)  # type: float
                sc = 0.55 + 0.45 * k  # type: float
                rr = QRectF(r.center().x() - r.width() * sc / 2.0, r.center().y() - r.height() * sc / 2.0,
                            r.width() * sc, r.height() * sc)
            elif i == self.__m_hover:
                rr = r.adjusted(-2, -2, 2, 2)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(0, 0, 0, 40))
            p.drawRoundedRect(rr.translated(0, 2), rr.width() * 0.22, rr.width() * 0.22)
            p.setBrush(col)
            p.drawRoundedRect(rr, rr.width() * 0.22, rr.width() * 0.22)
            if col == self.__m_color:
                p.setPen(QPen(QColor('#FFFFFF'), 2.5))
                p.setBrush(Qt.NoBrush)
                p.drawRoundedRect(rr.adjusted(3, 3, -3, -3), rr.width() * 0.16, rr.width() * 0.16)
        # Chameleon.
        self._drawChameleon(p, c, s, now)
        # Tongue.
        if 0 <= self.__m_target < len(rects) and since < TONGUE_IN:
            mouth = self._mouth(c, s)  # type: QPointF
            tgt = rects[self.__m_target].center()  # type: QPointF
            if since < TONGUE_OUT:
                ext = since / TONGUE_OUT  # type: float
            elif since < TONGUE_HOLD:
                ext = 1.0  # type: float
            else:
                ext = 1.0 - (since - TONGUE_HOLD) / (TONGUE_IN - TONGUE_HOLD)  # type: float
            tip = QPointF(mouth.x() + (tgt.x() - mouth.x()) * ext, mouth.y() + (tgt.y() - mouth.y()) * ext)  # type: QPointF
            p.setPen(QPen(QColor('#FF7A90'), max(2.5, s * 0.035), Qt.SolidLine, Qt.RoundCap))
            p.drawLine(mouth, tip)
            p.setPen(QPen(QColor('#C2405A'), 1.2))
            p.setBrush(self.__m_colors[self.__m_target] if since >= TONGUE_OUT else QColor('#FF7A90'))
            p.drawEllipse(tip, s * 0.05, s * 0.05)
        # Hex label.
        if self.__m_showHex:
            f = QFont('Monospace')  # type: QFont
            f.setStyleHint(QFont.TypeWriter)
            f.setBold(True)
            f.setPointSizeF(10.0)
            p.setFont(f)
            tc = QColor(self.palette().text().color())  # type: QColor
            hx = self.__m_color.name().upper()  # type: str
            box = QRectF(c.x() - s * 0.55, self.height() - 24.0, s * 1.1, 20.0)  # type: QRectF
            p.setPen(Qt.NoPen)
            p.setBrush(self.__m_color)
            p.drawEllipse(QPointF(box.left() + 10.0, box.center().y()), 6.0, 6.0)
            p.setPen(tc)
            p.drawText(box.adjusted(22, 0, 0, 0), Qt.AlignLeft | Qt.AlignVCenter, hx)
        p.end()

    def _drawChameleon(self, p, c, s, now):
        """
        Facing right. Color washes from snout (pos 0) to tail tip (pos 1).
        :param p: QPainter
        :param c: (QPointF) body center.
        :param s: (qreal | float | int) size
        :param now: qreal | float | int
        :return:
        """
        wipe = self._wipe()  # type: float
        new = QColor(self.__m_color)  # type: QColor
        old = QColor(self.__m_prevColor)  # type: QColor
        # Gradient along x: snout (right) is position 0, tail (left) is position 1.
        grad = QLinearGradient(QPointF(c.x() + s * 0.7, 0), QPointF(c.x() - s * 0.95, 0))  # type: QLinearGradient
        grad.setColorAt(0.0, new)
        if 0.0 < wipe < 1.0:
            grad.setColorAt(max(0.0, wipe - 0.02), new)
            grad.setColorAt(min(1.0, wipe + 0.02), old)
            grad.setColorAt(1.0, old)
        else:
            grad.setColorAt(1.0, new if wipe >= 1.0 else old)
        brush = QBrush(grad)  # type: QBrush
        outlineC = (new if wipe >= 0.5 else old).darker(150)  # type: QColor
        outline = QPen(outlineC, max(1.2, s * 0.018))  # type: QPen
        bob = sin(now * 1.6) * s * 0.01  # type: float
        # Branch.
        br = self.__m_branchColor  # type: QColor
        by = c.y() + s * 0.3  # type: float
        p.setPen(QPen(br, max(4.0, s * 0.06), Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(c.x() - s * 0.95, by + s * 0.03), QPointF(c.x() + s * 0.8, by - s * 0.02))
        p.setPen(QPen(br, max(2.0, s * 0.03), Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(c.x() + s * 0.45, by - s * 0.01), QPointF(c.x() + s * 0.62, by + s * 0.14))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor('#5FB37A'))
        leaf = QPainterPath()  # type: QPainterPath
        lp = QPointF(c.x() + s * 0.62, by + s * 0.14)  # type: QPointF
        leaf.moveTo(lp)
        leaf.quadTo(lp.x() + s * 0.12, lp.y() + s * 0.02, lp.x() + s * 0.16, lp.y() + s * 0.12)
        leaf.quadTo(lp.x() + s * 0.02, lp.y() + s * 0.12, lp.x(), lp.y())
        p.drawPath(leaf)
        p.save()
        p.translate(0, bob)
        # Tail spiral (stroked with the gradient, getting thinner).
        tc = QPointF(c.x() - s * 0.66, c.y() + s * 0.12)  # type: QPointF
        pts = []  # type: list[QPointF]
        steps = 40  # type: int
        for k in range(steps + 1):
            t = k / float(steps)  # type: float
            ang = -pi * 0.15 - t * pi * 2.6  # type: float
            rad = s * 0.2 * (1.0 - t * 0.78)  # type: float
            pts.append(QPointF(tc.x() + cos(ang) * rad, tc.y() + sin(ang) * rad))
        pts.insert(0, QPointF(c.x() - s * 0.45, c.y() + s * 0.02))
        for k in range(len(pts) - 1):
            wdt = s * 0.11 * (1.0 - k / float(len(pts))) + s * 0.015  # type: float
            p.setPen(QPen(brush, wdt, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(pts[k], pts[k + 1])
        # Legs.
        p.setPen(QPen(brush, max(3.0, s * 0.05), Qt.SolidLine, Qt.RoundCap))
        for lx, fx in ((-0.25, -0.32), (0.22, 0.3)):
            p.drawLine(QPointF(c.x() + lx * s, c.y() + s * 0.12), QPointF(c.x() + fx * s, by - s * 0.01))
        # Body.
        body = QPainterPath()  # type: QPainterPath
        body.moveTo(c.x() - s * 0.5, c.y() + s * 0.02)
        body.cubicTo(c.x() - s * 0.42, c.y() - s * 0.3, c.x() + s * 0.12, c.y() - s * 0.36, c.x() + s * 0.36, c.y() - s * 0.2)
        body.lineTo(c.x() + s * 0.4, c.y() + s * 0.1)
        body.cubicTo(c.x() + s * 0.15, c.y() + s * 0.24, c.x() - s * 0.3, c.y() + s * 0.24, c.x() - s * 0.5, c.y() + s * 0.02)
        p.setPen(outline)
        p.setBrush(brush)
        p.drawPath(body)
        # Back crest + stripes.
        p.setPen(QPen(outlineC, max(1.0, s * 0.012)))
        for k in range(5):
            x = c.x() - s * 0.32 + k * s * 0.14  # type: float
            p.drawLine(QPointF(x, c.y() - s * 0.16), QPointF(x + s * 0.04, c.y() + s * 0.12))
        # Head with casque.
        head = QPainterPath()  # type: QPainterPath
        head.moveTo(c.x() + s * 0.3, c.y() - s * 0.22)
        head.lineTo(c.x() + s * 0.4, c.y() - s * 0.38)
        head.quadTo(c.x() + s * 0.62, c.y() - s * 0.18, c.x() + s * 0.7, c.y() - s * 0.02)
        head.quadTo(c.x() + s * 0.6, c.y() + s * 0.12, c.x() + s * 0.38, c.y() + s * 0.13)
        head.closeSubpath()
        p.setPen(outline)
        p.setBrush(brush)
        p.drawPath(head)
        # Mouth line.
        p.setPen(QPen(outlineC, max(1.0, s * 0.015), Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(c.x() + s * 0.66, c.y() - s * 0.02), QPointF(c.x() + s * 0.48, c.y() + s * 0.04))
        # Turret eyes: near eye tracks, far eye (peeking over the head) wanders.
        eye = self._eye(c, s)  # type: QPointF
        far = QPointF(eye.x() + s * 0.06, eye.y() - s * 0.13)  # type: QPointF
        for pos, ang, r in ((far, self.__m_wanderAng, s * 0.06), (eye, self.__m_lookAng, s * 0.1)):
            p.setPen(outline)
            p.setBrush(brush)
            p.drawEllipse(pos, r, r)
            p.setPen(QPen(outlineC, max(0.8, s * 0.008)))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(pos, r * 0.7, r * 0.7)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor('#1E1E24'))
            p.drawEllipse(QPointF(pos.x() + cos(ang) * r * 0.45, pos.y() + sin(ang) * r * 0.45), r * 0.3, r * 0.3)
            p.setBrush(QColor('#FFFFFF'))
            p.drawEllipse(QPointF(pos.x() + cos(ang) * r * 0.45 - r * 0.1, pos.y() + sin(ang) * r * 0.45 - r * 0.1),
                          r * 0.09, r * 0.09)
        p.restore()

    # ---------- Properties ----------
    color = pyqtProperty(QColor, fget=getColor, fset=setColor, notify=colorChanged)  # type: pyqtProperty
    colors = pyqtProperty('QStringList', fget=getColors, fset=setColors)  # type: pyqtProperty
    columns = pyqtProperty(int, fget=getColumns, fset=setColumns)  # type: pyqtProperty
    showHex = pyqtProperty(bool, fget=isShowHex, fset=setShowHex)  # type: pyqtProperty
    branchColor = pyqtProperty(QColor, fget=getBranchColor, fset=setBranchColor)  # type: pyqtProperty
