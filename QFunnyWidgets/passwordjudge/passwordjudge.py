# -*- coding: utf-8 -*-
"""
PasswordJudgeWidget: a password field reviewed live by a powdered-wig judge with a monocle.
His eyes follow your text cursor, his monocle pops off at terrible passwords, he raises an eyebrow at
mediocre ones, beams at strong ones and covers his eyes when you reveal the password.
JudgeFaceWidget is the painted judge and can be used on its own.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtWidgets import QWidget, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QFontMetricsF
from random import choice
from math import sin


def clamp(x, a, b):
    """
    :param x: qreal | float | int
    :param a: qreal | float | int
    :param b: qreal | float | int
    :return: qreal | float | int
    """
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    """
    :param a: qreal | float | int
    :param b: qreal | float | int
    :param t: qreal | float | int
    :return: qreal | float | int
    """
    return a + (b - a) * t


COMMON_PASSWORDS = {'password', 'password1', '123456', '12345678', '123456789', '1234', '12345', 'qwerty',
                    'qwerty123', 'abc123', '111111', 'letmein', 'iloveyou', 'admin', 'welcome', 'monkey',
                    'dragon', 'football', 'sunshine', 'princess', 'passw0rd', 'master'}  # type: set
LEVEL_NAMES = ['Terrible', 'Weak', 'Fair', 'Good', 'Strong']  # type: list[str]
LEVEL_COLORS = ['#E63946', '#F4845F', '#FFD23F', '#9BDB4D', '#3BCEAC']  # type: list[str]
COMMENTS = {
    -1: ["I'm waiting. Impress me."],
    0: ["That's on every hacker's list. Page one.", 'My cat walked on the keyboard and did better.',
        "I've seen stronger passwords on sticky notes."],
    1: ['Weak. Like office coffee.', 'Add some numbers. Live a little.', 'Is that a password or a nap?'],
    2: ['Acceptable. Barely.', 'Getting there. Perhaps a symbol?', 'Hmm. Mildly respectable.'],
    3: ['Ooh. Now we are talking.', 'Respectable. My monocle is intrigued.'],
    4: ["Magnificent. I'm genuinely impressed.", "Bravo! Even I can't guess that.", "Fort Knox called. It's jealous."],
}  # type: dict
REVEAL_COMMENT = "I'm not looking! ...okay, I peeked."  # type: str


def passwordStrength(text, minLength=8):
    """
    Rough, opinionated password scoring.

    :param text: str | unicode | QString
    :param minLength: int
    :return: (int) -1 = empty, 0 = terrible .. 4 = strong
    """
    if not text:
        return -1
    if text.lower() in COMMON_PASSWORDS or len(set(text)) <= 2 or len(text) < 4:
        return 0
    pts = 0  # type: int
    pts += 1 if len(text) >= minLength else 0
    pts += 1 if len(text) >= minLength + 4 else 0
    pts += 1 if any(ch.islower() for ch in text) and any(ch.isupper() for ch in text) else 0
    pts += 1 if any(ch.isdigit() for ch in text) else 0
    pts += 1 if any(not ch.isalnum() for ch in text) else 0
    if len(text) < minLength:
        return 1
    if pts <= 1:
        return 1
    if pts <= 3:
        return 2
    return 3 if pts == 4 else 4


class JudgeFaceWidget(QWidget):
    """
    The judge: face on the left, verdict bubble and strength meter on the right.
    """

    def __init__(self, *args, **kwargs):
        """
        :param strength: (int) -1..4
        :param comment: (str | unicode | QString) Verdict text.
        :param skinColor: QColor | Qt.GlobalColor | int | str | QString
        :param wigColor: QColor | Qt.GlobalColor | int | str | QString
        :param args: any
        :param kwargs: any
        """
        strength = kwargs.pop('strength', -1)  # type: int
        comment = kwargs.pop('comment', COMMENTS[-1][0])  # type: str
        skinColor = kwargs.pop('skinColor', '#F6C9A8')  # type: QColor
        wigColor = kwargs.pop('wigColor', '#F1EFE9')  # type: QColor
        super(JudgeFaceWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_strength = int(clamp(int(strength), -1, 4))  # type: int
        self.__m_comment = comment  # type: str
        self.__m_skinColor = QColor(skinColor)  # type: QColor
        self.__m_wigColor = QColor(wigColor)  # type: QColor
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        # State.
        self.__m_cover = 0.0  # type: float
        self.__m_coverTarget = 0.0  # type: float
        self.__m_lookX = 0.0  # type: float
        self.__m_lookTarget = 0.0  # type: float
        self.__m_mono = 0.0  # type: float  # 0 = in place, 1 = dropped
        self.__m_monoVel = 0.0  # type: float
        self.__m_meter = 0.0  # type: float
        self.__m_changedAt = -10.0  # type: float
        self.__m_last = 0.0  # type: float
        # Timing.
        self.__m_clock = QElapsedTimer()  # type: QElapsedTimer
        self.__m_clock.start()
        self.__m_timer = QTimer(self)  # type: QTimer
        self.__m_timer.timeout.connect(self._tick)
        self.__m_timer.start(16)

    # ---------- Public API ----------
    def getStrength(self):
        """
        :return: int
        """
        return self.__m_strength

    @pyqtSlot(int)
    def setStrength(self, strength):
        """
        :param strength: (int) -1..4
        :return:
        """
        strength = int(clamp(int(strength), -1, 4))  # type: int
        if strength != self.__m_strength:
            self.__m_strength = strength  # type: int
            self.__m_changedAt = self.__m_clock.elapsed() / 1000.0  # type: float
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

    def isCovering(self):
        """
        :return: bool
        """
        return self.__m_coverTarget > 0.5

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setCovering(self, covering):
        """
        :param covering: bool
        :return:
        """
        self.__m_coverTarget = 1.0 if covering else 0.0  # type: float

    def getLook(self):
        """
        :return: qreal | float | int
        """
        return self.__m_lookTarget

    @pyqtSlot('qreal')
    @pyqtSlot(float)
    @pyqtSlot(int)
    def setLook(self, look):
        """
        :param look: (qreal | float | int) -1 = left .. 1 = right
        :return:
        """
        self.__m_lookTarget = float(clamp(float(look), -1.0, 1.0))  # type: float

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
        if self.__m_skinColor != color:
            self.__m_skinColor = color  # type: QColor
            self.update()

    def getWigColor(self):
        """
        :return: QColor
        """
        return self.__m_wigColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setWigColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        if self.__m_wigColor != color:
            self.__m_wigColor = color  # type: QColor
            self.update()

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(400, 150)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(240, 100)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(JudgeFaceWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(JudgeFaceWidget, self).hideEvent(event)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self.__m_clock.elapsed() / 1000.0  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        self.__m_cover += (self.__m_coverTarget - self.__m_cover) * min(1.0, dt * 9.0)
        self.__m_lookX += (self.__m_lookTarget - self.__m_lookX) * min(1.0, dt * 12.0)
        monoTarget = 1.0 if self.__m_strength == 0 else 0.0  # type: float
        # Bouncy monocle on its chain.
        self.__m_monoVel += ((monoTarget - self.__m_mono) * 140.0 - self.__m_monoVel * 6.0) * dt
        self.__m_mono += self.__m_monoVel * dt
        meterTarget = (self.__m_strength + 1) / 5.0 if self.__m_strength >= 0 else 0.0  # type: float
        self.__m_meter += (meterTarget - self.__m_meter) * min(1.0, dt * 8.0)
        self.update()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        now = self.__m_clock.elapsed() / 1000.0  # type: float
        w = float(self.width())  # type: float
        h = float(self.height())  # type: float
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        R = min(h * 0.4, w * 0.18)  # type: float
        fc = QPointF(R * 1.25, h / 2.0 + R * 0.05)  # type: QPointF
        # Disgust = head shake, delight = little hop.
        since = now - self.__m_changedAt  # type: float
        p.save()
        if self.__m_strength == 0 and since < 0.8:
            p.translate(sin(since * 30.0) * R * 0.06 * (1.0 - since / 0.8), 0)
        elif self.__m_strength == 4 and since < 0.6:
            p.translate(0, -abs(sin(since * 12.0)) * R * 0.1)
        self._drawJudge(p, fc, R, now)
        p.restore()
        self._drawVerdict(p, QRectF(fc.x() + R * 1.45, 4.0, w - fc.x() - R * 1.45 - 4.0, h - 8.0), now)
        p.end()

    def _drawJudge(self, p, c, R, now):
        """
        :param p: QPainter
        :param c: (QPointF) face center
        :param R: (qreal | float | int) face radius
        :param now: qreal | float | int
        :return:
        """
        s = self.__m_strength  # type: int
        wig = self.__m_wigColor  # type: QColor
        skin = self.__m_skinColor  # type: QColor
        wigPen = QPen(wig.darker(135), max(1.0, R * 0.03))  # type: QPen
        # Wig rolls behind the head.
        p.setPen(wigPen)
        p.setBrush(wig)
        for d in (-1.0, 1.0):
            for k in range(3):
                p.drawEllipse(QPointF(c.x() + d * R * 0.92, c.y() - R * 0.2 + k * R * 0.42), R * 0.26, R * 0.22)
        # Head.
        p.setPen(QPen(skin.darker(130), max(1.0, R * 0.03)))
        p.setBrush(skin)
        p.drawEllipse(c, R * 0.78, R * 0.9)
        # Wig cap.
        cap = QPainterPath()  # type: QPainterPath
        cap.moveTo(c.x() - R * 0.95, c.y() - R * 0.15)
        cap.cubicTo(c.x() - R * 1.0, c.y() - R * 1.25, c.x() + R * 1.0, c.y() - R * 1.25, c.x() + R * 0.95, c.y() - R * 0.15)
        cap.cubicTo(c.x() + R * 0.6, c.y() - R * 0.55, c.x() - R * 0.6, c.y() - R * 0.55, c.x() - R * 0.95, c.y() - R * 0.15)
        p.setPen(wigPen)
        p.setBrush(wig)
        p.drawPath(cap)
        p.setBrush(Qt.NoBrush)
        for k in range(4):
            x = c.x() - R * 0.55 + k * R * 0.37  # type: float
            p.drawArc(QRectF(x - R * 0.16, c.y() - R * 0.92, R * 0.32, R * 0.26), 20 * 16, 140 * 16)
        ink = QColor('#2B2B33')  # type: QColor
        ex = R * 0.3  # type: float
        ey = c.y() - R * 0.08  # type: float
        er = R * (0.17 if s == 4 else 0.14)  # type: float
        # Eyes.
        for d in (-1.0, 1.0):
            x = c.x() + d * ex  # type: float
            p.setPen(QPen(skin.darker(140), max(1.0, R * 0.02)))
            p.setBrush(QColor('#FFFFFF'))
            p.drawEllipse(QPointF(x, ey), er, er * 1.05)
            p.setPen(Qt.NoPen)
            p.setBrush(ink)
            p.drawEllipse(QPointF(x + self.__m_lookX * er * 0.45, ey + er * 0.15), er * 0.5, er * 0.55)
            # Unimpressed half-lids.
            if s in (0, 1):
                lid = QPainterPath()  # type: QPainterPath
                lid.addRect(QRectF(x - er * 1.1, ey - er * 1.2, er * 2.2, er * (1.15 if s == 1 else 0.9)))
                eye = QPainterPath()  # type: QPainterPath
                eye.addEllipse(QPointF(x, ey), er * 1.02, er * 1.07)
                p.fillPath(lid.intersected(eye), skin.darker(104))
        # Eyebrows.
        bp = QPen(wig.darker(160), max(1.5, R * 0.07), Qt.SolidLine, Qt.RoundCap)  # type: QPen
        p.setPen(bp)
        for d in (-1.0, 1.0):
            x = c.x() + d * ex  # type: float
            by = ey - er * 1.5  # type: float
            if s == 0:      # angry
                p.drawLine(QPointF(x + d * er, by - er * 0.4), QPointF(x - d * er * 0.9, by + er * 0.35))
            elif s == 1:    # flat, unimpressed
                p.drawLine(QPointF(x - er, by + er * 0.2), QPointF(x + er, by + er * 0.2))
            elif s == 2:    # one eyebrow raised (monocle side)
                lift = er * 0.7 if d > 0 else 0.0  # type: float
                p.drawLine(QPointF(x - er, by - lift), QPointF(x + er, by - lift - (er * 0.2 if d > 0 else 0)))
            elif s >= 3:    # both raised
                lift = er * (0.5 if s == 3 else 0.9)  # type: float
                p.drawArc(QRectF(x - er, by - lift - er * 0.2, er * 2.0, er * 0.8), 20 * 16, 140 * 16)
            else:           # neutral
                p.drawLine(QPointF(x - er, by), QPointF(x + er, by - er * 0.1))
        # Nose.
        p.setPen(QPen(skin.darker(150), max(1.0, R * 0.04), Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        p.drawArc(QRectF(c.x() - R * 0.08, c.y() + R * 0.02, R * 0.16, R * 0.18), 200 * 16, 200 * 16)
        # Mouth (under the mustache).
        my = c.y() + R * 0.5  # type: float
        mp = QPen(QColor('#7A3A2E'), max(1.2, R * 0.05), Qt.SolidLine, Qt.RoundCap)  # type: QPen
        p.setPen(mp)
        if s == 4:
            p.setBrush(QColor('#7A3A2E'))
            o = 1.0 + 0.1 * sin(now * 6.0)  # type: float
            p.drawEllipse(QPointF(c.x(), my), R * 0.1 * o, R * 0.12 * o)
        elif s == 3:
            p.drawArc(QRectF(c.x() - R * 0.18, my - R * 0.12, R * 0.36, R * 0.18), 200 * 16, 140 * 16)
        elif s in (0, 1):
            path = QPainterPath()  # type: QPainterPath
            path.moveTo(c.x() - R * 0.18, my + R * 0.06)
            path.cubicTo(c.x() - R * 0.06, my - R * 0.08, c.x() + R * 0.06, my + R * 0.06, c.x() + R * 0.18, my - R * 0.02)
            p.drawPath(path)
        else:
            p.drawLine(QPointF(c.x() - R * 0.14, my), QPointF(c.x() + R * 0.14, my + (R * 0.03 if s == 2 else 0)))
        # Handlebar mustache, twitching when annoyed.
        twitch = sin(now * 25.0) * R * 0.02 if s == 0 else 0.0  # type: float
        mc = wig.darker(150)  # type: QColor
        p.setPen(Qt.NoPen)
        p.setBrush(mc)
        for d in (-1.0, 1.0):
            m = QPainterPath()  # type: QPainterPath
            m.moveTo(c.x(), c.y() + R * 0.3)
            m.cubicTo(c.x() + d * R * 0.2, c.y() + R * 0.22, c.x() + d * R * 0.42, c.y() + R * 0.42,
                      c.x() + d * R * 0.5, c.y() + R * 0.22 + twitch)
            m.cubicTo(c.x() + d * R * 0.52, c.y() + R * 0.3, c.x() + d * R * 0.38, c.y() + R * 0.44, c.x(), c.y() + R * 0.38)
            m.closeSubpath()
            p.drawPath(m)
        # Blush when impressed.
        if s >= 3:
            bc = QColor('#FF8FA3')  # type: QColor
            bc.setAlpha(110)
            p.setBrush(bc)
            for d in (-1.0, 1.0):
                p.drawEllipse(QPointF(c.x() + d * R * 0.52, c.y() + R * 0.18), R * 0.12, R * 0.07)
        # Monocle on the right eye, hanging from a chain when dropped.
        gold = QColor('#D4A72C')  # type: QColor
        anchor = QPointF(c.x() + R * 0.65, c.y() + R * 0.95)  # type: QPointF
        mono = QPointF(c.x() + ex + self.__m_mono * R * 0.25, ey + self.__m_mono * R * 0.95)  # type: QPointF
        chain = QPainterPath()  # type: QPainterPath
        chain.moveTo(mono.x() + R * 0.12, mono.y() + R * 0.14)
        chain.quadTo(QPointF(anchor.x() + R * 0.15, (mono.y() + anchor.y()) / 2.0 + R * 0.3), anchor)
        p.setPen(QPen(gold, max(1.0, R * 0.025)))
        p.setBrush(Qt.NoBrush)
        p.drawPath(chain)
        glass = QColor(200, 230, 255, 70)  # type: QColor
        p.setPen(QPen(gold, max(1.5, R * 0.05)))
        p.setBrush(glass)
        p.drawEllipse(mono, R * 0.22, R * 0.22)
        p.setPen(QPen(QColor(255, 255, 255, 180), max(1.0, R * 0.025)))
        p.drawArc(QRectF(mono.x() - R * 0.14, mono.y() - R * 0.14, R * 0.28, R * 0.28), 100 * 16, 60 * 16)
        # Hands covering the eyes.
        cv = self.__m_cover  # type: float
        if cv > 0.01:
            p.setPen(QPen(skin.darker(135), max(1.0, R * 0.03)))
            p.setBrush(skin)
            for d in (-1.0, 1.0):
                peek = R * 0.18 * max(0.0, sin(now * 1.3)) ** 8 if d > 0 else 0.0  # type: float
                hy = lerp(c.y() + R * 1.8, ey + peek, cv)  # type: float
                hx = c.x() + d * ex  # type: float
                hand = QRectF(hx - R * 0.3, hy - R * 0.22, R * 0.6, R * 0.6)  # type: QRectF
                p.drawRoundedRect(hand, R * 0.18, R * 0.18)
                for k in range(1, 4):
                    fx = hand.left() + hand.width() * k / 4.0  # type: float
                    p.drawLine(QPointF(fx, hand.top() + R * 0.04), QPointF(fx, hand.top() + R * 0.22))

    def _drawVerdict(self, p, area, now):
        """
        :param p: QPainter
        :param area: (QRectF) space right of the face
        :param now: qreal | float | int
        :return:
        """
        if area.width() < 60:
            return
        s = self.__m_strength  # type: int
        f = QFont(self.font())  # type: QFont
        f.setPointSizeF(clamp(area.height() * 0.09, 8.5, 11.0))
        f.setItalic(True)
        fm = QFontMetricsF(f)  # type: QFontMetricsF
        meterH = 34.0  # type: float
        maxW = area.width() - 14.0  # type: float
        br = fm.boundingRect(QRectF(0, 0, maxW - 24.0, 1000.0), Qt.TextWordWrap, self.__m_comment)  # type: QRectF
        bw = min(maxW, br.width() + 26.0)  # type: float
        bh = br.height() + 18.0  # type: float
        bx = area.left() + 12.0  # type: float
        by = area.top() + max(0.0, (area.height() - meterH - bh) / 2.0)  # type: float
        since = now - self.__m_changedAt  # type: float
        pop = 1.0 + 0.06 * max(0.0, 1.0 - since * 4.0)  # type: float
        p.save()
        p.translate(bx, by + bh / 2.0)
        p.scale(pop, pop)
        p.translate(-bx, -(by + bh / 2.0))
        bubble = QPainterPath()  # type: QPainterPath
        bubble.addRoundedRect(QRectF(bx, by, bw, bh), 12, 12)
        tail = QPainterPath()  # type: QPainterPath
        tail.moveTo(bx + 2.0, by + bh * 0.4)
        tail.lineTo(bx - 10.0, by + bh * 0.55)
        tail.lineTo(bx + 2.0, by + bh * 0.7)
        tail.closeSubpath()
        bubble = bubble.united(tail)  # type: QPainterPath
        p.setPen(QPen(QColor(20, 20, 30, 60), 1.2))
        p.setBrush(QColor('#FFFFFF'))
        p.drawPath(bubble)
        p.setFont(f)
        p.setPen(QColor('#22222A'))
        p.drawText(QRectF(bx + 13.0, by + 9.0, bw - 26.0, bh - 18.0), Qt.TextWordWrap | Qt.AlignVCenter, self.__m_comment)
        p.restore()
        # Strength meter.
        my = by + bh + 12.0  # type: float
        segW = (min(area.width() - 12.0, 260.0) - 4 * 5.0) / 5.0  # type: float
        lit = self.__m_meter * 5.0  # type: float
        col = QColor(LEVEL_COLORS[s]) if s >= 0 else QColor(127, 127, 127)  # type: QColor
        p.setPen(Qt.NoPen)
        for k in range(5):
            r = QRectF(bx + k * (segW + 5.0), my, segW, 6.0)  # type: QRectF
            off = QColor(127, 127, 127, 70)  # type: QColor
            p.setBrush(off)
            p.drawRoundedRect(r, 3, 3)
            amt = clamp(lit - k, 0.0, 1.0)  # type: float
            if amt > 0:
                p.setBrush(col)
                p.drawRoundedRect(QRectF(r.left(), r.top(), r.width() * amt, r.height()), 3, 3)
        if s >= 0:
            lf = QFont(self.font())  # type: QFont
            lf.setBold(True)
            lf.setPointSizeF(8.5)
            p.setFont(lf)
            p.setPen(col)
            p.drawText(QRectF(bx, my + 9.0, 200.0, 16.0), Qt.AlignLeft | Qt.AlignVCenter, LEVEL_NAMES[s])

    # ---------- Properties ----------
    strength = pyqtProperty(int, fget=getStrength, fset=setStrength)  # type: pyqtProperty
    comment = pyqtProperty('QString', fget=getComment, fset=setComment)  # type: pyqtProperty
    covering = pyqtProperty(bool, fget=isCovering, fset=setCovering)  # type: pyqtProperty
    look = pyqtProperty('qreal', fget=getLook, fset=setLook)  # type: pyqtProperty
    skinColor = pyqtProperty(QColor, fget=getSkinColor, fset=setSkinColor)  # type: pyqtProperty
    wigColor = pyqtProperty(QColor, fget=getWigColor, fset=setWigColor)  # type: pyqtProperty


class PasswordJudgeWidget(QWidget):
    """
    Password field + judge + show/hide toggle.
    """
    strengthChanged = pyqtSignal(int)  # type: pyqtSignal
    textChanged = pyqtSignal('QString')  # type: pyqtSignal
    returnPressed = pyqtSignal()  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param text: str | unicode | QString
        :param placeholder: str | unicode | QString
        :param minLength: (int) Length the judge considers decent.
        :param showToggle: (bool) Show the reveal button.
        :param revealed: (bool) Show the password in clear text.
        :param strengthChanged: callable | None
        :param textChanged: callable | None
        :param returnPressed: callable | None
        :param args: any
        :param kwargs: any
        """
        text = kwargs.pop('text', '')  # type: str
        placeholder = kwargs.pop('placeholder', 'Enter a password')  # type: str
        minLength = kwargs.pop('minLength', 8)  # type: int
        showToggle = kwargs.pop('showToggle', True)  # type: bool
        revealed = kwargs.pop('revealed', False)  # type: bool
        strengthChanged = kwargs.pop('strengthChanged', None)  # type: callable | None
        textChanged = kwargs.pop('textChanged', None)  # type: callable | None
        returnPressed = kwargs.pop('returnPressed', None)  # type: callable | None
        super(PasswordJudgeWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_minLength = max(1, int(minLength))  # type: int
        self.__m_strength = -1  # type: int
        for sig, cb in ((self.strengthChanged, strengthChanged), (self.textChanged, textChanged),
                        (self.returnPressed, returnPressed)):
            if callable(cb):
                sig.connect(cb)
        # Children.
        self.__m_face = JudgeFaceWidget()  # type: JudgeFaceWidget
        self.__m_edit = QLineEdit()  # type: QLineEdit
        self.__m_edit.setObjectName('passwordJudgeEdit')
        self.__m_edit.setEchoMode(QLineEdit.Password)
        self.__m_edit.setPlaceholderText(placeholder)
        self.__m_edit.setMinimumHeight(34)
        self.__m_toggle = QPushButton(self.tr('Show'))  # type: QPushButton
        self.__m_toggle.setObjectName('passwordJudgeToggle')
        self.__m_toggle.setCheckable(True)
        self.__m_toggle.setCursor(Qt.PointingHandCursor)
        self.__m_toggle.setMinimumHeight(34)
        self.__m_toggle.setVisible(bool(showToggle))
        row = QHBoxLayout()  # type: QHBoxLayout
        row.setSpacing(8)
        row.addWidget(self.__m_edit, 1)
        row.addWidget(self.__m_toggle)
        layout = QVBoxLayout(self)  # type: QVBoxLayout
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.__m_face, 1)
        layout.addLayout(row)
        # Connections.
        self.__m_edit.textChanged.connect(self._onText)
        self.__m_edit.cursorPositionChanged.connect(self._onCursor)
        self.__m_edit.returnPressed.connect(self.returnPressed)
        self.__m_toggle.toggled.connect(self.setRevealed)
        self.__m_edit.setText(text)
        self.setRevealed(revealed)

    # ---------- Helpers ----------
    def _comment(self):
        """
        :return: str | unicode | QString
        """
        if self.isRevealed() and self.__m_edit.text():
            return REVEAL_COMMENT
        return choice(COMMENTS[self.__m_strength])

    @pyqtSlot('QString')
    def _onText(self, text):
        """
        :param text: str | unicode | QString
        :return:
        """
        strength = passwordStrength(text, self.__m_minLength)  # type: int
        if strength != self.__m_strength:
            self.__m_strength = strength  # type: int
            self.__m_face.setStrength(strength)
            self.__m_face.setComment(self._comment())
            self.strengthChanged.emit(strength)
        self.__m_face.setCovering(self.isRevealed() and bool(text))
        if self.isRevealed() and text:
            self.__m_face.setComment(REVEAL_COMMENT)
        self.textChanged.emit(text)

    @pyqtSlot(int, int)
    def _onCursor(self, old, new):
        """
        :param old: int
        :param new: int
        :return:
        """
        x = self.__m_edit.cursorRect().center().x()  # type: int
        self.__m_face.setLook((x / float(max(1, self.__m_edit.width()))) * 2.0 - 1.0)

    # ---------- Public API ----------
    def getStrength(self):
        """
        :return: (int) -1 = empty, 0..4
        """
        return self.__m_strength

    def getFace(self):
        """
        :return: JudgeFaceWidget
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

    def getMinLength(self):
        """
        :return: int
        """
        return self.__m_minLength

    @pyqtSlot(int)
    def setMinLength(self, minLength):
        """
        :param minLength: int
        :return:
        """
        self.__m_minLength = max(1, int(minLength))  # type: int
        self.__m_strength = -2  # type: int  # force re-evaluation
        self._onText(self.__m_edit.text())

    def isShowToggle(self):
        """
        :return: bool
        """
        return not self.__m_toggle.isHidden()

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setShowToggle(self, showToggle):
        """
        :param showToggle: bool
        :return:
        """
        self.__m_toggle.setVisible(bool(showToggle))

    def isRevealed(self):
        """
        :return: bool
        """
        return self.__m_edit.echoMode() == QLineEdit.Normal

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setRevealed(self, revealed):
        """
        :param revealed: bool
        :return:
        """
        revealed = bool(revealed)  # type: bool
        self.__m_edit.setEchoMode(QLineEdit.Normal if revealed else QLineEdit.Password)
        if self.__m_toggle.isChecked() != revealed:
            self.__m_toggle.setChecked(revealed)
        self.__m_toggle.setText(self.tr('Hide') if revealed else self.tr('Show'))
        has = bool(self.__m_edit.text())  # type: bool
        self.__m_face.setCovering(revealed and has)
        self.__m_face.setComment(REVEAL_COMMENT if revealed and has else choice(COMMENTS[max(-1, self.__m_strength)]))

    # ---------- Properties ----------
    text = pyqtProperty('QString', fget=getText, fset=setText, notify=textChanged)  # type: pyqtProperty
    placeholder = pyqtProperty('QString', fget=getPlaceholder, fset=setPlaceholder)  # type: pyqtProperty
    minLength = pyqtProperty(int, fget=getMinLength, fset=setMinLength)  # type: pyqtProperty
    showToggle = pyqtProperty(bool, fget=isShowToggle, fset=setShowToggle)  # type: pyqtProperty
    revealed = pyqtProperty(bool, fget=isRevealed, fset=setRevealed)  # type: pyqtProperty
