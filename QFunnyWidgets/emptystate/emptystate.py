# -*- coding: utf-8 -*-
"""
EmptyStateWidget: the "nothing here yet" placeholder for empty lists, inboxes and search results,
set in a tiny desert. A tumbleweed bounces across the screen, a cactus stands guard, crickets chirp,
and a call-to-action button invites the user to finally put something here.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QFontMetricsF, QLinearGradient
from ManyQt.QtWidgets import QWidget
from random import Random
from math import sin, pi


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


class EmptyStateWidget(QWidget):
    """
    Desert-themed empty state with a rolling tumbleweed.
    """
    actionClicked = pyqtSignal()  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param title: str | unicode | QString
        :param subtitle: str | unicode | QString
        :param actionText: (str | unicode | QString) Button label; empty hides the button.
        :param accentColor: QColor | Qt.GlobalColor | int | str | QString
        :param sandColor: QColor | Qt.GlobalColor | int | str | QString
        :param speed: (qreal | float | int) Tumbleweed speed multiplier.
        :param actionClicked: callable | None
        :param args: any
        :param kwargs: any
        """
        title = kwargs.pop('title', 'Nothing here yet')  # type: str
        subtitle = kwargs.pop('subtitle', 'Just us tumbleweeds. Add something to get started.')  # type: str
        actionText = kwargs.pop('actionText', 'Add item')  # type: str
        accentColor = kwargs.pop('accentColor', '#5E60CE')  # type: QColor
        sandColor = kwargs.pop('sandColor', '#E9C46A')  # type: QColor
        speed = kwargs.pop('speed', 1.0)  # type: float
        actionClicked = kwargs.pop('actionClicked', None)  # type: callable | None
        super(EmptyStateWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_title = title  # type: str
        self.__m_subtitle = subtitle  # type: str
        self.__m_actionText = actionText  # type: str
        self.__m_accentColor = QColor(accentColor)  # type: QColor
        self.__m_sandColor = QColor(sandColor)  # type: QColor
        self.__m_speed = max(0.05, float(speed))  # type: float
        if callable(actionClicked):
            self.actionClicked.connect(actionClicked)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        # State: tumbleweed made of random loops (seeded so it always looks the same).
        rnd = Random(7)  # type: Random
        self.__m_loops = [(rnd.uniform(-0.35, 0.35), rnd.uniform(-0.35, 0.35), rnd.uniform(0.35, 0.65),
                           rnd.uniform(0.25, 0.55), rnd.uniform(0, 180)) for _ in range(14)]  # type: list[tuple]
        self.__m_btnRect = QRectF()  # type: QRectF
        self.__m_btnHover = False  # type: bool
        self.__m_btnPress = False  # type: bool
        # Timing.
        self.__m_clock = QElapsedTimer()  # type: QElapsedTimer
        self.__m_clock.start()
        self.__m_timer = QTimer(self)  # type: QTimer
        self.__m_timer.timeout.connect(self.update)
        self.__m_timer.start(16)

    # ---------- Helpers ----------
    def _now(self):
        """
        :return: qreal | float | int
        """
        return self.__m_clock.elapsed() / 1000.0

    # ---------- Public API ----------
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

    def getSubtitle(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_subtitle

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setSubtitle(self, subtitle):
        """
        :param subtitle: str | unicode | QString
        :return:
        """
        self.__m_subtitle = subtitle  # type: str
        self.update()

    def getActionText(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_actionText

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setActionText(self, actionText):
        """
        :param actionText: str | unicode | QString
        :return:
        """
        self.__m_actionText = actionText  # type: str
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

    def getSandColor(self):
        """
        :return: QColor
        """
        return self.__m_sandColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setSandColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        if self.__m_sandColor != color:
            self.__m_sandColor = color  # type: QColor
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
        self.__m_speed = max(0.05, float(speed))  # type: float

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(420, 300)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(220, 180)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(EmptyStateWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(EmptyStateWidget, self).hideEvent(event)

    def mouseMoveEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        hover = self.__m_btnRect.contains(eventPos(e))  # type: bool
        if hover != self.__m_btnHover:
            self.__m_btnHover = hover  # type: bool
            self.setCursor(Qt.PointingHandCursor if hover else Qt.ArrowCursor)
        super(EmptyStateWidget, self).mouseMoveEvent(e)

    def mousePressEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if e.button() == Qt.LeftButton and self.__m_btnRect.contains(eventPos(e)):
            self.__m_btnPress = True  # type: bool
        super(EmptyStateWidget, self).mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if self.__m_btnPress and self.__m_btnRect.contains(eventPos(e)):
            self.actionClicked.emit()
        self.__m_btnPress = False  # type: bool
        super(EmptyStateWidget, self).mouseReleaseEvent(e)

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        now = self._now()  # type: float
        w = float(self.width())  # type: float
        h = float(self.height())  # type: float
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        ground = h * 0.8  # type: float
        unit = clamp(min(w, h) / 10.0, 8.0, 40.0)  # type: float
        self._drawScene(p, w, h, ground, unit, now)
        self._drawText(p, w, ground, unit)
        p.end()

    def _drawScene(self, p, w, h, ground, unit, now):
        """
        :param p: QPainter
        :param w: qreal | float | int
        :param h: qreal | float | int
        :param ground: (qreal | float | int) horizon y
        :param unit: (qreal | float | int) scene scale
        :param now: qreal | float | int
        :return:
        """
        sand = self.__m_sandColor  # type: QColor
        # Setting sun, half hidden behind the dunes.
        sun = QColor('#FFB703')  # type: QColor
        sun.setAlpha(60)
        p.setPen(Qt.NoPen)
        p.setBrush(sun)
        p.drawEllipse(QPointF(w * 0.16, ground - unit * 0.15), unit * 1.0, unit * 1.0)
        sun.setAlpha(150)
        p.setBrush(sun)
        p.drawEllipse(QPointF(w * 0.16, ground - unit * 0.15), unit * 0.65, unit * 0.65)
        # Dunes.
        dune = QPainterPath()  # type: QPainterPath
        dune.moveTo(0, h)
        dune.lineTo(0, ground)
        dune.cubicTo(w * 0.25, ground - unit * 0.6, w * 0.45, ground + unit * 0.25, w * 0.7, ground - unit * 0.35)
        dune.cubicTo(w * 0.85, ground - unit * 0.6, w * 0.95, ground, w, ground - unit * 0.1)
        dune.lineTo(w, h)
        dune.closeSubpath()
        grad = QLinearGradient(QPointF(0, ground - unit), QPointF(0, h))  # type: QLinearGradient
        top = QColor(sand)  # type: QColor
        top.setAlpha(170)
        bottom = QColor(sand.darker(130))  # type: QColor
        bottom.setAlpha(120)
        grad.setColorAt(0.0, top)
        grad.setColorAt(1.0, bottom)
        p.setBrush(grad)
        p.drawPath(dune)
        # Cactus.
        cx = w * 0.82  # type: float
        cbase = ground + unit * 0.05  # type: float
        cg = QColor('#2A9D8F')  # type: QColor
        pen = QPen(cg.darker(130), max(1.0, unit * 0.06))  # type: QPen
        p.setPen(pen)
        p.setBrush(cg)
        cw = unit * 0.55  # type: float
        ch = unit * 2.6  # type: float
        p.drawRoundedRect(QRectF(cx - cw / 2.0, cbase - ch, cw, ch + 2.0), cw / 2.0, cw / 2.0)
        sway = sin(now * 1.3) * unit * 0.05  # type: float
        arm = QPainterPath()  # type: QPainterPath
        arm.addRoundedRect(QRectF(cx - cw * 1.6 + sway, cbase - ch * 0.78, cw * 0.5, ch * 0.42), cw * 0.25, cw * 0.25)
        arm.addRoundedRect(QRectF(cx - cw * 1.6 + sway, cbase - ch * 0.42, cw * 1.2, cw * 0.45), cw * 0.22, cw * 0.22)
        arm.addRoundedRect(QRectF(cx + cw * 1.1 - sway, cbase - ch * 0.62, cw * 0.5, ch * 0.32), cw * 0.25, cw * 0.25)
        arm.addRoundedRect(QRectF(cx + cw * 0.4 - sway, cbase - ch * 0.35, cw * 1.2, cw * 0.45), cw * 0.22, cw * 0.22)
        p.drawPath(arm.simplified())
        # Cactus face: bored.
        ink = QColor('#1D3B36')  # type: QColor
        p.setPen(QPen(ink, max(1.0, unit * 0.06), Qt.SolidLine, Qt.RoundCap))
        fy = cbase - ch * 0.75  # type: float
        for d in (-1.0, 1.0):
            p.drawLine(QPointF(cx + d * cw * 0.2 - cw * 0.08, fy), QPointF(cx + d * cw * 0.2 + cw * 0.08, fy))
        p.drawLine(QPointF(cx - cw * 0.12, fy + cw * 0.35), QPointF(cx + cw * 0.12, fy + cw * 0.35))
        # Chirp.
        cyc = (now % 3.2)  # type: float
        if cyc < 1.2:
            f = QFont(self.font())  # type: QFont
            f.setItalic(True)
            f.setPointSizeF(max(6.5, unit * 0.32))
            p.setFont(f)
            tc = QColor(self.palette().text().color())  # type: QColor
            tc.setAlpha(int(170 * sin(cyc / 1.2 * pi)))
            p.setPen(tc)
            word = 'chirp' if int(now / 3.2) % 3 else 'chirp chirp'  # type: str
            p.drawText(QPointF(cx + cw * 1.3, cbase - unit * 0.2 - cyc * unit * 0.3), word)
        # Tumbleweed.
        r = unit * 0.75  # type: float
        speed = unit * 4.5 * self.__m_speed  # type: float
        span = w + 4.0 * r  # type: float
        period = span / speed + 1.5  # type: float  # short pause off-screen between passes
        t = now % period  # type: float
        x = -2.0 * r + t * speed  # type: float
        if x < w + 2.0 * r:
            ph = t * 3.2 * self.__m_speed  # type: float
            hop = abs(sin(ph)) * unit * 0.9 * (0.6 + 0.4 * abs(sin(ph * 0.37)))  # type: float
            y = ground + unit * 0.05 - r - hop  # type: float
            # Shadow.
            sh = QColor(0, 0, 0, int(50 * (1.0 - hop / (unit * 1.2))))  # type: QColor
            p.setPen(Qt.NoPen)
            p.setBrush(sh)
            p.drawEllipse(QPointF(x, ground + unit * 0.08), r * (0.9 - hop / (unit * 4.0)), r * 0.15)
            # Wind streaks.
            wc = QColor(self.palette().text().color())  # type: QColor
            wc.setAlpha(60)
            p.setPen(QPen(wc, max(1.0, unit * 0.05), Qt.SolidLine, Qt.RoundCap))
            for k in range(3):
                ly = y - r * 0.5 + k * r * 0.5  # type: float
                lx = x - r * 1.5 - k * r * 0.3  # type: float
                p.drawLine(QPointF(lx - r * 0.9, ly), QPointF(lx, ly))
            p.save()
            p.translate(x, y)
            p.rotate((x / r) * 180.0 / pi)
            weed = QColor('#A0703A')  # type: QColor
            p.setPen(QPen(weed, max(1.0, unit * 0.05)))
            p.setBrush(Qt.NoBrush)
            for ox, oy, rx, ry, ang in self.__m_loops:
                p.save()
                p.translate(ox * r, oy * r)
                p.rotate(ang)
                p.drawEllipse(QPointF(0, 0), rx * r, ry * r)
                p.restore()
            p.setPen(QPen(weed.darker(120), max(1.0, unit * 0.06)))
            p.drawEllipse(QPointF(0, 0), r * 0.95, r * 0.95)
            p.restore()

    def _drawText(self, p, w, ground, unit):
        """
        :param p: QPainter
        :param w: qreal | float | int
        :param ground: qreal | float | int
        :param unit: qreal | float | int
        :return:
        """
        tf = QFont(self.font())  # type: QFont
        tf.setBold(True)
        tf.setPointSizeF(clamp(unit * 0.55, 11.0, 18.0))
        sf = QFont(self.font())  # type: QFont
        sf.setPointSizeF(clamp(unit * 0.36, 8.5, 11.0))
        tfm = QFontMetricsF(tf)  # type: QFontMetricsF
        sfm = QFontMetricsF(sf)  # type: QFontMetricsF
        tw = min(w - 30.0, 420.0)  # type: float
        sr = sfm.boundingRect(QRectF(0, 0, tw, 500), Qt.TextWordWrap | Qt.AlignHCenter, self.__m_subtitle)  # type: QRectF
        btnH = 34.0 if self.__m_actionText else 0.0  # type: float
        blockH = tfm.height() + 6.0 + sr.height() + (16.0 + btnH if btnH else 0.0)  # type: float
        y = max(8.0, (ground - unit * 1.2 - blockH) / 2.0)  # type: float
        x = (w - tw) / 2.0  # type: float
        tc = QColor(self.palette().text().color())  # type: QColor
        p.setFont(tf)
        p.setPen(tc)
        p.drawText(QRectF(x, y, tw, tfm.height()), Qt.AlignCenter, self.__m_title)
        y += tfm.height() + 6.0
        sub = QColor(tc)  # type: QColor
        sub.setAlpha(165)
        p.setFont(sf)
        p.setPen(sub)
        p.drawText(QRectF(x, y, tw, sr.height()), Qt.TextWordWrap | Qt.AlignHCenter, self.__m_subtitle)
        y += sr.height() + 16.0
        if self.__m_actionText:
            bf = QFont(self.font())  # type: QFont
            bf.setBold(True)
            bf.setPointSizeF(9.5)
            bfm = QFontMetricsF(bf)  # type: QFontMetricsF
            adv = bfm.horizontalAdvance(self.__m_actionText) if hasattr(bfm, 'horizontalAdvance') else bfm.width(self.__m_actionText)  # type: float
            bw = adv + 52.0  # type: float
            rect = QRectF((w - bw) / 2.0, y, bw, btnH)  # type: QRectF
            if self.__m_btnPress:
                rect.adjust(2, 2, -2, -2)
            self.__m_btnRect = rect  # type: QRectF
            ac = self.__m_accentColor.lighter(112) if self.__m_btnHover else self.__m_accentColor  # type: QColor
            p.setPen(Qt.NoPen)
            p.setBrush(ac)
            p.drawRoundedRect(rect, btnH / 2.0, btnH / 2.0)
            p.setFont(bf)
            p.setPen(QColor('#FFFFFF'))
            # "+" icon.
            plus = QPointF(rect.left() + 20.0, rect.center().y())  # type: QPointF
            p.setPen(QPen(QColor('#FFFFFF'), 2.0, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(plus - QPointF(5, 0), plus + QPointF(5, 0))
            p.drawLine(plus - QPointF(0, 5), plus + QPointF(0, 5))
            p.drawText(rect.adjusted(24, 0, -8, 0), Qt.AlignCenter, self.__m_actionText)
        else:
            self.__m_btnRect = QRectF()  # type: QRectF

    # ---------- Properties ----------
    title = pyqtProperty('QString', fget=getTitle, fset=setTitle)  # type: pyqtProperty
    subtitle = pyqtProperty('QString', fget=getSubtitle, fset=setSubtitle)  # type: pyqtProperty
    actionText = pyqtProperty('QString', fget=getActionText, fset=setActionText)  # type: pyqtProperty
    accentColor = pyqtProperty(QColor, fget=getAccentColor, fset=setAccentColor)  # type: pyqtProperty
    sandColor = pyqtProperty(QColor, fget=getSandColor, fset=setSandColor)  # type: pyqtProperty
    speed = pyqtProperty('qreal', fget=getSpeed, fset=setSpeed)  # type: pyqtProperty
