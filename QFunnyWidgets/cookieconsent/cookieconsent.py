# -*- coding: utf-8 -*-
"""
CookieConsentWidget: a cookie-consent banner starring an actual cookie. It looks hopeful, gets
excited when you hover "Accept", starts to tear up when you hover "Decline", is happily eaten bite by
bite (with crumbs) when accepted and sobs dramatically when declined.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QFontMetricsF, QRadialGradient
from ManyQt.QtWidgets import QWidget
from math import sin, cos, pi, radians
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


CHIPS = [(-0.35, -0.45), (0.3, -0.5), (0.55, 0.05), (-0.55, 0.15), (0.1, 0.6), (-0.25, 0.55), (0.45, 0.45)]  # type: list
BITES = [(-25.0, 0.42, 0.25), (20.0, 0.38, 0.55), (-65.0, 0.34, 0.85)]  # type: list  # angle deg, radius ratio, time s


class Crumb(object):
    """
    A cookie crumb.
    """

    def __init__(self, x=0.0, y=0.0, vx=0.0, vy=0.0, size=2.0, life=1.0):
        """
        :param x: qreal | float | int
        :param y: qreal | float | int
        :param vx: qreal | float | int
        :param vy: qreal | float | int
        :param size: qreal | float | int
        :param life: (qreal | float | int) s
        """
        self.x = float(x)  # type: float
        self.y = float(y)  # type: float
        self.vx = float(vx)  # type: float
        self.vy = float(vy)  # type: float
        self.size = float(size)  # type: float
        self.life = float(life)  # type: float


class CookieConsentWidget(QWidget):
    """
    Emotionally manipulative cookie banner (for comedic purposes).
    """
    accepted = pyqtSignal()  # type: pyqtSignal
    declined = pyqtSignal()  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param title: str | unicode | QString
        :param message: str | unicode | QString
        :param acceptText: str | unicode | QString
        :param declineText: str | unicode | QString
        :param acceptedMessage: str | unicode | QString
        :param declinedMessage: str | unicode | QString
        :param accentColor: (QColor | Qt.GlobalColor | int | str | QString) Accept button color.
        :param panelColor: QColor | Qt.GlobalColor | int | str | QString
        :param textColor: QColor | Qt.GlobalColor | int | str | QString
        :param cookieColor: QColor | Qt.GlobalColor | int | str | QString
        :param autoReset: (int) ms after a choice before asking again (0 = never).
        :param accepted: callable | None
        :param declined: callable | None
        :param args: any
        :param kwargs: any
        """
        title = kwargs.pop('title', 'We use cookies')  # type: str
        message = kwargs.pop('message', "This cookie is hoping you'll accept it. No pressure. (Some pressure.)")  # type: str
        acceptText = kwargs.pop('acceptText', 'Accept')  # type: str
        declineText = kwargs.pop('declineText', 'Decline')  # type: str
        acceptedMessage = kwargs.pop('acceptedMessage', 'Nom. Excellent choice.')  # type: str
        declinedMessage = kwargs.pop('declinedMessage', 'Fine. The cookie will remember this.')  # type: str
        accentColor = kwargs.pop('accentColor', '#5E60CE')  # type: QColor
        panelColor = kwargs.pop('panelColor', '#FFFFFF')  # type: QColor
        textColor = kwargs.pop('textColor', '#23232B')  # type: QColor
        cookieColor = kwargs.pop('cookieColor', '#D9A066')  # type: QColor
        autoReset = kwargs.pop('autoReset', 0)  # type: int
        accepted = kwargs.pop('accepted', None)  # type: callable | None
        declined = kwargs.pop('declined', None)  # type: callable | None
        super(CookieConsentWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_title = title  # type: str
        self.__m_message = message  # type: str
        self.__m_acceptText = acceptText  # type: str
        self.__m_declineText = declineText  # type: str
        self.__m_acceptedMessage = acceptedMessage  # type: str
        self.__m_declinedMessage = declinedMessage  # type: str
        self.__m_accentColor = QColor(accentColor)  # type: QColor
        self.__m_panelColor = QColor(panelColor)  # type: QColor
        self.__m_textColor = QColor(textColor)  # type: QColor
        self.__m_cookieColor = QColor(cookieColor)  # type: QColor
        self.__m_autoReset = max(0, int(autoReset))  # type: int
        if callable(accepted):
            self.accepted.connect(accepted)
        if callable(declined):
            self.declined.connect(declined)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        # State.
        self.__m_choice = 0  # type: int  # 0 = asking, 1 = accepted, -1 = declined
        self.__m_choiceAt = -10.0  # type: float
        self.__m_hoverBtn = 0  # type: int  # 1 = accept, -1 = decline
        self.__m_acceptRect = QRectF()  # type: QRectF
        self.__m_declineRect = QRectF()  # type: QRectF
        self.__m_cookieCentre = QPointF()  # type: QPointF
        self.__m_cookieR = 10.0  # type: float
        self.__m_bitesDone = 0  # type: int
        self.__m_crumbs = []  # type: list[Crumb]
        self.__m_blinkAt = 2.0  # type: float
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

    def _choose(self, choice):
        """
        :param choice: (int) 1 = accept, -1 = decline
        :return: None
        """
        if self.__m_choice != 0:
            return
        self.__m_choice = int(choice)  # type: int
        self.__m_choiceAt = self._now()  # type: float
        self.__m_bitesDone = 0  # type: int
        self.__m_hoverBtn = 0  # type: int
        self.setCursor(Qt.ArrowCursor)
        if choice > 0:
            self.accepted.emit()
        else:
            self.declined.emit()
        self.update()

    # ---------- Public API ----------
    @pyqtSlot()
    def accept(self):
        """
        :return:
        """
        self._choose(1)

    @pyqtSlot()
    def decline(self):
        """
        :return:
        """
        self._choose(-1)

    @pyqtSlot()
    def reset(self):
        """
        Ask again with a fresh, whole cookie.
        :return:
        """
        self.__m_choice = 0  # type: int
        self.__m_bitesDone = 0  # type: int
        self.__m_crumbs = []  # type: list[Crumb]
        self.update()

    def getChoice(self):
        """
        :return: (int) 0 = undecided, 1 = accepted, -1 = declined
        """
        return self.__m_choice

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

    def getAcceptText(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_acceptText

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setAcceptText(self, acceptText):
        """
        :param acceptText: str | unicode | QString
        :return:
        """
        self.__m_acceptText = acceptText  # type: str
        self.update()

    def getDeclineText(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_declineText

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setDeclineText(self, declineText):
        """
        :param declineText: str | unicode | QString
        :return:
        """
        self.__m_declineText = declineText  # type: str
        self.update()

    def getAcceptedMessage(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_acceptedMessage

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setAcceptedMessage(self, acceptedMessage):
        """
        :param acceptedMessage: str | unicode | QString
        :return:
        """
        self.__m_acceptedMessage = acceptedMessage  # type: str
        self.update()

    def getDeclinedMessage(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_declinedMessage

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setDeclinedMessage(self, declinedMessage):
        """
        :param declinedMessage: str | unicode | QString
        :return:
        """
        self.__m_declinedMessage = declinedMessage  # type: str
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
        if self.__m_panelColor != color:
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
        if self.__m_textColor != color:
            self.__m_textColor = color  # type: QColor
            self.update()

    def getCookieColor(self):
        """
        :return: QColor
        """
        return self.__m_cookieColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setCookieColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        if self.__m_cookieColor != color:
            self.__m_cookieColor = color  # type: QColor
            self.update()

    def getAutoReset(self):
        """
        :return: int
        """
        return self.__m_autoReset

    @pyqtSlot(int)
    def setAutoReset(self, autoReset):
        """
        :param autoReset: (int) ms
        :return:
        """
        self.__m_autoReset = max(0, int(autoReset))  # type: int

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(520, 160)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(320, 120)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(CookieConsentWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(CookieConsentWidget, self).hideEvent(event)

    def mouseMoveEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        hover = 0  # type: int
        if self.__m_choice == 0:
            if self.__m_acceptRect.contains(eventPos(e)):
                hover = 1  # type: int
            elif self.__m_declineRect.contains(eventPos(e)):
                hover = -1  # type: int
        if hover != self.__m_hoverBtn:
            self.__m_hoverBtn = hover  # type: int
            self.setCursor(Qt.PointingHandCursor if hover else Qt.ArrowCursor)
        super(CookieConsentWidget, self).mouseMoveEvent(e)

    def leaveEvent(self, e):
        """
        :param e: QEvent
        :return:
        """
        self.__m_hoverBtn = 0  # type: int
        super(CookieConsentWidget, self).leaveEvent(e)

    def mouseReleaseEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if e.button() == Qt.LeftButton and self.__m_choice == 0:
            if self.__m_acceptRect.contains(eventPos(e)):
                self.accept()
            elif self.__m_declineRect.contains(eventPos(e)):
                self.decline()
        super(CookieConsentWidget, self).mouseReleaseEvent(e)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        since = now - self.__m_choiceAt  # type: float
        c = self.__m_cookieCentre  # type: QPointF
        R = self.__m_cookieR  # type: float
        if self.__m_choice == 1:
            while self.__m_bitesDone < len(BITES) and since >= BITES[self.__m_bitesDone][2]:
                ang, rr, t = BITES[self.__m_bitesDone]
                bx = c.x() + cos(radians(ang)) * R  # type: float
                by = c.y() + sin(radians(ang)) * R  # type: float
                for _ in range(14):
                    a = uniform(-pi, pi)  # type: float
                    sp = uniform(40, 140)  # type: float
                    self.__m_crumbs.append(Crumb(bx, by, cos(a) * sp + 40, sin(a) * sp - 80,
                                                 uniform(1.5, 3.5) * R / 40.0, uniform(0.6, 1.1)))
                self.__m_bitesDone += 1
        if self.__m_choice != 0 and self.__m_autoReset and since > self.__m_autoReset / 1000.0:
            self.reset()
        if now >= self.__m_blinkAt + 0.14:
            self.__m_blinkAt = now + uniform(2.0, 4.5)  # type: float
        alive = []  # type: list[Crumb]
        for cr in self.__m_crumbs:
            cr.vy += 500.0 * dt
            cr.x += cr.vx * dt
            cr.y += cr.vy * dt
            cr.life -= dt
            if cr.life > 0:
                alive.append(cr)
        self.__m_crumbs = alive  # type: list[Crumb]
        self.update()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        now = self._now()  # type: float
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        panel = QRectF(self.rect()).adjusted(3, 3, -3, -3)  # type: QRectF
        if self.__m_panelColor.alpha() > 0:
            p.setPen(QPen(QColor(0, 0, 0, 30), 1.0))
            p.setBrush(self.__m_panelColor)
            p.drawRoundedRect(panel, 16, 16)
        R = clamp(min(panel.height() * 0.33, panel.width() * 0.13), 14.0, 70.0)  # type: float
        c = QPointF(panel.left() + 22.0 + R, panel.center().y())  # type: QPointF
        self.__m_cookieCentre = c  # type: QPointF
        self.__m_cookieR = R  # type: float
        self._drawCookie(p, c, R, now)
        # Crumbs.
        p.setPen(Qt.NoPen)
        p.setBrush(self.__m_cookieColor.darker(115))
        for cr in self.__m_crumbs:
            p.drawEllipse(QPointF(cr.x, cr.y), cr.size, cr.size * 0.8)
        # Text block.
        x0 = c.x() + R + 24.0  # type: float
        tw = panel.right() - 20.0 - x0  # type: float
        if tw < 60:
            p.end()
            return
        tf = QFont(self.font())  # type: QFont
        tf.setBold(True)
        tf.setPointSizeF(12.5)
        mf = QFont(self.font())  # type: QFont
        mf.setPointSizeF(9.5)
        tfm = QFontMetricsF(tf)  # type: QFontMetricsF
        mfm = QFontMetricsF(mf)  # type: QFontMetricsF
        if self.__m_choice == 0:
            message = self.__m_message  # type: str
        else:
            message = self.__m_acceptedMessage if self.__m_choice > 0 else self.__m_declinedMessage  # type: str
        mr = mfm.boundingRect(QRectF(0, 0, tw, 1000), Qt.TextWordWrap, message)  # type: QRectF
        btnH = 34.0 if self.__m_choice == 0 else 0.0  # type: float
        blockH = tfm.height() + 6.0 + mr.height() + (14.0 + btnH if btnH else 0.0)  # type: float
        y = panel.center().y() - blockH / 2.0  # type: float
        p.setFont(tf)
        p.setPen(self.__m_textColor)
        p.drawText(QRectF(x0, y, tw, tfm.height()), Qt.AlignLeft | Qt.AlignVCenter, self.__m_title)
        y += tfm.height() + 6.0
        p.setFont(mf)
        sub = QColor(self.__m_textColor)  # type: QColor
        sub.setAlpha(190)
        p.setPen(sub)
        p.drawText(QRectF(x0, y, tw, mr.height()), Qt.TextWordWrap, message)
        y += mr.height() + 14.0
        if self.__m_choice == 0:
            self._drawButtons(p, x0, y, btnH, now)
        else:
            self.__m_acceptRect = QRectF()  # type: QRectF
            self.__m_declineRect = QRectF()  # type: QRectF
        p.end()

    def _drawButtons(self, p, x0, y, h, now):
        """
        :param p: QPainter
        :param x0: qreal | float | int
        :param y: qreal | float | int
        :param h: (qreal | float | int) button height
        :param now: qreal | float | int
        :return:
        """
        f = QFont(self.font())  # type: QFont
        f.setBold(True)
        f.setPointSizeF(9.5)
        fm = QFontMetricsF(f)  # type: QFontMetricsF
        aw = fm.horizontalAdvance(self.__m_acceptText) + 36.0 if hasattr(fm, 'horizontalAdvance') else fm.width(self.__m_acceptText) + 36.0  # type: float
        dw = fm.horizontalAdvance(self.__m_declineText) + 30.0 if hasattr(fm, 'horizontalAdvance') else fm.width(self.__m_declineText) + 30.0  # type: float
        self.__m_acceptRect = QRectF(x0, y, aw, h)  # type: QRectF
        # Decline button shrinks (a little) while you look at it. Dark pattern? Comedy pattern.
        shy = 0.92 if self.__m_hoverBtn == -1 else 1.0  # type: float
        self.__m_declineRect = QRectF(x0 + aw + 10.0, y + h * (1.0 - shy) / 2.0, dw * shy, h * shy)  # type: QRectF
        p.setFont(f)
        ac = self.__m_accentColor.lighter(112) if self.__m_hoverBtn == 1 else self.__m_accentColor  # type: QColor
        r = self.__m_acceptRect  # type: QRectF
        if self.__m_hoverBtn == 1:
            pulse = 1.0 + 0.04 * sin(now * 12.0)  # type: float
            cx = r.center()  # type: QPointF
            r = QRectF(cx.x() - r.width() * pulse / 2.0, cx.y() - r.height() * pulse / 2.0, r.width() * pulse, r.height() * pulse)
        p.setPen(Qt.NoPen)
        p.setBrush(ac)
        p.drawRoundedRect(r, h / 2.0, h / 2.0)
        p.setPen(QColor('#FFFFFF'))
        p.drawText(r, Qt.AlignCenter, self.__m_acceptText)
        d = self.__m_declineRect  # type: QRectF
        border = QColor(self.__m_textColor)  # type: QColor
        border.setAlpha(110 if self.__m_hoverBtn == -1 else 70)
        p.setPen(QPen(border, 1.3))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(d, d.height() / 2.0, d.height() / 2.0)
        tc = QColor(self.__m_textColor)  # type: QColor
        tc.setAlpha(200)
        p.setPen(tc)
        p.drawText(d, Qt.AlignCenter, self.__m_declineText)

    def _drawCookie(self, p, c, R, now):
        """
        :param p: QPainter
        :param c: (QPointF) center
        :param R: (qreal | float | int) radius
        :param now: qreal | float | int
        :return:
        """
        choice = self.__m_choice  # type: int
        since = now - self.__m_choiceAt  # type: float
        hover = self.__m_hoverBtn  # type: int
        p.save()
        bob = sin(now * (7.0 if hover == 1 else 2.0)) * R * (0.06 if hover == 1 else 0.03)  # type: float
        if choice == -1:
            bob = sin(now * 14.0) * R * 0.03  # sobbing
        p.translate(c.x(), c.y() + bob)
        cc = self.__m_cookieColor  # type: QColor
        # Cookie shape with bites taken out.
        shape = QPainterPath()  # type: QPainterPath
        shape.addEllipse(QPointF(0, 0), R, R)
        if choice == 1:
            for k in range(self.__m_bitesDone):
                ang, rr, t = BITES[k]
                bite = QPainterPath()  # type: QPainterPath
                bite.addEllipse(QPointF(cos(radians(ang)) * R * 1.05, sin(radians(ang)) * R * 1.05), R * rr, R * rr)
                shape = shape.subtracted(bite)  # type: QPainterPath
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 40))
        p.drawPath(shape.translated(0, R * 0.1))
        grad = QRadialGradient(QPointF(-R * 0.3, -R * 0.35), R * 1.6)  # type: QRadialGradient
        grad.setColorAt(0.0, cc.lighter(118))
        grad.setColorAt(0.8, cc)
        grad.setColorAt(1.0, cc.darker(125))
        p.setBrush(grad)
        p.setPen(QPen(cc.darker(145), max(1.2, R * 0.04)))
        p.drawPath(shape)
        # Chocolate chips (only where the cookie still exists).
        p.setPen(Qt.NoPen)
        p.setBrush(QColor('#5B3A1E'))
        for cx, cy in CHIPS:
            pt = QPointF(cx * R, cy * R)  # type: QPointF
            if shape.contains(pt) and not (abs(cx) < 0.5 and -0.3 < cy < 0.45):
                p.drawEllipse(pt, R * 0.09, R * 0.075)
        # Face.
        ink = QColor('#2E1E10')  # type: QColor
        ex = R * 0.25  # type: float
        ey = -R * 0.08  # type: float
        er = R * 0.14  # type: float
        pen = QPen(ink, max(1.2, R * 0.06), Qt.SolidLine, Qt.RoundCap)  # type: QPen
        blinking = self.__m_blinkAt <= now < self.__m_blinkAt + 0.14  # type: bool
        if choice == 1:
            # Blissful ^ ^ eyes and a blush.
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            for d in (-1.0, 1.0):
                p.drawArc(QRectF(d * ex - er, ey - er * 0.6, er * 2.0, er * 1.4), 20 * 16, 140 * 16)
            bl = QColor('#FF8FA3')  # type: QColor
            bl.setAlpha(150)
            p.setPen(Qt.NoPen)
            p.setBrush(bl)
            for d in (-1.0, 1.0):
                p.drawEllipse(QPointF(d * R * 0.45, R * 0.18), R * 0.12, R * 0.07)
            p.setPen(pen)
            p.setBrush(QColor('#7A2E1E'))
            mouth = QPainterPath()  # type: QPainterPath
            mouth.moveTo(-R * 0.18, R * 0.22)
            mouth.quadTo(0, R * 0.5, R * 0.18, R * 0.22)
            mouth.closeSubpath()
            p.drawPath(mouth)
        elif choice == -1:
            # Squeezed shut eyes, tear streams, wailing mouth.
            p.setPen(pen)
            for d in (-1.0, 1.0):
                p.drawLine(QPointF(d * ex - er, ey - er * 0.5), QPointF(d * ex + er * 0.2 * d, ey))
                p.drawLine(QPointF(d * ex + er * 0.2 * d, ey), QPointF(d * ex - er, ey + er * 0.4))
            tear = QColor('#5AB9FF')  # type: QColor
            tear.setAlpha(210)
            for d in (-1.0, 1.0):
                stream = QPainterPath()  # type: QPainterPath
                stream.moveTo(d * ex, ey + er * 0.5)
                for k in range(1, 7):
                    t = k / 6.0  # type: float
                    stream.lineTo(d * (ex + R * 0.08 * sin(now * 10.0 + k)), ey + er * 0.5 + t * R * 0.8)
                tp = QPen(tear, max(2.0, R * 0.1), Qt.SolidLine, Qt.RoundCap)  # type: QPen
                p.setPen(tp)
                p.setBrush(Qt.NoBrush)
                p.drawPath(stream)
            p.setPen(pen)
            p.setBrush(QColor('#7A2E1E'))
            o = 1.0 + 0.2 * sin(now * 16.0)  # type: float
            p.drawEllipse(QPointF(0, R * 0.36), R * 0.16, R * 0.12 * o)
        else:
            # Hopeful puppy eyes.
            for d in (-1.0, 1.0):
                if blinking:
                    p.setPen(pen)
                    p.setBrush(Qt.NoBrush)
                    p.drawArc(QRectF(d * ex - er, ey - er * 0.5, er * 2.0, er), 180 * 16, 180 * 16)
                    continue
                big = er * (1.15 if hover == 1 else 1.0)  # type: float
                p.setPen(Qt.NoPen)
                p.setBrush(ink)
                p.drawEllipse(QPointF(d * ex, ey), big, big * 1.1)
                p.setBrush(QColor('#FFFFFF'))
                p.drawEllipse(QPointF(d * ex - big * 0.3, ey - big * 0.35), big * 0.35, big * 0.35)
                p.drawEllipse(QPointF(d * ex + big * 0.3, ey + big * 0.35), big * 0.15, big * 0.15)
                if hover == -1:
                    # Welling tear.
                    grow = clamp((now * 1.0) % 1.5, 0.0, 1.0)  # type: float
                    tc = QColor('#5AB9FF')  # type: QColor
                    tc.setAlpha(200)
                    p.setBrush(tc)
                    p.drawEllipse(QPointF(d * ex + d * big * 0.4, ey + big * 1.1 + grow * R * 0.15), big * 0.3, big * 0.38)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            if hover == -1:
                # Quivering lip + worried brows.
                mouth = QPainterPath()  # type: QPainterPath
                mouth.moveTo(-R * 0.16, R * 0.33)
                for k in range(1, 7):
                    mouth.lineTo(-R * 0.16 + k * R * 0.32 / 6.0, R * 0.3 + (R * 0.025 if k % 2 else -R * 0.025) * sin(now * 40.0))
                p.drawPath(mouth)
                for d in (-1.0, 1.0):
                    p.drawLine(QPointF(d * (ex + er), ey - er * 1.5), QPointF(d * (ex - er * 0.8), ey - er * 2.1))
            elif hover == 1:
                p.setBrush(QColor('#7A2E1E'))
                mouth = QPainterPath()  # type: QPainterPath
                mouth.moveTo(-R * 0.2, R * 0.2)
                mouth.quadTo(0, R * 0.52, R * 0.2, R * 0.2)
                mouth.closeSubpath()
                p.drawPath(mouth)
            else:
                p.drawArc(QRectF(-R * 0.14, R * 0.12, R * 0.28, R * 0.2), 200 * 16, 140 * 16)
        p.restore()

    # ---------- Properties ----------
    title = pyqtProperty('QString', fget=getTitle, fset=setTitle)  # type: pyqtProperty
    message = pyqtProperty('QString', fget=getMessage, fset=setMessage)  # type: pyqtProperty
    acceptText = pyqtProperty('QString', fget=getAcceptText, fset=setAcceptText)  # type: pyqtProperty
    declineText = pyqtProperty('QString', fget=getDeclineText, fset=setDeclineText)  # type: pyqtProperty
    acceptedMessage = pyqtProperty('QString', fget=getAcceptedMessage, fset=setAcceptedMessage)  # type: pyqtProperty
    declinedMessage = pyqtProperty('QString', fget=getDeclinedMessage, fset=setDeclinedMessage)  # type: pyqtProperty
    accentColor = pyqtProperty(QColor, fget=getAccentColor, fset=setAccentColor)  # type: pyqtProperty
    panelColor = pyqtProperty(QColor, fget=getPanelColor, fset=setPanelColor)  # type: pyqtProperty
    textColor = pyqtProperty(QColor, fget=getTextColor, fset=setTextColor)  # type: pyqtProperty
    cookieColor = pyqtProperty(QColor, fget=getCookieColor, fset=setCookieColor)  # type: pyqtProperty
    autoReset = pyqtProperty(int, fget=getAutoReset, fset=setAutoReset)  # type: pyqtProperty
