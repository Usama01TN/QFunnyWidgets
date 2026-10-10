# -*- coding: utf-8 -*-
"""
ErrorGremlinWidget: an inline alert banner explaining what went wrong, starring the gremlin
responsible. Info: it naps. Warning: it peeks in, waving a wrench. Error: it is chewing a cable
(sparks included). Critical: it bounces in front of a fire while the banner flashes. Retry scares
it away; the close button fades the banner out.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty, \
    Q_ENUMS, qVersion
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QFontMetricsF
from ManyQt.QtWidgets import QWidget
from enum import IntEnum
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


class Spark(object):
    """
    A spark or a flame.
    """

    def __init__(self, x=0.0, y=0.0, vx=0.0, vy=0.0, life=0.4, kind=0):
        """
        :param x: qreal | float | int
        :param y: qreal | float | int
        :param vx: qreal | float | int
        :param vy: qreal | float | int
        :param life: (qreal | float | int) s
        :param kind: (int) 0 = spark, 1 = flame
        """
        self.x = float(x)  # type: float
        self.y = float(y)  # type: float
        self.vx = float(vx)  # type: float
        self.vy = float(vy)  # type: float
        self.life = float(life)  # type: float
        self.maxLife = float(life)  # type: float
        self.kind = int(kind)  # type: int


class ErrorGremlinWidget(QWidget):
    """
    Alert banner with a gremlin whose mischief matches the severity.
    """

    class Severity(IntEnum):
        """
        Severity enumeration class.
        """
        Info = 0  # type: int
        Warning = 1  # type: int
        Error = 2  # type: int
        Critical = 3  # type: int

    Info = Severity.Info  # type: int
    Warning = Severity.Warning  # type: int
    Error = Severity.Error  # type: int
    Critical = Severity.Critical  # type: int
    COLORS = {0: '#4C9AFF', 1: '#FFB020', 2: '#E63946', 3: '#C9184A'}  # type: dict
    retryClicked = pyqtSignal()  # type: pyqtSignal
    dismissed = pyqtSignal()  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param severity: (Severity | int) Info, Warning, Error or Critical.
        :param title: str | unicode | QString
        :param message: str | unicode | QString
        :param retryText: (str | unicode | QString) Empty hides the retry button.
        :param closable: (bool) Show the close button.
        :param panelColor: QColor | Qt.GlobalColor | int | str | QString
        :param textColor: QColor | Qt.GlobalColor | int | str | QString
        :param retryClicked: callable | None
        :param dismissed: callable | None
        :param args: any
        :param kwargs: any
        """
        severity = kwargs.pop('severity', ErrorGremlinWidget.Error)  # type: int
        title = kwargs.pop('title', 'Something went wrong')  # type: str
        message = kwargs.pop('message', 'A gremlin got into the server room. Our team has been notified.')  # type: str
        retryText = kwargs.pop('retryText', 'Retry')  # type: str
        closable = kwargs.pop('closable', True)  # type: bool
        panelColor = kwargs.pop('panelColor', '#FFFFFF')  # type: QColor
        textColor = kwargs.pop('textColor', '#23232B')  # type: QColor
        retryClicked = kwargs.pop('retryClicked', None)  # type: callable | None
        dismissed = kwargs.pop('dismissed', None)  # type: callable | None
        super(ErrorGremlinWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_severity = ErrorGremlinWidget.Severity(int(clamp(int(severity), 0, 3)))  # type: ErrorGremlinWidget.Severity
        self.__m_title = title  # type: str
        self.__m_message = message  # type: str
        self.__m_retryText = retryText  # type: str
        self.__m_closable = bool(closable)  # type: bool
        self.__m_panelColor = QColor(panelColor)  # type: QColor
        self.__m_textColor = QColor(textColor)  # type: QColor
        if callable(retryClicked):
            self.retryClicked.connect(retryClicked)
        if callable(dismissed):
            self.dismissed.connect(dismissed)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        # State.
        self.__m_retryAt = -10.0  # type: float
        self.__m_closeAt = -1.0  # type: float
        self.__m_changedAt = 0.0  # type: float
        self.__m_retryRect = QRectF()  # type: QRectF
        self.__m_closeRect = QRectF()  # type: QRectF
        self.__m_hoverBtn = 0  # type: int
        self.__m_sparks = []  # type: list[Spark]
        self.__m_sparkAcc = 0.0  # type: float
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

    def _iconRect(self):
        """
        :return: QRectF
        """
        panel = QRectF(self.rect()).adjusted(3, 3, -3, -3)  # type: QRectF
        size = min(panel.height() - 12.0, 96.0)  # type: float
        return QRectF(panel.left() + 14.0, panel.center().y() - size / 2.0, size, size)

    def _fleeing(self):
        """
        :return: (qreal | float | int) 0..1 progress of the gremlin running away (0 when not fleeing)
        """
        since = self._now() - self.__m_retryAt  # type: float
        if since < 1.6:
            return clamp(since / 0.5, 0.0, 1.0)
        return 0.0

    # ---------- Public API ----------
    @pyqtSlot()
    @pyqtSlot(int, 'QString', 'QString')
    @pyqtSlot(int, str, str)
    def showAlert(self, severity=-1, title='', message=''):
        """
        (Re)show the banner, optionally with new content.

        :param severity: (int) -1 keeps the current severity.
        :param title: (str | unicode | QString) Empty keeps the current title.
        :param message: (str | unicode | QString) Empty keeps the current message.
        :return:
        """
        if severity is not None and int(severity) >= 0:
            self.setSeverity(severity)
        if title:
            self.__m_title = title  # type: str
        if message:
            self.__m_message = message  # type: str
        self.__m_closeAt = -1.0  # type: float
        self.__m_retryAt = -10.0  # type: float
        self.show()
        self.update()

    @pyqtSlot()
    def dismiss(self):
        """
        Fade out, then hide.
        :return:
        """
        if self.__m_closeAt < 0:
            self.__m_closeAt = self._now()  # type: float

    def getSeverity(self):
        """
        :return: ErrorGremlinWidget.Severity
        """
        return self.__m_severity

    @pyqtSlot(Severity)
    @pyqtSlot(int)
    def setSeverity(self, severity):
        """
        :param severity: ErrorGremlinWidget.Severity | int
        :return:
        """
        severity = ErrorGremlinWidget.Severity(int(clamp(int(severity), 0, 3)))  # type: ErrorGremlinWidget.Severity
        if severity != self.__m_severity:
            self.__m_severity = severity  # type: ErrorGremlinWidget.Severity
            self.__m_changedAt = self._now()  # type: float
            self.__m_sparks = []  # type: list[Spark]
            self.update()

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

    def getMessage(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_message

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setMessage(self, message):
        """
        :param message: str | unicode | QString
        :return:
        """
        self.__m_message = message  # type: str
        self.update()

    def getRetryText(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_retryText

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setRetryText(self, retryText):
        """
        :param retryText: str | unicode | QString
        :return:
        """
        self.__m_retryText = retryText  # type: str
        self.update()

    def isClosable(self):
        """
        :return: bool
        """
        return self.__m_closable

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setClosable(self, closable):
        """
        :param closable: bool
        :return:
        """
        self.__m_closable = bool(closable)  # type: bool
        self.update()

    def getPanelColor(self):
        """
        :return: QColor
        """
        return self.__m_panelColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setPanelColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        self.__m_panelColor = color  # type: QColor
        self.update()

    def getTextColor(self):
        """
        :return: QColor
        """
        return self.__m_textColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setTextColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        self.__m_textColor = color  # type: QColor
        self.update()

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(520, 110)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(300, 90)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(ErrorGremlinWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(ErrorGremlinWidget, self).hideEvent(event)

    def mouseMoveEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        hover = 1 if self.__m_retryRect.contains(eventPos(e)) else -1 if self.__m_closeRect.contains(eventPos(e)) else 0  # type: int
        if hover != self.__m_hoverBtn:
            self.__m_hoverBtn = hover  # type: int
            self.setCursor(Qt.PointingHandCursor if hover else Qt.ArrowCursor)
        super(ErrorGremlinWidget, self).mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if e.button() == Qt.LeftButton and self.__m_closeAt < 0:
            if self.__m_retryRect.contains(eventPos(e)):
                self.__m_retryAt = self._now()  # type: float
                self.retryClicked.emit()
            elif self.__m_closeRect.contains(eventPos(e)):
                self.dismiss()
        super(ErrorGremlinWidget, self).mouseReleaseEvent(e)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        if self.__m_closeAt >= 0 and now - self.__m_closeAt > 0.35:
            self.__m_closeAt = -1.0  # type: float
            self.hide()
            self.dismissed.emit()
            return
        icon = self._iconRect()  # type: QRectF
        sev = int(self.__m_severity)  # type: int
        if self._fleeing() == 0.0:
            if sev == self.Error:
                self.__m_sparkAcc += dt * 22.0
                while self.__m_sparkAcc > 1.0:
                    self.__m_sparkAcc -= 1.0
                    a = uniform(-pi, 0)  # type: float
                    sp = uniform(50, 140)  # type: float
                    self.__m_sparks.append(Spark(
                        icon.center().x() + icon.width() * 0.12, icon.top() + icon.height() * 0.62,
                        cos(a) * sp, sin(a) * sp, uniform(0.15, 0.35), 0))
            elif sev == self.Critical:
                self.__m_sparkAcc += dt * 30.0
                while self.__m_sparkAcc > 1.0:
                    self.__m_sparkAcc -= 1.0
                    self.__m_sparks.append(Spark(uniform(icon.left() + 6, icon.right() - 6), icon.bottom() - 4,
                                                 0, -uniform(40, 80), uniform(0.4, 0.7), 1))
        alive = []  # type: list[Spark]
        for sp in self.__m_sparks:
            if sp.kind == 0:
                sp.vy += 400.0 * dt
            sp.x += sp.vx * dt + (sin(now * 9.0 + sp.y * 0.2) * 10.0 * dt if sp.kind else 0.0)
            sp.y += sp.vy * dt
            sp.life -= dt
            if sp.life > 0:
                alive.append(sp)
        self.__m_sparks = alive  # type: list[Spark]
        self.update()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        now = self._now()  # type: float
        sev = int(self.__m_severity)  # type: int
        sc = QColor(self.COLORS[sev])  # type: QColor
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        if self.__m_closeAt >= 0:
            p.setOpacity(clamp(1.0 - (now - self.__m_closeAt) / 0.35, 0.0, 1.0))
        panel = QRectF(self.rect()).adjusted(3, 3, -3, -3)  # type: QRectF
        path = QPainterPath()  # type: QPainterPath
        path.addRoundedRect(panel, 12, 12)
        p.fillPath(path, self.__m_panelColor)
        tint = QColor(sc)  # type: QColor
        tint.setAlpha(22)
        p.fillPath(path, tint)
        border = QColor(sc)  # type: QColor
        if sev == self.Critical:
            border.setAlpha(int(120 + 135 * (0.5 + 0.5 * sin(now * 10.0))))
        else:
            border.setAlpha(110)
        p.setPen(QPen(border, 1.5 if sev < 3 else 2.5))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)
        # Severity stripe.
        p.save()
        p.setClipPath(path)
        p.fillRect(QRectF(panel.left(), panel.top(), 6, panel.height()), sc)
        p.restore()
        # Gremlin scene (clipped to its icon box).
        icon = self._iconRect()  # type: QRectF
        ip = QPainterPath()  # type: QPainterPath
        ip.addRoundedRect(icon, 12, 12)
        bg = QColor(sc)  # type: QColor
        bg.setAlpha(30)
        p.fillPath(ip, bg)
        p.save()
        p.setClipPath(ip)
        self._drawScene(p, icon, sev, now)
        p.restore()
        # Buttons.
        tc = self.__m_textColor  # type: QColor
        right = panel.right() - 12.0  # type: float
        if self.__m_closable:
            cr = QRectF(panel.right() - 30.0, panel.top() + 8.0, 22.0, 22.0)  # type: QRectF
            self.__m_closeRect = cr  # type: QRectF
            cc = QColor(tc)  # type: QColor
            cc.setAlpha(200 if self.__m_hoverBtn == -1 else 120)
            p.setPen(QPen(cc, 1.8, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(cr.center() + QPointF(-5, -5), cr.center() + QPointF(5, 5))
            p.drawLine(cr.center() + QPointF(5, -5), cr.center() + QPointF(-5, 5))
            right = cr.left() - 6.0  # type: float
        else:
            self.__m_closeRect = QRectF()  # type: QRectF
        bf = QFont(self.font())  # type: QFont
        bf.setBold(True)
        bf.setPointSizeF(9.0)
        bfm = QFontMetricsF(bf)  # type: QFontMetricsF
        if self.__m_retryText:
            adv = bfm.horizontalAdvance(self.__m_retryText) if hasattr(bfm, 'horizontalAdvance') else bfm.width(self.__m_retryText)  # type: float
            rr = QRectF(right - adv - 28.0, panel.bottom() - 40.0, adv + 28.0, 30.0)  # type: QRectF
            self.__m_retryRect = rr  # type: QRectF
            p.setPen(QPen(sc, 1.5))
            p.setBrush(QColor(sc.red(), sc.green(), sc.blue(), 50 if self.__m_hoverBtn == 1 else 0))
            p.drawRoundedRect(rr, 15, 15)
            p.setFont(bf)
            p.setPen(sc.darker(110) if self.__m_panelColor.lightness() > 128 else sc.lighter(130))
            p.drawText(rr, Qt.AlignCenter, self.__m_retryText)
            textRight = rr.left() - 10.0  # type: float
        else:
            self.__m_retryRect = QRectF()  # type: QRectF
            textRight = right  # type: float
        # Text.
        x0 = icon.right() + 16.0  # type: float
        tw = max(40.0, textRight - x0)  # type: float
        retrying = 0.0 < self._fleeing() or now - self.__m_retryAt < 1.6  # type: bool
        tf = QFont(self.font())  # type: QFont
        tf.setBold(True)
        tf.setPointSizeF(11.0)
        p.setFont(tf)
        p.setPen(tc)
        title = self.tr('Retrying... (the gremlin fled)') if retrying else self.__m_title  # type: str
        p.drawText(QRectF(x0, panel.top() + 12.0, tw, 20.0), Qt.AlignLeft | Qt.AlignVCenter, title)
        mf = QFont(self.font())  # type: QFont
        mf.setPointSizeF(9.0)
        p.setFont(mf)
        sub = QColor(tc)  # type: QColor
        sub.setAlpha(180)
        p.setPen(sub)
        p.drawText(QRectF(x0, panel.top() + 34.0, tw, panel.height() - 42.0), Qt.TextWordWrap | Qt.AlignTop, self.__m_message)
        p.end()

    def _drawScene(self, p, icon, sev, now):
        """
        :param p: QPainter
        :param icon: QRectF
        :param sev: int
        :param now: qreal | float | int
        :return:
        """
        g = icon.width() * 0.5  # type: float
        cx = icon.center().x()  # type: float
        cy = icon.center().y() + g * 0.15  # type: float
        flee = self._fleeing()  # type: float
        # Critical: flames behind.
        if sev == self.Critical:
            for sp in self.__m_sparks:
                if sp.kind != 1:
                    continue
                k = clamp(sp.life / sp.maxLife, 0.0, 1.0)  # type: float
                fc = QColor(255, int(80 + 150 * k), 30)  # type: QColor
                fc.setAlpha(int(200 * k))
                r = g * 0.12 * (0.5 + k)  # type: float
                fl = QPainterPath()  # type: QPainterPath
                fl.moveTo(sp.x, sp.y - r * 2.2)
                fl.cubicTo(sp.x + r, sp.y - r * 0.6, sp.x + r, sp.y + r, sp.x, sp.y + r)
                fl.cubicTo(sp.x - r, sp.y + r, sp.x - r, sp.y - r * 0.6, sp.x, sp.y - r * 2.2)
                p.fillPath(fl, fc)
        # Error: the cable being chewed.
        if sev == self.Error:
            cable = QPainterPath()  # type: QPainterPath
            cy2 = icon.top() + icon.height() * 0.62  # type: float
            cable.moveTo(icon.left() - 4, cy2 + g * 0.1)
            cable.cubicTo(cx - g * 0.4, cy2 - g * 0.1, cx, cy2 + g * 0.1, icon.right() + 4, cy2 - g * 0.05)
            p.setPen(QPen(QColor('#2B2D36'), max(3.0, g * 0.12), Qt.SolidLine, Qt.RoundCap))
            p.setBrush(Qt.NoBrush)
            p.drawPath(cable)
        if flee > 0.0:
            # Scurrying off to the left.
            cx -= flee * icon.width() * 1.1
            cy += -abs(sin(now * 25.0)) * g * 0.08
        elif sev == self.Info:
            cy += g * 0.25
        elif sev == self.Warning:
            cy += g * 0.55 + sin(now * 2.0) * g * 0.05  # only peeking over the bottom edge
        elif sev == self.Critical:
            cy -= abs(sin(now * 9.0)) * g * 0.25
        self._drawGremlin(p, QPointF(cx, cy), g, sev, flee, now)
        # Sparks on top.
        for sp in self.__m_sparks:
            if sp.kind != 0:
                continue
            k = clamp(sp.life / sp.maxLife, 0.0, 1.0)  # type: float
            yc = QColor('#FFD23F')  # type: QColor
            yc.setAlpha(int(255 * k))
            p.setPen(QPen(yc, max(1.2, g * 0.04), Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(sp.x, sp.y), QPointF(sp.x - sp.vx * 0.03, sp.y - sp.vy * 0.03))
        # Info: z.
        if sev == self.Info and flee == 0.0:
            f = QFont(self.font())  # type: QFont
            f.setBold(True)
            ph = (now * 0.5) % 1.0  # type: float
            f.setPointSizeF(max(6.0, g * (0.18 + 0.12 * ph)))
            p.setFont(f)
            zc = QColor(self.COLORS[0])  # type: QColor
            zc.setAlpha(int(230 * sin(ph * pi)))
            p.setPen(zc)
            p.drawText(QPointF(cx + g * 0.45 + ph * g * 0.2, icon.top() + g * 0.55 - ph * g * 0.3), 'z')
        if flee > 0.0 and flee < 1.0:
            f = QFont(self.font())  # type: QFont
            f.setBold(True)
            f.setPointSizeF(max(7.0, g * 0.22))
            p.setFont(f)
            p.setPen(QColor(self.COLORS[sev]))
            p.drawText(QPointF(icon.center().x() - g * 0.2, icon.top() + g * 0.45), self.tr('eep!'))

    def _drawGremlin(self, p, c, g, sev, flee, now):
        """
        :param p: QPainter
        :param c: (QPointF) body center
        :param g: (qreal | float | int) size
        :param sev: int
        :param flee: qreal | float | int
        :param now: qreal | float | int
        :return:
        """
        skin = QColor('#7FA37A')  # type: QColor
        ink = QColor('#1E2A1C')  # type: QColor
        outline = QPen(skin.darker(150), max(1.0, g * 0.04))  # type: QPen
        breathe = 1.0 + 0.04 * sin(now * 2.0) if sev == self.Info else 1.0  # type: float
        # Ears.
        droop = 0.35 if sev == self.Info else 0.0  # type: float
        p.setPen(outline)
        p.setBrush(skin)
        for d in (-1.0, 1.0):
            ear = QPainterPath()  # type: QPainterPath
            ear.moveTo(c.x() + d * g * 0.25, c.y() - g * 0.3)
            ear.lineTo(c.x() + d * g * 0.95, c.y() - g * (0.6 - droop))
            ear.lineTo(c.x() + d * g * 0.42, c.y() - g * 0.05)
            ear.closeSubpath()
            p.drawPath(ear)
            p.setBrush(QColor('#C98B8B'))
            inner = QPainterPath()  # type: QPainterPath
            inner.moveTo(c.x() + d * g * 0.32, c.y() - g * 0.24)
            inner.lineTo(c.x() + d * g * 0.78, c.y() - g * (0.5 - droop))
            inner.lineTo(c.x() + d * g * 0.42, c.y() - g * 0.1)
            inner.closeSubpath()
            p.setPen(Qt.NoPen)
            p.drawPath(inner)
            p.setPen(outline)
            p.setBrush(skin)
        # Head/body blob.
        p.drawEllipse(c, g * 0.48 * breathe, g * 0.42 * breathe)
        # Eyes.
        ex = g * 0.19  # type: float
        ey = c.y() - g * 0.08  # type: float
        if sev == self.Info and flee == 0.0:
            p.setPen(QPen(ink, max(1.0, g * 0.05), Qt.SolidLine, Qt.RoundCap))
            p.setBrush(Qt.NoBrush)
            for d in (-1.0, 1.0):
                p.drawArc(QRectF(c.x() + d * ex - g * 0.1, ey - g * 0.04, g * 0.2, g * 0.12), 180 * 16, 180 * 16)
        else:
            dart = sin(now * 8.0) * g * 0.03 if sev == self.Warning else 0.0  # type: float
            for d in (-1.0, 1.0):
                p.setPen(Qt.NoPen)
                p.setBrush(QColor('#FFE066'))
                p.drawEllipse(QPointF(c.x() + d * ex, ey), g * 0.13, g * 0.12)
                p.setBrush(ink)
                p.drawEllipse(QPointF(c.x() + d * ex + dart - (g * 0.04 if flee else 0.0), ey), g * 0.03, g * 0.09)
            if sev >= self.Error or flee:
                # Mischievous brows.
                p.setPen(QPen(ink, max(1.0, g * 0.05), Qt.SolidLine, Qt.RoundCap))
                for d in (-1.0, 1.0):
                    p.drawLine(QPointF(c.x() + d * (ex + g * 0.12), ey - g * 0.18), QPointF(c.x() + d * (ex - g * 0.1), ey - g * 0.12))
        # Mouth.
        my = c.y() + g * 0.16  # type: float
        if sev == self.Info and flee == 0.0:
            p.setPen(QPen(ink, max(1.0, g * 0.04)))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QPointF(c.x(), my), g * 0.04, g * 0.05)
        else:
            open_ = g * (0.06 + 0.06 * abs(sin(now * 14.0))) if sev == self.Error and not flee else g * (0.14 if sev == self.Critical or flee else 0.07)  # type: float
            mouth = QPainterPath()  # type: QPainterPath
            mouth.moveTo(c.x() - g * 0.24, my - g * 0.03)
            mouth.quadTo(c.x(), my + open_ * 2.2, c.x() + g * 0.24, my - g * 0.03)
            mouth.closeSubpath()
            p.setPen(QPen(ink, max(1.0, g * 0.03)))
            p.setBrush(QColor('#3B1020'))
            p.drawPath(mouth)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor('#FFFFFF'))
            for k in range(4):
                x = c.x() - g * 0.17 + k * g * 0.11  # type: float
                tooth = QPainterPath()  # type: QPainterPath
                tooth.moveTo(x - g * 0.04, my - g * 0.02)
                tooth.lineTo(x + g * 0.04, my - g * 0.02)
                tooth.lineTo(x, my + g * 0.06)
                tooth.closeSubpath()
                p.drawPath(tooth)
        # Warning: waving a wrench.
        if sev == self.Warning and not flee:
            p.save()
            p.translate(c.x() + g * 0.55, c.y() - g * 0.3)
            p.rotate(-30.0 + sin(now * 6.0) * 25.0)
            p.setPen(QPen(QColor('#8D99AE'), max(2.0, g * 0.07), Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(0, 0), QPointF(0, -g * 0.45))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor('#8D99AE'))
            jaw = QPainterPath()  # type: QPainterPath
            jaw.addEllipse(QPointF(0, -g * 0.5), g * 0.11, g * 0.11)
            cut = QPainterPath()  # type: QPainterPath
            cut.addRect(QRectF(-g * 0.04, -g * 0.65, g * 0.08, g * 0.12))
            p.drawPath(jaw.subtracted(cut))
            p.restore()

    # ---------- Properties ----------
    Q_ENUMS('Severity' if qVersion()[0] == '4' else Severity)
    severity = pyqtProperty(Severity, fget=getSeverity, fset=setSeverity)  # type: pyqtProperty
    title = pyqtProperty('QString', fget=getTitle, fset=setTitle)  # type: pyqtProperty
    message = pyqtProperty('QString', fget=getMessage, fset=setMessage)  # type: pyqtProperty
    retryText = pyqtProperty('QString', fget=getRetryText, fset=setRetryText)  # type: pyqtProperty
    closable = pyqtProperty(bool, fget=isClosable, fset=setClosable)  # type: pyqtProperty
    panelColor = pyqtProperty(QColor, fget=getPanelColor, fset=setPanelColor)  # type: pyqtProperty
    textColor = pyqtProperty(QColor, fget=getTextColor, fset=setTextColor)  # type: pyqtProperty
