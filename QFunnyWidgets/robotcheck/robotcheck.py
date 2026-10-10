# -*- coding: utf-8 -*-
"""
RobotCheckWidget: an "I'm not a robot" verification box with a robot hiding behind it. Its antenna
blinks over the edge while idle; when you click, the spinner turns and the robot pops up, sweating
oil, eyes darting. Then it winks, gives a thumbs-up ("Definitely human. Totally.") and ducks back
down. With failChance > 0 you may be found "suspiciously robotic".
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QFontMetricsF
from ManyQt.QtWidgets import QWidget
from random import random
from math import sin

IDLE, CHECKING, VERIFIED, FAILED = range(4)  # type: tuple


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


class RobotCheckWidget(QWidget):
    """
    Human verification box, administered by a robot.
    """
    CHECK_TIME = 1.8  # type: float
    verified = pyqtSignal()  # type: pyqtSignal
    failed = pyqtSignal()  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param text: (str | unicode | QString) Checkbox label.
        :param verifiedText: str | unicode | QString
        :param failChance: (qreal | float | int) 0..1 probability of being declared a robot.
        :param panelColor: QColor | Qt.GlobalColor | int | str | QString
        :param textColor: QColor | Qt.GlobalColor | int | str | QString
        :param robotColor: QColor | Qt.GlobalColor | int | str | QString
        :param verified: callable | None
        :param failed: callable | None
        :param args: any
        :param kwargs: any
        """
        text = kwargs.pop('text', "I'm not a robot")  # type: str
        verifiedText = kwargs.pop('verifiedText', 'Verified human (probably)')  # type: str
        failChance = kwargs.pop('failChance', 0.0)  # type: float
        panelColor = kwargs.pop('panelColor', '#F9F9FB')  # type: QColor
        textColor = kwargs.pop('textColor', '#23232B')  # type: QColor
        robotColor = kwargs.pop('robotColor', '#AAB4C3')  # type: QColor
        verified = kwargs.pop('verified', None)  # type: callable | None
        failed = kwargs.pop('failed', None)  # type: callable | None
        super(RobotCheckWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_text = text  # type: str
        self.__m_verifiedText = verifiedText  # type: str
        self.__m_failChance = float(clamp(float(failChance), 0.0, 1.0))  # type: float
        self.__m_panelColor = QColor(panelColor)  # type: QColor
        self.__m_textColor = QColor(textColor)  # type: QColor
        self.__m_robotColor = QColor(robotColor)  # type: QColor
        if callable(verified):
            self.verified.connect(verified)
        if callable(failed):
            self.failed.connect(failed)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.StrongFocus)
        # State.
        self.__m_mode = IDLE  # type: int
        self.__m_modeAt = 0.0  # type: float
        self.__m_rise = 0.0  # type: float
        self.__m_riseVel = 0.0  # type: float
        self.__m_boxRect = QRectF()  # type: QRectF
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

    def _setMode(self, mode):
        """
        :param mode: int
        :return:
        """
        self.__m_mode = mode  # type: int
        self.__m_modeAt = self._now()  # type: float
        self.update()

    def _panel(self):
        """
        :return: QRectF
        """
        w = float(self.width())  # type: float
        h = float(self.height())  # type: float
        pw = min(w - 16.0, 330.0)  # type: float
        ph = min(78.0, h * 0.5)  # type: float
        return QRectF((w - pw) / 2.0, h - ph - 8.0, pw, ph)

    # ---------- Public API ----------
    @pyqtSlot()
    def verify(self):
        """
        Start the (very rigorous) verification.
        :return:
        """
        if self.__m_mode in (IDLE, FAILED):
            self._setMode(CHECKING)

    @pyqtSlot()
    def reset(self):
        """
        :return:
        """
        self._setMode(IDLE)

    def isVerified(self):
        """
        :return: bool
        """
        return self.__m_mode == VERIFIED

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
        self.update()

    def getVerifiedText(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_verifiedText

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setVerifiedText(self, verifiedText):
        """
        :param verifiedText: str | unicode | QString
        :return:
        """
        self.__m_verifiedText = verifiedText  # type: str
        self.update()

    def getFailChance(self):
        """
        :return: qreal | float | int
        """
        return self.__m_failChance

    @pyqtSlot('qreal')
    @pyqtSlot(float)
    @pyqtSlot(int)
    def setFailChance(self, failChance):
        """
        :param failChance: (qreal | float | int) 0..1
        :return:
        """
        self.__m_failChance = float(clamp(float(failChance), 0.0, 1.0))  # type: float
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

    def getRobotColor(self):
        """
        :return: QColor
        """
        return self.__m_robotColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setRobotColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        self.__m_robotColor = color  # type: QColor
        self.update()

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(360, 190)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(240, 140)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(RobotCheckWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(RobotCheckWidget, self).hideEvent(event)

    def mouseReleaseEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        panel = self._panel()  # type: QRectF
        hit = QRectF(panel.left(), panel.top(), panel.width() * 0.7, panel.height())  # type: QRectF
        if e.button() == Qt.LeftButton and hit.contains(eventPos(e)):
            self.verify()
        super(RobotCheckWidget, self).mouseReleaseEvent(e)

    def keyPressEvent(self, e):
        """
        :param e: QKeyEvent
        :return:
        """
        if e.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
            self.verify()
            return
        super(RobotCheckWidget, self).keyPressEvent(e)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        since = now - self.__m_modeAt  # type: float
        mode = self.__m_mode  # type: int
        if mode == CHECKING and since >= self.CHECK_TIME:
            if random() < self.__m_failChance:
                self._setMode(FAILED)
                self.failed.emit()
            else:
                self._setMode(VERIFIED)
                self.verified.emit()
        elif mode == FAILED and since > 2.6:
            self._setMode(IDLE)
        # How far the robot pokes out from behind the panel.
        if mode == CHECKING:
            target = 1.0  # type: float
        elif mode == VERIFIED:
            target = 1.0 if since < 2.6 else 0.12  # type: float
        elif mode == FAILED:
            target = 0.75  # type: float
        else:
            target = 0.32 if (now % 6.0) > 4.8 else 0.12  # type: float  # occasional peek
        self.__m_riseVel += ((target - self.__m_rise) * 160.0 - self.__m_riseVel * 14.0) * dt
        self.__m_rise += self.__m_riseVel * dt
        self.update()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        now = self._now()  # type: float
        panel = self._panel()  # type: QRectF
        mode = self.__m_mode  # type: int
        since = now - self.__m_modeAt  # type: float
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        # Robot first, so the panel hides its lower half.
        s = min(panel.height() * 1.05, (panel.top() - 4.0) * 0.95)  # type: float
        rx = panel.left() + panel.width() * 0.63  # type: float
        ry = panel.top() + s * 0.55 - self.__m_rise * s * 0.95  # type: float
        self._drawRobot(p, QPointF(rx, ry), s, mode, since, now)
        # Panel.
        p.setPen(QPen(QColor(0, 0, 0, 40), 1.0))
        p.setBrush(self.__m_panelColor)
        p.drawRoundedRect(panel, 6, 6)
        # Robot hands gripping the panel edge while it peeks.
        if self.__m_rise > 0.25:
            p.setPen(QPen(self.__m_robotColor.darker(140), 1.2))
            p.setBrush(self.__m_robotColor)
            for d in (-1.0, 1.0):
                if mode == VERIFIED and d > 0 and since < 2.6:
                    continue
                p.drawRoundedRect(QRectF(rx + d * s * 0.42 - s * 0.08, panel.top() - s * 0.05, s * 0.16, s * 0.1), 3, 3)
        # Checkbox.
        bs = min(28.0, panel.height() * 0.38)  # type: float
        box = QRectF(panel.left() + 16.0, panel.center().y() - bs / 2.0, bs, bs)  # type: QRectF
        self.__m_boxRect = box  # type: QRectF
        tc = self.__m_textColor  # type: QColor
        if mode == CHECKING:
            p.setPen(QPen(QColor('#4A90E2'), 3.0, Qt.SolidLine, Qt.RoundCap))
            p.setBrush(Qt.NoBrush)
            start = int((now * 540.0) % 360.0) * 16  # type: int
            span = int(90 + 120 * abs(sin(now * 3.0))) * 16  # type: int
            p.drawArc(box.adjusted(2, 2, -2, -2), start, span)
        elif mode == VERIFIED:
            k = clamp(since / 0.35, 0.0, 1.0)  # type: float
            p.setPen(QPen(QColor('#1FA463'), 3.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            a = QPointF(box.left() + bs * 0.18, box.top() + bs * 0.52)  # type: QPointF
            b = QPointF(box.left() + bs * 0.42, box.top() + bs * 0.76)  # type: QPointF
            c = QPointF(box.left() + bs * 0.86, box.top() + bs * 0.2)  # type: QPointF
            if k < 0.4:
                t = k / 0.4  # type: float
                p.drawLine(a, QPointF(a.x() + (b.x() - a.x()) * t, a.y() + (b.y() - a.y()) * t))
            else:
                t = (k - 0.4) / 0.6  # type: float
                path = QPainterPath()  # type: QPainterPath
                path.moveTo(a)
                path.lineTo(b)
                path.lineTo(QPointF(b.x() + (c.x() - b.x()) * t, b.y() + (c.y() - b.y()) * t))
                p.setBrush(Qt.NoBrush)
                p.drawPath(path)
        else:
            border = QColor('#E63946') if mode == FAILED else QColor(tc)  # type: QColor
            if mode != FAILED:
                border.setAlpha(120)
            p.setPen(QPen(border, 2.0))
            p.setBrush(QColor('#FFFFFF') if self.__m_panelColor.lightness() > 128 else self.__m_panelColor.lighter(130))
            p.drawRoundedRect(box, 3, 3)
            if mode == FAILED:
                p.setPen(QPen(QColor('#E63946'), 3.0, Qt.SolidLine, Qt.RoundCap))
                p.drawLine(box.topLeft() + QPointF(7, 7), box.bottomRight() - QPointF(7, 7))
                p.drawLine(QPointF(box.right() - 7, box.top() + 7), QPointF(box.left() + 7, box.bottom() - 7))
        # Label.
        f = QFont(self.font())  # type: QFont
        f.setPointSizeF(10.5)
        p.setFont(f)
        if mode == VERIFIED:
            label = self.__m_verifiedText  # type: str
        elif mode == FAILED:
            label = self.tr('Suspiciously robotic. Try again.')  # type: str
        else:
            label = self.__m_text  # type: str
        p.setPen(QColor('#E63946') if mode == FAILED else tc)
        p.drawText(QRectF(box.right() + 12.0, panel.top(), panel.width() * 0.62 - bs - 28.0, panel.height()),
                   Qt.AlignVCenter | Qt.AlignLeft | Qt.TextWordWrap, label)
        # Logo block.
        lx = panel.right() - panel.width() * 0.24  # type: float
        lc = QPointF(lx + panel.width() * 0.12, panel.top() + panel.height() * 0.36)  # type: QPointF
        lr = panel.height() * 0.17  # type: float
        p.setPen(QPen(QColor('#4A90E2'), max(2.0, lr * 0.3), Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        rot = now * 40.0 if mode == CHECKING else 0.0  # type: float
        for k in range(3):
            st = int((rot + k * 120 + 20) * 16)  # type: int
            p.drawArc(QRectF(lc.x() - lr, lc.y() - lr, lr * 2, lr * 2), st, 80 * 16)
        f2 = QFont(self.font())  # type: QFont
        f2.setPointSizeF(7.0)
        p.setFont(f2)
        sub = QColor(tc)  # type: QColor
        sub.setAlpha(150)
        p.setPen(sub)
        p.drawText(QRectF(lx, lc.y() + lr + 2.0, panel.width() * 0.24, 12.0), Qt.AlignCenter, 'notCAPTCHA')
        f2.setPointSizeF(6.0)
        p.setFont(f2)
        p.drawText(QRectF(lx, lc.y() + lr + 13.0, panel.width() * 0.24, 10.0), Qt.AlignCenter, self.tr('Privacy - Terms'))
        p.end()

    def _drawRobot(self, p, c, s, mode, since, now):
        """
        :param p: QPainter
        :param c: (QPointF) head center
        :param s: (qreal | float | int) size
        :param mode: int
        :param since: qreal | float | int
        :param now: qreal | float | int
        :return:
        """
        rc = self.__m_robotColor  # type: QColor
        dark = QColor('#2B2F3A')  # type: QColor
        hw = s * 0.8  # type: float
        hh = s * 0.6  # type: float
        head = QRectF(c.x() - hw / 2.0, c.y() - hh / 2.0, hw, hh)  # type: QRectF
        # Antenna.
        p.setPen(QPen(rc.darker(140), max(1.5, s * 0.03)))
        p.drawLine(QPointF(c.x(), head.top()), QPointF(c.x(), head.top() - s * 0.2))
        on = (now % 1.0) < 0.5 or mode == CHECKING  # type: bool
        bulb = QColor('#E63946') if on else QColor('#7A2A30')  # type: QColor
        if mode == VERIFIED:
            bulb = QColor('#3BCEAC')  # type: QColor
        p.setPen(Qt.NoPen)
        p.setBrush(bulb)
        p.drawEllipse(QPointF(c.x(), head.top() - s * 0.22), s * 0.055, s * 0.055)
        # Head + ear bolts.
        p.setPen(QPen(rc.darker(150), max(1.0, s * 0.02)))
        p.setBrush(rc)
        for d in (-1.0, 1.0):
            p.drawRoundedRect(QRectF(c.x() + d * hw / 2.0 - s * 0.05, c.y() - s * 0.08, s * 0.1, s * 0.16), 2, 2)
        p.drawRoundedRect(head, s * 0.12, s * 0.12)
        # Visor with LED eyes.
        visor = QRectF(head.left() + hw * 0.12, head.top() + hh * 0.18, hw * 0.76, hh * 0.38)  # type: QRectF
        p.setPen(Qt.NoPen)
        p.setBrush(dark)
        p.drawRoundedRect(visor, hh * 0.12, hh * 0.12)
        led = QColor('#6FE3FF')  # type: QColor
        er = visor.height() * 0.3  # type: float
        dart = sin(now * 12.0) * visor.width() * 0.06 if mode == CHECKING else 0.0  # type: float
        for d in (-1.0, 1.0):
            ex = visor.center().x() + d * visor.width() * 0.22 + dart  # type: float
            ey = visor.center().y()  # type: float
            if mode == VERIFIED and d > 0 and since < 2.6:
                p.setPen(QPen(led, max(1.5, er * 0.5), Qt.SolidLine, Qt.RoundCap))
                p.drawLine(QPointF(ex - er, ey), QPointF(ex + er, ey))  # wink
                p.setPen(Qt.NoPen)
                continue
            if mode == FAILED:
                p.setPen(QPen(QColor('#FF6B6B'), max(1.5, er * 0.45), Qt.SolidLine, Qt.RoundCap))
                p.drawLine(QPointF(ex - er * 0.8, ey - er * 0.8), QPointF(ex + er * 0.8, ey + er * 0.8))
                p.drawLine(QPointF(ex - er * 0.8, ey + er * 0.8), QPointF(ex + er * 0.8, ey - er * 0.8))
                p.setPen(Qt.NoPen)
                continue
            glow = QColor(led)  # type: QColor
            glow.setAlpha(80)
            p.setBrush(glow)
            p.drawEllipse(QPointF(ex, ey), er * 1.5, er * 1.5)
            p.setBrush(led)
            p.drawEllipse(QPointF(ex, ey), er, er * (0.45 if mode == CHECKING else 1.0))
        # Mouth grille.
        mouth = QRectF(c.x() - hw * 0.22, head.top() + hh * 0.66, hw * 0.44, hh * 0.16)  # type: QRectF
        p.setBrush(dark)
        p.drawRoundedRect(mouth, 2, 2)
        p.setPen(QPen(rc, max(1.0, s * 0.015)))
        for k in range(1, 5):
            x = mouth.left() + mouth.width() * k / 5.0  # type: float
            wob = sin(now * 30.0 + k) * mouth.height() * 0.2 if mode == CHECKING else 0.0  # type: float
            p.drawLine(QPointF(x, mouth.top() + 1 + wob), QPointF(x, mouth.bottom() - 1))
        # Oil sweat while being "checked".
        if mode == CHECKING:
            for k in range(2):
                t = (now * 1.2 + k * 0.5) % 1.0  # type: float
                oc = QColor('#3A3020')  # type: QColor
                oc.setAlpha(int(230 * (1.0 - t)))
                x = head.right() - hw * 0.08 + k * hw * 0.1  # type: float
                y = head.top() + hh * 0.1 + t * hh * 0.5  # type: float
                drop = QPainterPath()  # type: QPainterPath
                drop.moveTo(x, y - 5.0)
                drop.quadTo(x + 3.5, y + 1.0, x, y + 3.0)
                drop.quadTo(x - 3.5, y + 1.0, x, y - 5.0)
                p.fillPath(drop, oc)
        # Thumbs-up when verified.
        if mode == VERIFIED and since < 2.6:
            hx = head.right() + s * 0.18  # type: float
            hy = head.center().y() + s * 0.05  # type: float
            p.setPen(QPen(rc.darker(150), max(1.0, s * 0.02)))
            p.setBrush(rc)
            p.drawRoundedRect(QRectF(hx - s * 0.1, hy - s * 0.05, s * 0.2, s * 0.18), 4, 4)
            p.drawRoundedRect(QRectF(hx - s * 0.05, hy - s * 0.2, s * 0.08, s * 0.17), 3, 3)
        # Speech.
        speech = ''  # type: str
        if mode == CHECKING:
            speech = self.tr('beep...?') if since < 0.9 else self.tr('Calculating humanity...')  # type: str
        elif mode == VERIFIED and since < 2.6:
            speech = self.tr('Definitely human. Totally.')  # type: str
        elif mode == FAILED:
            speech = self.tr('Oh no. One of us!')  # type: str
        if speech and self.__m_rise > 0.6:
            f = QFont(self.font())  # type: QFont
            f.setPointSizeF(8.5)
            f.setBold(True)
            fm = QFontMetricsF(f)  # type: QFontMetricsF
            tw = fm.horizontalAdvance(speech) if hasattr(fm, 'horizontalAdvance') else fm.width(speech)  # type: float
            bw = tw + 16.0  # type: float
            bh = fm.height() + 8.0  # type: float
            bx = clamp(head.left() - bw - 6.0, 2.0, self.width() - bw - 2.0)  # type: float
            by = max(2.0, head.top() - bh * 0.4)  # type: float
            path = QPainterPath()  # type: QPainterPath
            path.addRoundedRect(QRectF(bx, by, bw, bh), bh / 2.0, bh / 2.0)
            p.setPen(QPen(QColor(20, 20, 30, 60), 1.0))
            p.setBrush(QColor('#FFFFFF'))
            p.drawPath(path)
            p.setFont(f)
            p.setPen(QColor('#22222A'))
            p.drawText(QRectF(bx, by, bw, bh), Qt.AlignCenter, speech)

    # ---------- Properties ----------
    text = pyqtProperty('QString', fget=getText, fset=setText)  # type: pyqtProperty
    verifiedText = pyqtProperty('QString', fget=getVerifiedText, fset=setVerifiedText)  # type: pyqtProperty
    failChance = pyqtProperty('qreal', fget=getFailChance, fset=setFailChance)  # type: pyqtProperty
    panelColor = pyqtProperty(QColor, fget=getPanelColor, fset=setPanelColor)  # type: pyqtProperty
    textColor = pyqtProperty(QColor, fget=getTextColor, fset=setTextColor)  # type: pyqtProperty
    robotColor = pyqtProperty(QColor, fget=getRobotColor, fset=setRobotColor)  # type: pyqtProperty
