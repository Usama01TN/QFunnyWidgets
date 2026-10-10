# -*- coding: utf-8 -*-
"""
SearchDetectiveWidget: a search field with a resident detective. He puffs his pipe while idle,
sweeps his magnifying glass while you type, investigates intently while the search runs, declares
"Elementary!" when results are found and gets rained on when the trail goes cold.
DetectiveFaceWidget is the painted detective and can be used on its own.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QFontMetricsF
from ManyQt.QtWidgets import QWidget, QLineEdit, QVBoxLayout
from random import uniform, choice
from math import sin, cos, pi

IDLE, TYPING, SEARCHING, FOUND, NONE = range(5)  # type: tuple


def clamp(x, a, b):
    """
    :param x: qreal | float | int
    :param a: qreal | float | int
    :param b: qreal | float | int
    :return: qreal | float | int
    """
    return a if x < a else b if x > b else x


LINES = {
    IDLE: ['Who are we looking for?', 'The game is afoot. Type something.'],
    TYPING: ['Hmm... a clue.', 'Go on, I am listening.', 'Fascinating. Continue.'],
    SEARCHING: ['Investigating...', 'Examining the evidence...', 'Interrogating the database...'],
    NONE: ['The trail has gone cold.', 'No suspects. Curious.', 'Nothing. Not even fingerprints.'],
}  # type: dict


class Puff(object):
    """
    A pipe smoke puff or a rain drop.
    """

    def __init__(self, x=0.0, y=0.0, vx=0.0, vy=0.0, life=1.5, kind=0):
        """
        :param x: qreal | float | int
        :param y: qreal | float | int
        :param vx: qreal | float | int
        :param vy: qreal | float | int
        :param life: (qreal | float | int) s
        :param kind: (int) 0 = smoke, 1 = rain
        """
        self.x = float(x)  # type: float
        self.y = float(y)  # type: float
        self.vx = float(vx)  # type: float
        self.vy = float(vy)  # type: float
        self.life = float(life)  # type: float
        self.maxLife = float(life)  # type: float
        self.kind = int(kind)  # type: int


class DetectiveFaceWidget(QWidget):
    """
    The detective (left) and his remarks (right).
    """

    def __init__(self, *args, **kwargs):
        """
        :param state: (int) IDLE, TYPING, SEARCHING, FOUND or NONE.
        :param comment: str | unicode | QString
        :param hatColor: QColor | Qt.GlobalColor | int | str | QString
        :param skinColor: QColor | Qt.GlobalColor | int | str | QString
        :param args: any
        :param kwargs: any
        """
        state = kwargs.pop('state', IDLE)  # type: int
        comment = kwargs.pop('comment', LINES[IDLE][0])  # type: str
        hatColor = kwargs.pop('hatColor', '#8B6B4A')  # type: QColor
        skinColor = kwargs.pop('skinColor', '#F3C6A5')  # type: QColor
        super(DetectiveFaceWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_state = int(clamp(int(state), 0, 4))  # type: int
        self.__m_comment = comment  # type: str
        self.__m_hatColor = QColor(hatColor)  # type: QColor
        self.__m_skinColor = QColor(skinColor)  # type: QColor
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        # State.
        self.__m_changedAt = 0.0  # type: float
        self.__m_puffs = []  # type: list[Puff]
        self.__m_puffAcc = 0.0  # type: float
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

    def _face(self):
        """
        :return: (tuple) center QPointF, radius float
        """
        h = float(self.height())  # type: float
        R = max(14.0, min(h * 0.36, self.width() * 0.16))  # type: float
        return QPointF(R * 1.6, h / 2.0 + R * 0.25), R

    # ---------- Public API ----------
    def getState(self):
        """
        :return: int
        """
        return self.__m_state

    @pyqtSlot(int)
    def setState(self, state):
        """
        :param state: (int) IDLE, TYPING, SEARCHING, FOUND or NONE
        :return:
        """
        state = int(clamp(int(state), 0, 4))  # type: int
        if state != self.__m_state:
            self.__m_state = state  # type: int
            self.__m_changedAt = self._now()  # type: float
            self.update()

    def getComment(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_comment

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setComment(self, comment):
        """
        :param comment: str | unicode | QString
        :return:
        """
        self.__m_comment = comment  # type: str
        self.update()

    def getHatColor(self):
        """
        :return: QColor
        """
        return self.__m_hatColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setHatColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        self.__m_hatColor = color  # type: QColor
        self.update()

    def getSkinColor(self):
        """
        :return: QColor
        """
        return self.__m_skinColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setSkinColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        self.__m_skinColor = color  # type: QColor
        self.update()

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(400, 140)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(220, 90)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(DetectiveFaceWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(DetectiveFaceWidget, self).hideEvent(event)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        c, R = self._face()
        st = self.__m_state  # type: int
        if st in (IDLE, TYPING, SEARCHING):
            self.__m_puffAcc += dt * (1.2 if st == IDLE else 2.5)
            while self.__m_puffAcc > 1.0:
                self.__m_puffAcc -= 1.0
                self.__m_puffs.append(Puff(c.x() - R * 1.0, c.y() + R * 0.28, uniform(-3, 6), -uniform(14, 24),
                                           uniform(1.4, 2.0), 0))
        elif st == NONE:
            self.__m_puffAcc += dt * 18.0
            while self.__m_puffAcc > 1.0:
                self.__m_puffAcc -= 1.0
                self.__m_puffs.append(Puff(c.x() + uniform(-R * 0.6, R * 0.6), c.y() - R * 1.35, 0, uniform(90, 130),
                                           uniform(0.25, 0.4), 1))
        alive = []  # type: list[Puff]
        for pf in self.__m_puffs:
            pf.x += pf.vx * dt
            pf.y += pf.vy * dt
            pf.life -= dt
            if pf.life > 0:
                alive.append(pf)
        self.__m_puffs = alive  # type: list[Puff]
        self.update()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        now = self._now()  # type: float
        c, R = self._face()
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        st = self.__m_state  # type: int
        since = now - self.__m_changedAt  # type: float
        hop = -abs(sin(since * 10.0)) * R * 0.12 * max(0.0, 1.0 - since / 0.8) if st == FOUND else 0.0  # type: float
        p.save()
        p.translate(0, hop)
        self._drawDetective(p, c, R, st, now)
        p.restore()
        # Smoke and rain.
        p.setPen(Qt.NoPen)
        for pf in self.__m_puffs:
            a = clamp(pf.life / pf.maxLife, 0.0, 1.0)  # type: float
            if pf.kind == 0:
                sc = QColor(200, 205, 215)  # type: QColor
                sc.setAlpha(int(150 * a))
                p.setBrush(sc)
                rr = R * (0.06 + 0.12 * (1.0 - a))  # type: float
                p.drawEllipse(QPointF(pf.x, pf.y), rr, rr)
            else:
                rc = QColor('#7FB8FF')  # type: QColor
                rc.setAlpha(int(220 * a))
                p.setPen(QPen(rc, max(1.0, R * 0.03), Qt.SolidLine, Qt.RoundCap))
                p.drawLine(QPointF(pf.x, pf.y), QPointF(pf.x, pf.y + R * 0.08))
                p.setPen(Qt.NoPen)
        if st == NONE:
            # Personal rain cloud.
            cc = QColor('#9AA3B5')  # type: QColor
            p.setBrush(cc)
            cy = c.y() - R * 1.45  # type: float
            for dx, rr in ((-0.35, 0.22), (0.0, 0.3), (0.35, 0.22)):
                p.drawEllipse(QPointF(c.x() + dx * R + sin(now) * R * 0.05, cy), rr * R, rr * R * 0.8)
        self._drawBubble(p, QRectF(c.x() + R * 1.25, 4.0, self.width() - c.x() - R * 1.25 - 4.0, self.height() - 8.0), now)
        p.end()

    def _drawDetective(self, p, c, R, st, now):
        """
        :param p: QPainter
        :param c: (QPointF) face center
        :param R: (qreal | float | int) radius
        :param st: int
        :param now: qreal | float | int
        :return:
        """
        skin = self.__m_skinColor  # type: QColor
        hat = self.__m_hatColor  # type: QColor
        ink = QColor('#2B2B33')  # type: QColor
        # Head.
        p.setPen(QPen(skin.darker(130), max(1.0, R * 0.03)))
        p.setBrush(skin)
        p.drawEllipse(c, R * 0.8, R * 0.88)
        # Deerstalker: dome with check pattern, front and back bills, tied-up ear flaps.
        dome = QPainterPath()  # type: QPainterPath
        dome.moveTo(c.x() - R * 0.85, c.y() - R * 0.25)
        dome.cubicTo(
            c.x() - R * 0.9, c.y() - R * 1.25, c.x() + R * 0.9, c.y() - R * 1.25, c.x() + R * 0.85, c.y() - R * 0.25)
        dome.quadTo(c.x(), c.y() - R * 0.45, c.x() - R * 0.85, c.y() - R * 0.25)
        p.setPen(QPen(hat.darker(140), max(1.0, R * 0.03)))
        p.setBrush(hat)
        p.drawPath(dome)
        p.save()
        p.setClipPath(dome)
        p.setPen(QPen(hat.darker(125), max(1.0, R * 0.025)))
        step = R * 0.18  # type: float
        x = c.x() - R  # type: float
        while x < c.x() + R:
            p.drawLine(QPointF(x, c.y() - R * 1.3), QPointF(x, c.y()))
            x += step
        y = c.y() - R * 1.2  # type: float
        while y < c.y():
            p.drawLine(QPointF(c.x() - R, y), QPointF(c.x() + R, y))
            y += step
        p.restore()
        p.setPen(QPen(hat.darker(140), max(1.0, R * 0.03)))
        p.setBrush(hat.darker(110))
        p.drawEllipse(QPointF(c.x() + R * 0.92, c.y() - R * 0.3), R * 0.3, R * 0.1)   # front bill
        p.drawEllipse(QPointF(c.x() - R * 0.92, c.y() - R * 0.3), R * 0.25, R * 0.09)  # back bill
        p.setBrush(hat.lighter(110))
        p.drawEllipse(QPointF(c.x(), c.y() - R * 1.05), R * 0.1, R * 0.07)          # bow on top
        # Pipe (left side of the mouth).
        p.setPen(QPen(QColor('#4A2F1E'), max(1.5, R * 0.06), Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(c.x() - R * 0.2, c.y() + R * 0.42), QPointF(c.x() - R * 0.85, c.y() + R * 0.5))
        p.setPen(QPen(QColor('#3A2414'), max(1.0, R * 0.03)))
        p.setBrush(QColor('#6B4226'))
        p.drawRoundedRect(QRectF(c.x() - R * 1.13, c.y() + R * 0.3, R * 0.26, R * 0.3), R * 0.06, R * 0.06)
        # Left eye + brow.
        ex = c.x() - R * 0.3  # type: float
        ey = c.y() - R * 0.08  # type: float
        p.setPen(Qt.NoPen)
        p.setBrush(ink)
        if st == FOUND:
            p.setPen(QPen(ink, max(1.2, R * 0.05), Qt.SolidLine, Qt.RoundCap))
            p.setBrush(Qt.NoBrush)
            p.drawArc(QRectF(ex - R * 0.1, ey - R * 0.05, R * 0.2, R * 0.14), 20 * 16, 140 * 16)
        else:
            p.drawEllipse(QPointF(ex, ey), R * 0.06, R * (0.03 if st == SEARCHING else 0.07))
        bp = QPen(QColor('#5A4030'), max(1.2, R * 0.05), Qt.SolidLine, Qt.RoundCap)  # type: QPen
        p.setPen(bp)
        if st == SEARCHING:
            p.drawLine(QPointF(ex - R * 0.14, ey - R * 0.18), QPointF(ex + R * 0.12, ey - R * 0.12))
        elif st == NONE:
            p.drawLine(QPointF(ex - R * 0.14, ey - R * 0.14), QPointF(ex + R * 0.12, ey - R * 0.2))
        else:
            lift = R * 0.08 if st == FOUND else 0.0  # type: float
            p.drawLine(QPointF(ex - R * 0.14, ey - R * 0.17 - lift), QPointF(ex + R * 0.12, ey - R * 0.19 - lift))
        # Mouth.
        mp = QPen(QColor('#7A3A2E'), max(1.2, R * 0.05), Qt.SolidLine, Qt.RoundCap)  # type: QPen
        p.setPen(mp)
        p.setBrush(Qt.NoBrush)
        mx = c.x() + R * 0.02  # type: float
        my = c.y() + R * 0.42  # type: float
        if st == FOUND:
            p.setBrush(QColor('#7A3A2E'))
            m = QPainterPath()  # type: QPainterPath
            m.moveTo(mx - R * 0.22, my - R * 0.06)
            m.quadTo(mx, my + R * 0.25, mx + R * 0.22, my - R * 0.06)
            m.closeSubpath()
            p.drawPath(m)
        elif st == NONE:
            p.drawArc(QRectF(mx - R * 0.16, my, R * 0.32, R * 0.18), 30 * 16, 120 * 16)
        elif st == TYPING:
            p.drawEllipse(QPointF(mx + R * 0.05, my), R * 0.05, R * 0.06)
        else:
            p.drawLine(QPointF(mx - R * 0.14, my), QPointF(mx + R * 0.14, my))
        # Magnifying glass over the right eye: sweeps while typing / searching.
        sweep = 0.0  # type: float
        if st == TYPING:
            sweep = sin(now * 4.0) * R * 0.12  # type: float
        elif st == SEARCHING:
            sweep = sin(now * 7.0) * R * 0.3  # type: float
        lc = QPointF(c.x() + R * 0.35 + sweep, c.y() - R * 0.05 + (-R * 0.15 if st == FOUND else 0.0))  # type: QPointF
        lr = R * 0.36  # type: float
        gold = QColor('#C9A227')  # type: QColor
        p.setPen(QPen(QColor('#3A2414'), max(2.0, R * 0.1), Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(lc.x() + lr * 0.65, lc.y() + lr * 0.65), QPointF(lc.x() + lr * 1.5, lc.y() + lr * 1.5))
        lens = QPainterPath()  # type: QPainterPath
        lens.addEllipse(lc, lr, lr)
        p.save()
        p.setClipPath(lens)
        p.fillPath(lens, skin.lighter(104))
        # The magnified eye (it follows the lens, obviously).
        er = lr * 0.62  # type: float
        p.setPen(QPen(skin.darker(140), max(1.0, R * 0.02)))
        p.setBrush(QColor('#FFFFFF'))
        p.drawEllipse(QPointF(lc.x(), lc.y()), er, er * (0.55 if st == SEARCHING else 0.9))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor('#4B6B8A'))
        look = sin(now * 7.0) * er * 0.3 if st == SEARCHING else 0.0  # type: float
        p.drawEllipse(QPointF(lc.x() + look, lc.y()), er * 0.5, er * (0.4 if st == SEARCHING else 0.5))
        p.setBrush(ink)
        p.drawEllipse(QPointF(lc.x() + look, lc.y()), er * 0.25, er * 0.25)
        p.setBrush(QColor(255, 255, 255, 220))
        p.drawEllipse(QPointF(lc.x() + look - er * 0.18, lc.y() - er * 0.18), er * 0.1, er * 0.1)
        p.fillPath(lens, QColor(190, 225, 255, 50))
        p.restore()
        p.setPen(QPen(gold, max(2.0, R * 0.08)))
        p.setBrush(Qt.NoBrush)
        p.drawPath(lens)
        if st == FOUND:
            # Triumphant glint.
            gl = QColor('#FFF6C8')  # type: QColor
            k = 0.6 + 0.4 * sin(now * 8.0)  # type: float
            p.setPen(QPen(gl, max(1.5, R * 0.04), Qt.SolidLine, Qt.RoundCap))
            g0 = QPointF(lc.x() - lr * 0.7, lc.y() - lr * 0.75)  # type: QPointF
            for a in range(4):
                ang = a * pi / 2.0  # type: float
                p.drawLine(g0, QPointF(g0.x() + cos(ang) * lr * 0.35 * k, g0.y() + sin(ang) * lr * 0.35 * k))

    def _drawBubble(self, p, area, now):
        """
        :param p: QPainter
        :param area: QRectF
        :param now: qreal | float | int
        :return:
        """
        if area.width() < 60:
            return
        f = QFont(self.font())  # type: QFont
        f.setPointSizeF(clamp(area.height() * 0.09, 9.0, 11.5))
        f.setItalic(True)
        fm = QFontMetricsF(f)  # type: QFontMetricsF
        text = self.__m_comment  # type: str
        if self.__m_state == SEARCHING:
            text = text.rstrip('.') + '.' * (1 + int(now * 3.0) % 3)  # type: str
        maxW = area.width() - 14.0  # type: float
        br = fm.boundingRect(
            QRectF(0, 0, maxW - 26.0, 1000.0), Qt.TextWordWrap, self.__m_comment + '..')  # type: QRectF
        bw = min(maxW, br.width() + 28.0)  # type: float
        bh = br.height() + 18.0  # type: float
        bx = area.left() + 12.0  # type: float
        by = area.top() + (area.height() - bh) / 2.0  # type: float
        bubble = QPainterPath()  # type: QPainterPath
        bubble.addRoundedRect(QRectF(bx, by, bw, bh), 12, 12)
        tail = QPainterPath()  # type: QPainterPath
        tail.moveTo(bx + 2.0, by + bh * 0.4)
        tail.lineTo(bx - 10.0, by + bh * 0.6)
        tail.lineTo(bx + 2.0, by + bh * 0.72)
        tail.closeSubpath()
        p.setPen(QPen(QColor(20, 20, 30, 60), 1.2))
        p.setBrush(QColor('#FFFFFF'))
        p.drawPath(bubble.united(tail))
        p.setFont(f)
        p.setPen(QColor('#22222A'))
        p.drawText(QRectF(bx + 14.0, by + 9.0, bw - 28.0, bh - 18.0), Qt.TextWordWrap | Qt.AlignVCenter, text)

    # ---------- Properties ----------
    state = pyqtProperty(int, fget=getState, fset=setState)  # type: pyqtProperty
    comment = pyqtProperty('QString', fget=getComment, fset=setComment)  # type: pyqtProperty
    hatColor = pyqtProperty(QColor, fget=getHatColor, fset=setHatColor)  # type: pyqtProperty
    skinColor = pyqtProperty(QColor, fget=getSkinColor, fset=setSkinColor)  # type: pyqtProperty


class SearchDetectiveWidget(QWidget):
    """
    Search field + detective. Emits searchRequested after a debounce; report results with setResultCount().
    """
    searchRequested = pyqtSignal('QString')  # type: pyqtSignal
    textChanged = pyqtSignal('QString')  # type: pyqtSignal
    returnPressed = pyqtSignal()  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param placeholder: str | unicode | QString
        :param debounce: (int) ms of typing silence before searchRequested is emitted.
        :param searchFunction: (callable | None) text -> int; when given, results are reported automatically.
        :param searchRequested: callable | None
        :param textChanged: callable | None
        :param returnPressed: callable | None
        :param args: any
        :param kwargs: any
        """
        placeholder = kwargs.pop('placeholder', 'Search...')  # type: str
        debounce = kwargs.pop('debounce', 450)  # type: int
        searchFunction = kwargs.pop('searchFunction', None)  # type: callable | None
        searchRequested = kwargs.pop('searchRequested', None)  # type: callable | None
        textChanged = kwargs.pop('textChanged', None)  # type: callable | None
        returnPressed = kwargs.pop('returnPressed', None)  # type: callable | None
        super(SearchDetectiveWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_searchFunction = searchFunction if callable(searchFunction) else None  # type: callable | None
        for sig, cb in ((self.searchRequested, searchRequested), (self.textChanged, textChanged),
                        (self.returnPressed, returnPressed)):
            if callable(cb):
                sig.connect(cb)
        # Children.
        self.__m_face = DetectiveFaceWidget()  # type: DetectiveFaceWidget
        self.__m_edit = QLineEdit()  # type: QLineEdit
        self.__m_edit.setObjectName('searchDetectiveEdit')
        self.__m_edit.setPlaceholderText(placeholder)
        self.__m_edit.setClearButtonEnabled(True)
        self.__m_edit.setMinimumHeight(34)
        layout = QVBoxLayout(self)  # type: QVBoxLayout
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.__m_face, 1)
        layout.addWidget(self.__m_edit)
        # Debounce + fake investigation delay.
        self.__m_debounce = QTimer(self)  # type: QTimer
        self.__m_debounce.setSingleShot(True)
        self.__m_debounce.setInterval(max(0, int(debounce)))
        self.__m_debounce.timeout.connect(self._fire)
        self.__m_investigate = QTimer(self)  # type: QTimer
        self.__m_investigate.setSingleShot(True)
        self.__m_investigate.setInterval(900)
        self.__m_investigate.timeout.connect(self._autoResult)
        # Connections.
        self.__m_edit.textChanged.connect(self._onText)
        self.__m_edit.returnPressed.connect(self._onReturn)

    # ---------- Helpers ----------
    @pyqtSlot('QString')
    def _onText(self, text):
        """
        :param text: str | unicode | QString
        :return:
        """
        self.textChanged.emit(text)
        self.__m_investigate.stop()
        if not text.strip():
            self.__m_debounce.stop()
            self.__m_face.setState(IDLE)
            self.__m_face.setComment(choice(LINES[IDLE]))
            return
        if self.__m_face.getState() != TYPING:
            self.__m_face.setState(TYPING)
            self.__m_face.setComment(choice(LINES[TYPING]))
        self.__m_debounce.start()

    @pyqtSlot()
    def _onReturn(self):
        """
        :return:
        """
        self.__m_debounce.stop()
        self._fire()
        self.returnPressed.emit()

    @pyqtSlot()
    def _fire(self):
        """
        :return:
        """
        text = self.__m_edit.text().strip()  # type: str
        if not text:
            return
        self.__m_face.setState(SEARCHING)
        self.__m_face.setComment(choice(LINES[SEARCHING]))
        self.searchRequested.emit(text)
        if self.__m_searchFunction is not None:
            self.__m_investigate.start()

    @pyqtSlot()
    def _autoResult(self):
        """
        :return:
        """
        try:
            n = int(self.__m_searchFunction(self.__m_edit.text().strip()))  # type: int
        except Exception:
            n = 0  # type: int
        self.setResultCount(n)

    # ---------- Public API ----------
    @pyqtSlot(int)
    def setResultCount(self, count):
        """
        Report the outcome of the search the detective is working on.

        :param count: (int) Number of results.
        :return:
        """
        count = max(0, int(count))  # type: int
        if not self.__m_edit.text().strip():
            return
        if count:
            self.__m_face.setState(FOUND)
            self.__m_face.setComment(self.tr('Elementary! {} result{}.').format(count, '' if count == 1 else 's'))
        else:
            self.__m_face.setState(NONE)
            self.__m_face.setComment(choice(LINES[NONE]))

    def getFace(self):
        """
        :return: DetectiveFaceWidget
        """
        return self.__m_face

    def getLineEdit(self):
        """
        :return: QLineEdit
        """
        return self.__m_edit

    def getText(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_edit.text()

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setText(self, text):
        """
        :param text: str | unicode | QString
        :return:
        """
        self.__m_edit.setText(text)

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

    def getDebounce(self):
        """
        :return: int
        """
        return self.__m_debounce.interval()

    @pyqtSlot(int)
    def setDebounce(self, debounce):
        """
        :param debounce: (int) ms
        :return:
        """
        self.__m_debounce.setInterval(max(0, int(debounce)))

    def getSearchFunction(self):
        """
        :return: callable | None
        """
        return self.__m_searchFunction

    @pyqtSlot(object)
    def setSearchFunction(self, searchFunction):
        """
        :param searchFunction: (callable | None) text -> int
        :return:
        """
        self.__m_searchFunction = searchFunction if callable(searchFunction) else None  # type: callable | None

    # ---------- Properties ----------
    text = pyqtProperty('QString', fget=getText, fset=setText, notify=textChanged)  # type: pyqtProperty
    placeholder = pyqtProperty('QString', fget=getPlaceholder, fset=setPlaceholder)  # type: pyqtProperty
    debounce = pyqtProperty(int, fget=getDebounce, fset=setDebounce)  # type: pyqtProperty
    searchFunction = pyqtProperty(object, fget=getSearchFunction, fset=setSearchFunction)  # type: pyqtProperty
