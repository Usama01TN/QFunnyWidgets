# -*- coding: utf-8 -*-
"""
SleepyCatSectionWidget: a collapsible section (accordion panel) with a cat napping on its header.
Collapsed, the cat sleeps curled up like a loaf (it peeks with one eye if you hover). Expand the
section and it jolts awake, hops up, then sits watching the content with a swishing tail. Collapse
it and the cat yawns and curls back up. Put any widget inside with setContentWidget().
CatHeaderWidget is the painted header and can be used on its own.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, QObject, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont
from ManyQt.QtWidgets import QWidget, QVBoxLayout
from random import uniform
from math import sin, pi

SLEEPING, STARTLED, SITTING, YAWNING = range(4)  # type: tuple
STARTLE_TIME = 0.6  # type: float
YAWN_TIME = 1.0  # type: float
CAT_ROOM = 42.0  # type: float  # space above the bar for the cat
BAR_HEIGHT = 40.0  # type: float


def clamp(x, a, b):
    """
    :param x: qreal | float | int
    :param a: qreal | float | int
    :param b: qreal | float | int
    :return: qreal | float | int
    """
    return a if x < a else b if x > b else x


class CatHeaderWidget(QWidget):
    """
    Clickable section header with a resident cat.
    """
    clicked = pyqtSignal()  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param title: str | unicode | QString
        :param expanded: bool
        :param catColor: QColor | Qt.GlobalColor | int | str | QString
        :param barColor: QColor | Qt.GlobalColor | int | str | QString
        :param textColor: QColor | Qt.GlobalColor | int | str | QString
        :param clicked: callable | None
        :param args: any
        :param kwargs: any
        """
        title = kwargs.pop('title', 'Section')  # type: str
        expanded = kwargs.pop('expanded', False)  # type: bool
        catColor = kwargs.pop('catColor', '#F4A261')  # type: QColor
        barColor = kwargs.pop('barColor', '#ECEEF3')  # type: QColor
        textColor = kwargs.pop('textColor', '#23232B')  # type: QColor
        clicked = kwargs.pop('clicked', None)  # type: callable | None
        super(CatHeaderWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_title = title  # type: str
        self.__m_expanded = bool(expanded)  # type: bool
        self.__m_catColor = QColor(catColor)  # type: QColor
        self.__m_barColor = QColor(barColor)  # type: QColor
        self.__m_textColor = QColor(textColor)  # type: QColor
        if callable(clicked):
            self.clicked.connect(clicked)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFixedHeight(int(CAT_ROOM + BAR_HEIGHT))
        # State.
        self.__m_cat = SITTING if self.__m_expanded else SLEEPING  # type: int
        self.__m_catAt = -10.0  # type: float
        self.__m_chevron = 90.0 if self.__m_expanded else 0.0  # type: float
        self.__m_hovered = False  # type: bool
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

    # ---------- Public API ----------
    def isExpanded(self):
        """
        :return: bool
        """
        return self.__m_expanded

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setExpanded(self, expanded):
        """
        :param expanded: bool
        :return:
        """
        expanded = bool(expanded)  # type: bool
        if expanded != self.__m_expanded:
            self.__m_expanded = expanded  # type: bool
            self.__m_cat = STARTLED if expanded else YAWNING  # type: int
            self.__m_catAt = self._now()  # type: float
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

    def getCatColor(self):
        """
        :return: QColor
        """
        return self.__m_catColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setCatColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        self.__m_catColor = color  # type: QColor
        self.update()

    def getBarColor(self):
        """
        :return: QColor
        """
        return self.__m_barColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setBarColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        self.__m_barColor = color  # type: QColor
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
        return QSize(360, int(CAT_ROOM + BAR_HEIGHT))

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(CatHeaderWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(CatHeaderWidget, self).hideEvent(event)

    def enterEvent(self, e):
        """
        :param e: QEvent
        :return:
        """
        self.__m_hovered = True  # type: bool
        super(CatHeaderWidget, self).enterEvent(e)

    def leaveEvent(self, e):
        """
        :param e: QEvent
        :return:
        """
        self.__m_hovered = False  # type: bool
        super(CatHeaderWidget, self).leaveEvent(e)

    def mouseReleaseEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if e.button() == Qt.LeftButton and self.rect().contains(e.pos()):
            self.clicked.emit()
        super(CatHeaderWidget, self).mouseReleaseEvent(e)

    def keyPressEvent(self, e):
        """
        :param e: QKeyEvent
        :return:
        """
        if e.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
            self.clicked.emit()
            return
        super(CatHeaderWidget, self).keyPressEvent(e)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        since = now - self.__m_catAt  # type: float
        if self.__m_cat == STARTLED and since > STARTLE_TIME:
            self.__m_cat = SITTING  # type: int
        elif self.__m_cat == YAWNING and since > YAWN_TIME:
            self.__m_cat = SLEEPING  # type: int
        target = 90.0 if self.__m_expanded else 0.0  # type: float
        self.__m_chevron += (target - self.__m_chevron) * min(1.0, dt * 12.0)
        if now >= self.__m_blinkAt + 0.14:
            self.__m_blinkAt = now + uniform(2.0, 5.0)  # type: float
        self.update()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        now = self._now()  # type: float
        w = float(self.width())  # type: float
        bar = QRectF(1.0, CAT_ROOM, w - 2.0, self.height() - CAT_ROOM - 1.0)  # type: QRectF
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        bc = self.__m_barColor.lighter(108) if self.__m_hovered else self.__m_barColor  # type: QColor
        p.setPen(QPen(QColor(0, 0, 0, 30), 1.0))
        p.setBrush(bc)
        p.drawRoundedRect(bar, 12, 12)
        if self.hasFocus():
            fc = QColor(self.__m_textColor)  # type: QColor
            fc.setAlpha(60)
            p.setPen(QPen(fc, 1.0, Qt.DashLine))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(bar.adjusted(3, 3, -3, -3), 9, 9)
        # Chevron.
        cc = QPointF(bar.left() + 22.0, bar.center().y())  # type: QPointF
        p.save()
        p.translate(cc)
        p.rotate(self.__m_chevron)
        p.setPen(QPen(self.__m_textColor, 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.drawLine(QPointF(-3, -6), QPointF(3, 0))
        p.drawLine(QPointF(3, 0), QPointF(-3, 6))
        p.restore()
        # Title.
        f = QFont(self.font())  # type: QFont
        f.setBold(True)
        f.setPointSizeF(10.5)
        p.setFont(f)
        p.setPen(self.__m_textColor)
        p.drawText(QRectF(bar.left() + 42.0, bar.top(), bar.width() - 140.0, bar.height()),
                   Qt.AlignLeft | Qt.AlignVCenter, self.__m_title)
        # Cat on the right end of the bar.
        self._drawCat(p, QPointF(bar.right() - 52.0, bar.top() + 4.0), now)
        p.end()

    def _drawCat(self, p, base, now):
        """
        :param p: QPainter
        :param base: (QPointF) point on the bar the cat sits on
        :param now: qreal | float | int
        :return:
        """
        cat = self.__m_cat  # type: int
        since = now - self.__m_catAt  # type: float
        col = self.__m_catColor  # type: QColor
        ink = QColor('#3A2416')  # type: QColor
        outline = QPen(col.darker(150), 1.2)  # type: QPen
        pen = QPen(ink, 1.6, Qt.SolidLine, Qt.RoundCap)  # type: QPen
        p.save()
        p.translate(base)
        if cat == STARTLED:
            t = clamp(since / STARTLE_TIME, 0.0, 1.0)  # type: float
            p.translate(0, -sin(t * pi) * 8.0)
        lying = cat in (SLEEPING, YAWNING)  # type: bool
        if lying:
            # Loaf: wide body, head on the left, tail wrapped in front.
            breathe = 1.0 + 0.04 * sin(now * 2.2)  # type: float
            p.setPen(outline)
            p.setBrush(col)
            p.drawEllipse(QPointF(6.0, -9.0), 24.0, 11.0 * breathe)
            p.setBrush(col.darker(112))
            for k in range(3):
                p.drawRect(QRectF(4.0 + k * 7.0, -19.0 * breathe, 3.0, 6.0))
            p.setBrush(col)
            tail = QPainterPath()  # type: QPainterPath
            tail.moveTo(28.0, -4.0)
            tail.quadTo(20.0, 3.0, -4.0, 0.0)
            p.setPen(QPen(col.darker(120), 5.0, Qt.SolidLine, Qt.RoundCap))
            p.setBrush(Qt.NoBrush)
            p.drawPath(tail)
            hc = QPointF(-16.0, -11.0)  # type: QPointF
        else:
            # Sitting upright, tail swishing.
            swish = sin(now * 3.0) * 6.0  # type: float
            p.setPen(QPen(col.darker(120), 5.0, Qt.SolidLine, Qt.RoundCap))
            p.setBrush(Qt.NoBrush)
            tail = QPainterPath()  # type: QPainterPath
            tail.moveTo(10.0, -4.0)
            tail.cubicTo(26.0, -6.0, 24.0 + swish, -22.0, 18.0 + swish, -30.0)
            p.drawPath(tail)
            p.setPen(outline)
            p.setBrush(col)
            p.drawEllipse(QPointF(0.0, -12.0), 13.0, 13.0)
            p.setBrush(col.lighter(120))
            p.drawEllipse(QPointF(0.0, -9.0), 7.0, 8.0)
            hc = QPointF(0.0, -30.0)  # type: QPointF
        # Head + ears.
        p.setPen(outline)
        p.setBrush(col)
        twitch = sin(now * 30.0) * 1.5 if (self.__m_hovered and lying) else 0.0  # type: float
        for d in (-1.0, 1.0):
            ear = QPainterPath()  # type: QPainterPath
            ear.moveTo(hc.x() + d * 4.0, hc.y() - 7.0)
            ear.lineTo(hc.x() + d * 9.5, hc.y() - 15.0 + (twitch if d > 0 else 0.0))
            ear.lineTo(hc.x() + d * 10.0, hc.y() - 4.0)
            ear.closeSubpath()
            p.drawPath(ear)
        p.drawEllipse(hc, 11.0, 9.5)
        p.setPen(QPen(col.darker(125), 1.2))
        for dx in (-3.0, 0.0, 3.0):
            p.drawLine(QPointF(hc.x() + dx, hc.y() - 9.0), QPointF(hc.x() + dx, hc.y() - 5.5))
        # Face.
        ey = hc.y() - 1.0  # type: float
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        blinking = self.__m_blinkAt <= now < self.__m_blinkAt + 0.14  # type: bool
        if cat == SLEEPING:
            peek = self.__m_hovered and (now % 3.0) < 1.6  # type: bool
            for d in (-1.0, 1.0):
                if peek and d > 0:
                    p.setPen(Qt.NoPen)
                    p.setBrush(QColor('#9BDB4D'))
                    p.drawEllipse(QPointF(hc.x() + d * 4.5, ey), 2.2, 1.4)
                    p.setBrush(ink)
                    p.drawEllipse(QPointF(hc.x() + d * 4.5, ey), 0.7, 1.3)
                    p.setPen(pen)
                    p.setBrush(Qt.NoBrush)
                else:
                    p.drawArc(QRectF(hc.x() + d * 4.5 - 2.5, ey - 1.0, 5.0, 3.0), 180 * 16, 180 * 16)
        elif cat == YAWNING:
            for d in (-1.0, 1.0):
                p.drawLine(QPointF(hc.x() + d * 4.5 - 2.5, ey - 1.0), QPointF(hc.x() + d * 4.5 + 2.5, ey + 0.5))
        elif cat == STARTLED:
            for d in (-1.0, 1.0):
                p.setPen(QPen(ink, 1.0))
                p.setBrush(QColor('#FFFFFF'))
                p.drawEllipse(QPointF(hc.x() + d * 4.5, ey), 3.2, 3.6)
                p.setPen(Qt.NoPen)
                p.setBrush(ink)
                p.drawEllipse(QPointF(hc.x() + d * 4.5, ey), 1.0, 1.0)
        else:
            for d in (-1.0, 1.0):
                if blinking:
                    p.drawLine(QPointF(hc.x() + d * 4.5 - 2.2, ey), QPointF(hc.x() + d * 4.5 + 2.2, ey))
                    continue
                p.setPen(Qt.NoPen)
                p.setBrush(QColor('#9BDB4D'))
                p.drawEllipse(QPointF(hc.x() + d * 4.5, ey), 2.6, 2.8)
                p.setBrush(ink)
                p.drawEllipse(QPointF(hc.x() + d * 4.5, ey + 0.8), 0.9, 2.0)  # watching the content below
                p.setPen(pen)
        # Nose / mouth.
        p.setPen(Qt.NoPen)
        p.setBrush(QColor('#E58C8A'))
        p.drawEllipse(QPointF(hc.x(), hc.y() + 2.5), 1.4, 1.0)
        if cat == YAWNING or cat == STARTLED:
            open_ = sin(clamp(since / YAWN_TIME, 0.0, 1.0) * pi) * 3.5 if cat == YAWNING else 2.0  # type: float
            p.setBrush(QColor('#7A2E2E'))
            p.drawEllipse(QPointF(hc.x(), hc.y() + 5.5), 2.2, max(0.6, open_))
        else:
            p.setPen(QPen(ink, 1.0, Qt.SolidLine, Qt.RoundCap))
            p.setBrush(Qt.NoBrush)
            p.drawArc(QRectF(hc.x() - 3.0, hc.y() + 2.5, 3.0, 2.5), 180 * 16, 180 * 16)
            p.drawArc(QRectF(hc.x(), hc.y() + 2.5, 3.0, 2.5), 180 * 16, 180 * 16)
        # Whiskers.
        wc = QColor(ink)  # type: QColor
        wc.setAlpha(120)
        p.setPen(QPen(wc, 0.8))
        for d in (-1.0, 1.0):
            p.drawLine(QPointF(hc.x() + d * 6.0, hc.y() + 3.0), QPointF(hc.x() + d * 14.0, hc.y() + 1.5))
            p.drawLine(QPointF(hc.x() + d * 6.0, hc.y() + 4.0), QPointF(hc.x() + d * 14.0, hc.y() + 5.0))
        p.restore()
        # Sleeping z / startled !
        f = QFont(self.font())  # type: QFont
        f.setBold(True)
        if cat == SLEEPING:
            ph = (now * 0.5) % 1.0  # type: float
            f.setPointSizeF(6.5 + 3.0 * ph)
            p.setFont(f)
            zc = QColor(self.__m_textColor)  # type: QColor
            zc.setAlpha(int(200 * sin(ph * pi)))
            p.setPen(zc)
            p.drawText(QPointF(base.x() - 28.0 - ph * 6.0, base.y() - 16.0 - ph * 10.0), 'z')
        elif cat == STARTLED:
            f.setPointSizeF(11.0)
            p.setFont(f)
            p.setPen(QColor('#E63946'))
            p.drawText(QPointF(base.x() + 14.0, base.y() - 30.0 - sin(clamp(since / STARTLE_TIME, 0, 1) * pi) * 8.0), '!')

    # ---------- Properties ----------
    expanded = pyqtProperty(bool, fget=isExpanded, fset=setExpanded)  # type: pyqtProperty
    title = pyqtProperty('QString', fget=getTitle, fset=setTitle)  # type: pyqtProperty
    catColor = pyqtProperty(QColor, fget=getCatColor, fset=setCatColor)  # type: pyqtProperty
    barColor = pyqtProperty(QColor, fget=getBarColor, fset=setBarColor)  # type: pyqtProperty
    textColor = pyqtProperty(QColor, fget=getTextColor, fset=setTextColor)  # type: pyqtProperty


class SleepyCatSectionWidget(QWidget):
    """
    Collapsible section: CatHeaderWidget + an animated content area.
    """
    toggled = pyqtSignal(bool)  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param title: str | unicode | QString
        :param expanded: bool
        :param content: (QWidget | None) Widget shown inside the section.
        :param catColor: QColor | Qt.GlobalColor | int | str | QString
        :param barColor: QColor | Qt.GlobalColor | int | str | QString
        :param textColor: QColor | Qt.GlobalColor | int | str | QString
        :param toggled: callable | None
        :param args: any
        :param kwargs: any
        """
        title = kwargs.pop('title', 'Advanced settings')  # type: str
        expanded = kwargs.pop('expanded', False)  # type: bool
        content = kwargs.pop('content', None)  # type: QWidget | None
        catColor = kwargs.pop('catColor', '#F4A261')  # type: QColor
        barColor = kwargs.pop('barColor', '#ECEEF3')  # type: QColor
        textColor = kwargs.pop('textColor', '#23232B')  # type: QColor
        toggled = kwargs.pop('toggled', None)  # type: callable | None
        super(SleepyCatSectionWidget, self).__init__(*args, **kwargs)
        if callable(toggled):
            self.toggled.connect(toggled)
        # Children.
        self.__m_header = CatHeaderWidget(title=title, expanded=expanded, catColor=catColor, barColor=barColor,
                                          textColor=textColor, clicked=self.toggle)  # type: CatHeaderWidget
        self.__m_body = QWidget()  # type: QWidget
        self.__m_bodyLayout = QVBoxLayout(self.__m_body)  # type: QVBoxLayout
        self.__m_bodyLayout.setContentsMargins(12, 8, 12, 8)
        self.__m_content = None  # type: QWidget | None
        layout = QVBoxLayout(self)  # type: QVBoxLayout
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.__m_header)
        layout.addWidget(self.__m_body)
        # Height animation.
        self.__m_expanded = bool(expanded)  # type: bool
        self.__m_height = 0.0  # type: float
        self.__m_timer = QTimer(self)  # type: QTimer
        self.__m_timer.timeout.connect(self._tick)
        if content is not None:
            self.setContentWidget(content)
        self._snap()

    # ---------- Helpers ----------
    def _targetHeight(self):
        """
        :return: qreal | float | int
        """
        return float(self.__m_body.sizeHint().height()) if self.__m_expanded else 0.0

    def _snap(self):
        """
        Jump straight to the final height (no animation).
        :return:
        """
        self.__m_height = self._targetHeight()  # type: float
        self.__m_body.setMaximumHeight(int(self.__m_height) if not self.__m_expanded else 16777215)
        self.__m_body.setVisible(self.__m_expanded)
        # Lifting the height cap does not by itself make the parent re-layout, so ask explicitly.
        self.__m_body.updateGeometry()
        self.updateGeometry()

    @pyqtSlot()
    def _tick(self):
        """
        :return:
        """
        target = self._targetHeight()  # type: float
        self.__m_height += (target - self.__m_height) * 0.22
        if abs(target - self.__m_height) < 1.0:
            self.__m_timer.stop()
            self._snap()
            return
        self.__m_body.setVisible(True)
        self.__m_body.setMaximumHeight(int(self.__m_height))

    # ---------- Public API ----------
    @pyqtSlot()
    def toggle(self):
        """
        :return:
        """
        self.setExpanded(not self.__m_expanded)

    def isExpanded(self):
        """
        :return: bool
        """
        return self.__m_expanded

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setExpanded(self, expanded):
        """
        :param expanded: bool
        :return:
        """
        expanded = bool(expanded)  # type: bool
        if expanded == self.__m_expanded:
            return
        self.__m_height = float(self.__m_body.height()) if self.__m_body.isVisible() else 0.0  # type: float
        self.__m_expanded = expanded  # type: bool
        self.__m_header.setExpanded(expanded)
        self.__m_body.setMaximumHeight(int(self.__m_height))
        self.__m_timer.start(16)
        self.toggled.emit(expanded)

    def getContentWidget(self):
        """
        :return: QWidget | None
        """
        return self.__m_content

    @pyqtSlot(QWidget)
    def setContentWidget(self, content):
        """
        :param content: QWidget
        :return:
        """
        if self.__m_content is not None:
            self.__m_bodyLayout.removeWidget(self.__m_content)
            self.__m_content.setParent(None)
        self.__m_content = content  # type: QWidget | None
        if content is not None:
            self.__m_bodyLayout.addWidget(content)
        self._snap()

    def getHeader(self):
        """
        :return: CatHeaderWidget
        """
        return self.__m_header

    def getTitle(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_header.getTitle()

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setTitle(self, title):
        """
        :param title: str | unicode | QString
        :return:
        """
        self.__m_header.setTitle(title)

    # ---------- Properties ----------
    expanded = pyqtProperty(bool, fget=isExpanded, fset=setExpanded, notify=toggled)  # type: pyqtProperty
    title = pyqtProperty('QString', fget=getTitle, fset=setTitle)  # type: pyqtProperty
    # QObject (not QWidget) is the property type every binding can register.
    contentWidget = pyqtProperty(QObject, fget=getContentWidget, fset=setContentWidget)  # type: pyqtProperty
