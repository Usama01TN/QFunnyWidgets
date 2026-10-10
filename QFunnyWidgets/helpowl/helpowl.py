# -*- coding: utf-8 -*-
"""
HelpOwlWidget: an inline "?" help icon that is a sleeping owl (the question mark is on its belly).
Hover it and the owl wakes up, swivels its head all the way round, and a help bubble appears next
to it. Leave and it dozes off again; click it to pin the bubble open.
HelpBubble is the floating tooltip window and can be used on its own.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, QPoint, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QFontMetricsF
from ManyQt.QtWidgets import QWidget, QApplication
from math import sin, pi

SLEEP, WAKING, AWAKE, DOZING = range(4)  # type: tuple
WAKE_TIME = 0.6  # type: float
DOZE_TIME = 0.5  # type: float


def clamp(x, a, b):
    """
    :param x: qreal | float | int
    :param a: qreal | float | int
    :param b: qreal | float | int
    :return: qreal | float | int
    """
    return a if x < a else b if x > b else x


def easeOut(t):
    """
    :param t: (qreal | float | int) 0..1
    :return: qreal | float | int
    """
    t = clamp(t, 0.0, 1.0)  # type: float
    return 1.0 - (1.0 - t) ** 3


class HelpBubble(QWidget):
    """
    Frameless floating help bubble with a tail pointing down-left.
    """

    def __init__(self, *args, **kwargs):
        """
        :param title: str | unicode | QString
        :param text: str | unicode | QString
        :param accentColor: QColor | Qt.GlobalColor | int | str | QString
        :param args: any
        :param kwargs: any
        """
        title = kwargs.pop('title', '')  # type: str
        text = kwargs.pop('text', '')  # type: str
        accentColor = kwargs.pop('accentColor', '#8D6E63')  # type: QColor
        super(HelpBubble, self).__init__(*args, **kwargs)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        # Options.
        self.__m_title = title  # type: str
        self.__m_text = text  # type: str
        self.__m_accentColor = QColor(accentColor)  # type: QColor
        self.__m_opacity = 0.0  # type: float
        self.__m_tailRight = False  # type: bool
        self._resizeToText()

    # ---------- Helpers ----------
    def _fonts(self):
        """
        :return: (tuple) title QFont, text QFont
        """
        tf = QFont(self.font())  # type: QFont
        tf.setBold(True)
        tf.setPointSizeF(9.5)
        bf = QFont(self.font())  # type: QFont
        bf.setPointSizeF(9.0)
        return tf, bf

    def _resizeToText(self):
        """
        :return:
        """
        tf, bf = self._fonts()
        maxW = 240.0  # type: float
        tr = QFontMetricsF(tf).boundingRect(QRectF(0, 0, maxW, 400), Qt.TextWordWrap, self.__m_title) if self.__m_title else QRectF()
        br = QFontMetricsF(bf).boundingRect(QRectF(0, 0, maxW, 1000), Qt.TextWordWrap, self.__m_text)  # type: QRectF
        w = max(tr.width(), br.width()) + 28.0  # type: float
        h = tr.height() + (4.0 if self.__m_title else 0.0) + br.height() + 22.0 + 10.0  # type: float  # +10 tail
        self.resize(int(w) + 2, int(h) + 2)

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
        self._resizeToText()
        self.update()

    def getText(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_text

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setText(self, text):
        """
        :param text: str | unicode | QString
        :return:
        """
        self.__m_text = text  # type: str
        self._resizeToText()
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
        self.__m_accentColor = color  # type: QColor
        self.update()

    def isTailRight(self):
        """
        :return: (bool) True when the tail points down-right (bubble shown left of its anchor).
        """
        return self.__m_tailRight

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setTailRight(self, tailRight):
        """
        :param tailRight: bool
        :return:
        """
        self.__m_tailRight = bool(tailRight)  # type: bool
        self.update()

    def getOpacity(self):
        """
        :return: qreal | float | int
        """
        return self.__m_opacity

    @pyqtSlot('qreal')
    @pyqtSlot(float)
    @pyqtSlot(int)
    def setOpacity(self, opacity):
        """
        :param opacity: (qreal | float | int) 0..1
        :return:
        """
        self.__m_opacity = float(clamp(float(opacity), 0.0, 1.0))  # type: float
        self.update()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        p.setOpacity(self.__m_opacity)
        rect = QRectF(1, 1, self.width() - 2, self.height() - 12)  # type: QRectF
        path = QPainterPath()  # type: QPainterPath
        path.addRoundedRect(rect, 10, 10)
        tail = QPainterPath()  # type: QPainterPath
        if self.__m_tailRight:
            tail.moveTo(rect.right() - 10, rect.bottom() - 2)
            tail.lineTo(rect.right() - 2, self.height() - 1.0)
            tail.lineTo(rect.right() - 24, rect.bottom() - 2)
        else:
            tail.moveTo(rect.left() + 10, rect.bottom() - 2)
            tail.lineTo(rect.left() + 2, self.height() - 1.0)
            tail.lineTo(rect.left() + 24, rect.bottom() - 2)
        tail.closeSubpath()
        path = path.united(tail)  # type: QPainterPath
        p.setPen(QPen(QColor(0, 0, 0, 50), 1.0))
        p.setBrush(QColor('#FFFDF7'))
        p.drawPath(path)
        p.fillRect(QRectF(rect.left() + 1, rect.top() + 10, 4, rect.height() - 20), self.__m_accentColor)
        tf, bf = self._fonts()
        y = rect.top() + 10.0  # type: float
        if self.__m_title:
            p.setFont(tf)
            p.setPen(QColor('#23232B'))
            th = QFontMetricsF(tf).boundingRect(QRectF(0, 0, rect.width() - 26, 400), Qt.TextWordWrap, self.__m_title).height()  # type: float
            p.drawText(QRectF(rect.left() + 14, y, rect.width() - 26, th), Qt.TextWordWrap, self.__m_title)
            y += th + 4.0
        p.setFont(bf)
        p.setPen(QColor('#4A4A55'))
        p.drawText(QRectF(rect.left() + 14, y, rect.width() - 26, rect.bottom() - y - 6), Qt.TextWordWrap, self.__m_text)
        p.end()

    # ---------- Properties ----------
    title = pyqtProperty('QString', fget=getTitle, fset=setTitle)  # type: pyqtProperty
    text = pyqtProperty('QString', fget=getText, fset=setText)  # type: pyqtProperty
    accentColor = pyqtProperty(QColor, fget=getAccentColor, fset=setAccentColor)  # type: pyqtProperty
    opacity = pyqtProperty('qreal', fget=getOpacity, fset=setOpacity)  # type: pyqtProperty
    tailRight = pyqtProperty(bool, fget=isTailRight, fset=setTailRight)  # type: pyqtProperty


class HelpOwlWidget(QWidget):
    """
    Help icon owl with a pop-up explanation.
    """
    shown = pyqtSignal()  # type: pyqtSignal
    hidden = pyqtSignal()  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param helpText: (str | unicode | QString) The explanation shown in the bubble.
        :param title: (str | unicode | QString) Optional bubble title.
        :param owlColor: QColor | Qt.GlobalColor | int | str | QString
        :param shown: callable | None
        :param hidden: callable | None
        :param args: any
        :param kwargs: any
        """
        helpText = kwargs.pop('helpText', 'Hoo! This is where the helpful explanation goes.')  # type: str
        title = kwargs.pop('title', '')  # type: str
        owlColor = kwargs.pop('owlColor', '#8D6E63')  # type: QColor
        shown = kwargs.pop('shown', None)  # type: callable | None
        hidden = kwargs.pop('hidden', None)  # type: callable | None
        super(HelpOwlWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_owlColor = QColor(owlColor)  # type: QColor
        if callable(shown):
            self.shown.connect(shown)
        if callable(hidden):
            self.hidden.connect(hidden)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setCursor(Qt.WhatsThisCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        # Bubble window.
        # Parented to the owl so Qt destroys them together; the ToolTip flag keeps it a floating window.
        self.__m_bubble = HelpBubble(self, title=title, text=helpText, accentColor=owlColor)  # type: HelpBubble
        # State.
        self.__m_state = SLEEP  # type: int
        self.__m_stateAt = -10.0  # type: float
        self.__m_hovered = False  # type: bool
        self.__m_pinned = False  # type: bool
        self.__m_visible = False  # type: bool
        self.__m_alpha = 0.0  # type: float
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

    def _setState(self, state):
        """
        :param state: int
        :return:
        """
        if state != self.__m_state:
            self.__m_state = state  # type: int
            self.__m_stateAt = self._now()  # type: float

    def _wantOpen(self):
        """
        :return: bool
        """
        return self.__m_hovered or self.__m_pinned

    def _placeBubble(self):
        """
        Put the bubble just above-right of the owl, inside the screen.
        :return:
        """
        b = self.__m_bubble  # type: HelpBubble
        g = self.mapToGlobal(QPoint(int(self.width() * 0.75), 0))  # type: QPoint
        win = self.window()  # type: QWidget
        winRight = win.mapToGlobal(QPoint(win.width(), 0)).x()  # type: int
        # Flip to the owl's left when the bubble would stick out of the window.
        flip = g.x() + b.width() > winRight  # type: bool
        b.setTailRight(flip)
        x = (self.mapToGlobal(QPoint(int(self.width() * 0.25), 0)).x() - b.width()) if flip else g.x()  # type: int
        y = g.y() - b.height() + 6  # type: int
        # Qt 5.14+/6: QWidget.screen(); older Qt: QDesktopWidget.
        if hasattr(self, 'screen') and self.screen() is not None:
            screen = self.screen().availableGeometry()  # type: QRect
        elif hasattr(QApplication, 'desktop') and QApplication.desktop() is not None:
            screen = QApplication.desktop().availableGeometry(self)  # type: QRect
        else:
            screen = None
        if screen is not None:
            x = int(clamp(x, screen.left(), screen.right() - b.width()))
            y = int(clamp(y, screen.top(), screen.bottom() - b.height()))
        b.move(x, y)

    # ---------- Public API ----------
    @pyqtSlot()
    def showHelp(self):
        """
        Wake up and pin the bubble open.
        :return:
        """
        self.__m_pinned = True  # type: bool
        self.update()

    @pyqtSlot()
    def hideHelp(self):
        """
        :return:
        """
        self.__m_pinned = False  # type: bool
        self.__m_hovered = False  # type: bool

    def isHelpVisible(self):
        """
        :return: bool
        """
        return self.__m_visible

    def getBubble(self):
        """
        :return: HelpBubble
        """
        return self.__m_bubble

    def getHelpText(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_bubble.getText()

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setHelpText(self, helpText):
        """
        :param helpText: str | unicode | QString
        :return:
        """
        self.__m_bubble.setText(helpText)

    def getTitle(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_bubble.getTitle()

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setTitle(self, title):
        """
        :param title: str | unicode | QString
        :return:
        """
        self.__m_bubble.setTitle(title)

    def getOwlColor(self):
        """
        :return: QColor
        """
        return self.__m_owlColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setOwlColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        self.__m_owlColor = color  # type: QColor
        self.__m_bubble.setAccentColor(color)
        self.update()

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(34, 40)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(22, 26)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(HelpOwlWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        try:
            self.__m_bubble.hide()
        except RuntimeError:  # bubble already destroyed during application shutdown
            pass
        super(HelpOwlWidget, self).hideEvent(event)

    def enterEvent(self, e):
        """
        :param e: QEvent
        :return:
        """
        self.__m_hovered = True  # type: bool
        super(HelpOwlWidget, self).enterEvent(e)

    def leaveEvent(self, e):
        """
        :param e: QEvent
        :return:
        """
        self.__m_hovered = False  # type: bool
        super(HelpOwlWidget, self).leaveEvent(e)

    def mouseReleaseEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if e.button() == Qt.LeftButton:
            self.__m_pinned = not self.__m_pinned  # type: bool
        super(HelpOwlWidget, self).mouseReleaseEvent(e)

    def keyPressEvent(self, e):
        """
        :param e: QKeyEvent
        :return:
        """
        if e.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter, Qt.Key_F1):
            self.__m_pinned = not self.__m_pinned  # type: bool
            return
        if e.key() == Qt.Key_Escape:
            self.hideHelp()
            return
        super(HelpOwlWidget, self).keyPressEvent(e)

    def focusOutEvent(self, e):
        """
        :param e: QFocusEvent
        :return:
        """
        self.__m_pinned = False  # type: bool
        super(HelpOwlWidget, self).focusOutEvent(e)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        since = now - self.__m_stateAt  # type: float
        want = self._wantOpen()  # type: bool
        st = self.__m_state  # type: int
        if want and st in (SLEEP, DOZING):
            self._setState(WAKING)
        elif st == WAKING and since >= WAKE_TIME:
            self._setState(AWAKE)
        elif not want and st in (AWAKE, WAKING):
            self._setState(DOZING)
        elif st == DOZING and since >= DOZE_TIME:
            self._setState(SLEEP)
        # Bubble fades in once the head has finished turning.
        target = 1.0 if (want and self.__m_state == AWAKE) else 0.0  # type: float
        self.__m_alpha += (target - self.__m_alpha) * min(1.0, dt * 12.0)
        b = self.__m_bubble  # type: HelpBubble
        if self.__m_alpha > 0.02:
            if not b.isVisible():
                self._placeBubble()
                b.show()
            b.setOpacity(self.__m_alpha)
            if not self.__m_visible:
                self.__m_visible = True  # type: bool
                self.shown.emit()
        elif b.isVisible():
            b.hide()
            if self.__m_visible:
                self.__m_visible = False  # type: bool
                self.hidden.emit()
        self.update()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        now = self._now()  # type: float
        w = float(self.width())  # type: float
        h = float(self.height())  # type: float
        s = min(w / 0.85, h)  # type: float
        c = QPointF(w / 2.0, h / 2.0)  # type: QPointF
        st = self.__m_state  # type: int
        since = now - self.__m_stateAt  # type: float
        oc = self.__m_owlColor  # type: QColor
        ink = QColor('#2B1D14')  # type: QColor
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        breathe = 1.0 + (0.03 * sin(now * 2.0) if st == SLEEP else 0.0)  # type: float
        # Feet.
        p.setPen(QPen(QColor('#E09F3E'), max(1.2, s * 0.05), Qt.SolidLine, Qt.RoundCap))
        for d in (-1.0, 1.0):
            p.drawLine(QPointF(c.x() + d * s * 0.1, c.y() + s * 0.4), QPointF(c.x() + d * s * 0.14, c.y() + s * 0.47))
        # Body.
        p.setPen(QPen(oc.darker(140), max(1.0, s * 0.03)))
        p.setBrush(oc)
        p.drawEllipse(QPointF(c.x(), c.y() + s * 0.12), s * 0.33 * breathe, s * 0.33)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor('#EAD7C3'))
        p.drawEllipse(QPointF(c.x(), c.y() + s * 0.18), s * 0.2, s * 0.23)
        # The "?" on the belly.
        f = QFont(self.font())  # type: QFont
        f.setBold(True)
        f.setPixelSize(max(7, int(s * 0.3)))
        p.setFont(f)
        p.setPen(oc.darker(130))
        p.drawText(QRectF(c.x() - s * 0.2, c.y() - s * 0.03, s * 0.4, s * 0.42), Qt.AlignCenter, '?')
        # Wings.
        p.setPen(QPen(oc.darker(140), max(1.0, s * 0.03)))
        p.setBrush(oc.darker(112))
        flap = sin(since * 30.0) * s * 0.03 if st == WAKING else 0.0  # type: float
        for d in (-1.0, 1.0):
            p.drawEllipse(QPointF(c.x() + d * s * 0.3, c.y() + s * 0.15 - flap), s * 0.09, s * 0.2)
        # Head (swivels when waking).
        hc = QPointF(c.x(), c.y() - s * 0.2)  # type: QPointF
        p.save()
        p.translate(hc)
        if st == WAKING:
            p.rotate(300.0 * (1.0 - easeOut(since / WAKE_TIME)))
        elif st == SLEEP:
            p.rotate(-10.0)
        p.setPen(QPen(oc.darker(140), max(1.0, s * 0.03)))
        p.setBrush(oc)
        for d in (-1.0, 1.0):
            tuft = QPainterPath()  # type: QPainterPath
            tuft.moveTo(d * s * 0.12, -s * 0.18)
            tuft.lineTo(d * s * 0.26, -s * 0.32)
            tuft.lineTo(d * s * 0.27, -s * 0.12)
            tuft.closeSubpath()
            p.drawPath(tuft)
        p.drawEllipse(QPointF(0, 0), s * 0.3, s * 0.24)
        # Face disc + eyes.
        er = s * 0.1  # type: float
        for d in (-1.0, 1.0):
            ec = QPointF(d * s * 0.13, -s * 0.01)  # type: QPointF
            p.setPen(Qt.NoPen)
            p.setBrush(QColor('#EAD7C3'))
            p.drawEllipse(ec, er * 1.25, er * 1.25)
            if st in (SLEEP, DOZING):
                p.setPen(QPen(ink, max(1.0, s * 0.035), Qt.SolidLine, Qt.RoundCap))
                p.setBrush(Qt.NoBrush)
                p.drawArc(QRectF(ec.x() - er * 0.8, ec.y() - er * 0.4, er * 1.6, er * 1.0), 180 * 16, 180 * 16)
            else:
                p.setBrush(QColor('#FFD23F'))
                p.drawEllipse(ec, er, er)
                p.setBrush(ink)
                p.drawEllipse(QPointF(ec.x() + er * 0.25, ec.y() - er * 0.2), er * 0.5, er * 0.5)
                p.setBrush(QColor('#FFFFFF'))
                p.drawEllipse(QPointF(ec.x() + er * 0.1, ec.y() - er * 0.4), er * 0.18, er * 0.18)
        # Beak.
        p.setPen(Qt.NoPen)
        p.setBrush(QColor('#E09F3E'))
        beak = QPainterPath()  # type: QPainterPath
        beak.moveTo(-s * 0.04, s * 0.06)
        beak.lineTo(s * 0.04, s * 0.06)
        beak.lineTo(0, s * 0.14)
        beak.closeSubpath()
        p.drawPath(beak)
        p.restore()
        # Sleepy z (kept inside the icon).
        if st == SLEEP:
            ph = (now * 0.5) % 1.0  # type: float
            zf = QFont(self.font())  # type: QFont
            zf.setBold(True)
            zf.setPixelSize(max(6, int(s * (0.14 + 0.08 * ph))))
            p.setFont(zf)
            zc = QColor(self.palette().text().color())  # type: QColor
            zc.setAlpha(int(200 * sin(ph * pi)))
            p.setPen(zc)
            p.drawText(QPointF(min(w - s * 0.2, c.x() + s * 0.28 + ph * s * 0.08), max(s * 0.2, c.y() - s * 0.38 - ph * s * 0.1)), 'z')
        if self.hasFocus():
            fc = QColor(self.palette().text().color())  # type: QColor
            fc.setAlpha(60)
            p.setPen(QPen(fc, 1.0, Qt.DashLine))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(QRectF(self.rect()).adjusted(1, 1, -1, -1), 6, 6)
        p.end()

    # ---------- Properties ----------
    helpText = pyqtProperty('QString', fget=getHelpText, fset=setHelpText)  # type: pyqtProperty
    title = pyqtProperty('QString', fget=getTitle, fset=setTitle)  # type: pyqtProperty
    owlColor = pyqtProperty(QColor, fget=getOwlColor, fset=setOwlColor)  # type: pyqtProperty
