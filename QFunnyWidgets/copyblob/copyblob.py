# -*- coding: utf-8 -*-
"""
CopyBlobButtonWidget: a copy-to-clipboard chip (think install commands, API keys, coupon codes) with
a blob mascot. Click it and the text is copied while the blob performs mitosis: it pinches into two,
the clone hops up and vanishes into the clipboard with a sparkle, and a "Copied!" bubble pops up.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QFontMetricsF, QCursor, QKeySequence
from ManyQt.QtWidgets import QWidget, QApplication
from math import sin, cos, pi
from random import uniform

SPLIT = 0.35  # type: float
HOP = 1.0  # type: float
BUBBLE = 1.7  # type: float


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


def easeOut(t):
    """
    :param t: (qreal | float | int) 0..1
    :return: qreal | float | int
    """
    t = clamp(t, 0.0, 1.0)  # type: float
    return 1.0 - (1.0 - t) ** 3


class CopyBlobButtonWidget(QWidget):
    """
    Copy button with a self-replicating mascot.
    """
    copied = pyqtSignal('QString')  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param text: (str | unicode | QString) What gets copied.
        :param label: (str | unicode | QString) What is displayed; empty shows the text itself.
        :param prompt: (str | unicode | QString) Prefix such as "$"; empty hides it.
        :param blobColor: QColor | Qt.GlobalColor | int | str | QString
        :param chipColor: QColor | Qt.GlobalColor | int | str | QString
        :param textColor: QColor | Qt.GlobalColor | int | str | QString
        :param copied: callable | None
        :param args: any
        :param kwargs: any
        """
        text = kwargs.pop('text', 'pip install funnywidgets')  # type: str
        label = kwargs.pop('label', '')  # type: str
        prompt = kwargs.pop('prompt', '$')  # type: str
        blobColor = kwargs.pop('blobColor', '#9BDB4D')  # type: QColor
        chipColor = kwargs.pop('chipColor', '#23252E')  # type: QColor
        textColor = kwargs.pop('textColor', '#E6E8EF')  # type: QColor
        copied = kwargs.pop('copied', None)  # type: callable | None
        super(CopyBlobButtonWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_text = text  # type: str
        self.__m_label = label  # type: str
        self.__m_prompt = prompt  # type: str
        self.__m_blobColor = QColor(blobColor)  # type: QColor
        self.__m_chipColor = QColor(chipColor)  # type: QColor
        self.__m_textColor = QColor(textColor)  # type: QColor
        if callable(copied):
            self.copied.connect(copied)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setToolTip(self.tr('Click to copy'))
        # State.
        self.__m_copiedAt = -10.0  # type: float
        self.__m_pressed = False  # type: bool
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

    def _chip(self):
        """
        :return: QRectF
        """
        h = float(self.height())  # type: float
        ch = clamp(h * 0.42, 34.0, 54.0)  # type: float
        return QRectF(3.0, h - ch - 6.0, self.width() - 6.0, ch)

    # ---------- Public API ----------
    @pyqtSlot()
    def copy(self):
        """
        Copy the text to the clipboard (and replicate the blob).
        :return:
        """
        cb = QApplication.clipboard()
        if cb is not None:
            cb.setText(self.__m_text)
        self.__m_copiedAt = self._now()  # type: float
        self.copied.emit(self.__m_text)
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
        self.update()

    def getLabel(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_label

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setLabel(self, label):
        """
        :param label: str | unicode | QString
        :return:
        """
        self.__m_label = label  # type: str
        self.update()

    def getPrompt(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_prompt

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setPrompt(self, prompt):
        """
        :param prompt: str | unicode | QString
        :return:
        """
        self.__m_prompt = prompt  # type: str
        self.update()

    def getBlobColor(self):
        """
        :return: QColor
        """
        return self.__m_blobColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setBlobColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        self.__m_blobColor = color  # type: QColor
        self.update()

    def getChipColor(self):
        """
        :return: QColor
        """
        return self.__m_chipColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setChipColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        self.__m_chipColor = color  # type: QColor
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
        return QSize(340, 110)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(180, 90)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(CopyBlobButtonWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(CopyBlobButtonWidget, self).hideEvent(event)

    def enterEvent(self, e):
        """
        :param e: QEvent
        :return:
        """
        self.__m_hovered = True  # type: bool
        super(CopyBlobButtonWidget, self).enterEvent(e)

    def leaveEvent(self, e):
        """
        :param e: QEvent
        :return:
        """
        self.__m_hovered = False  # type: bool
        super(CopyBlobButtonWidget, self).leaveEvent(e)

    def mousePressEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if e.button() == Qt.LeftButton and self._chip().contains(eventPos(e)):
            self.__m_pressed = True  # type: bool
        super(CopyBlobButtonWidget, self).mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if self.__m_pressed and self._chip().contains(eventPos(e)):
            self.copy()
        self.__m_pressed = False  # type: bool
        super(CopyBlobButtonWidget, self).mouseReleaseEvent(e)

    def keyPressEvent(self, e):
        """
        :param e: QKeyEvent
        :return:
        """
        if e.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter) or e.matches(QKeySequence.Copy):
            self.copy()
            return
        super(CopyBlobButtonWidget, self).keyPressEvent(e)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        if now >= self.__m_blinkAt + 0.14:
            self.__m_blinkAt = now + uniform(2.0, 4.5)  # type: float
        self.update()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        now = self._now()  # type: float
        chip = self._chip()  # type: QRectF
        since = now - self.__m_copiedAt  # type: float
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        # Chip.
        cc = self.__m_chipColor.lighter(115) if self.__m_hovered else self.__m_chipColor  # type: QColor
        r = chip.height() * 0.3  # type: float
        rect = chip.adjusted(1, 1, -1, -1) if self.__m_pressed else chip  # type: QRectF
        p.setPen(QPen(QColor(255, 255, 255, 25), 1.0))
        p.setBrush(cc)
        p.drawRoundedRect(rect, r, r)
        blobArea = QRectF(rect.right() - rect.height(), rect.top(), rect.height(), rect.height())  # type: QRectF
        p.setPen(QPen(QColor(255, 255, 255, 30), 1.0))
        p.drawLine(QPointF(blobArea.left(), rect.top() + 8), QPointF(blobArea.left(), rect.bottom() - 8))
        # Text.
        f = QFont('Monospace')  # type: QFont
        f.setStyleHint(QFont.TypeWriter)
        f.setPointSizeF(clamp(rect.height() * 0.26, 9.0, 12.0))
        p.setFont(f)
        fm = QFontMetricsF(f)  # type: QFontMetricsF
        x = rect.left() + 14.0  # type: float
        if self.__m_prompt:
            pc = QColor(self.__m_blobColor)  # type: QColor
            p.setPen(pc)
            p.drawText(QRectF(x, rect.top(), 30, rect.height()), Qt.AlignLeft | Qt.AlignVCenter, self.__m_prompt)
            x += (fm.horizontalAdvance(self.__m_prompt + ' ') if hasattr(fm, 'horizontalAdvance') else fm.width(self.__m_prompt + ' '))
        label = self.__m_label or self.__m_text  # type: str
        avail = blobArea.left() - x - 10.0  # type: float
        p.setPen(self.__m_textColor)
        p.drawText(QRectF(x, rect.top(), avail, rect.height()), Qt.AlignLeft | Qt.AlignVCenter,
                   fm.elidedText(label, Qt.ElideMiddle, avail))
        # Blob(s).
        bc = blobArea.center()  # type: QPointF
        br = rect.height() * 0.3  # type: float
        self._drawBlobs(p, bc, br, since, now)
        # "Copied!" bubble.
        if 0.25 < since < BUBBLE:
            a = clamp(min((since - 0.25) * 6.0, (BUBBLE - since) * 4.0), 0.0, 1.0)  # type: float
            bf = QFont(self.font())  # type: QFont
            bf.setBold(True)
            bf.setPointSizeF(8.5)
            bfm = QFontMetricsF(bf)  # type: QFontMetricsF
            txt = self.tr('Copied!')  # type: str
            tw = bfm.horizontalAdvance(txt) if hasattr(bfm, 'horizontalAdvance') else bfm.width(txt)  # type: float
            bw = tw + 16.0  # type: float
            bh = bfm.height() + 8.0  # type: float
            bx = clamp(bc.x() - bw - br * 0.6, 2.0, self.width() - bw - 2.0)  # type: float
            by = max(2.0, chip.top() - bh - 8.0 - (1.0 - a) * 6.0)  # type: float
            p.save()
            p.setOpacity(a)
            p.setPen(Qt.NoPen)
            p.setBrush(self.__m_blobColor)
            p.drawRoundedRect(QRectF(bx, by, bw, bh), bh / 2.0, bh / 2.0)
            p.setFont(bf)
            p.setPen(QColor('#1E2A12'))
            p.drawText(QRectF(bx, by, bw, bh), Qt.AlignCenter, txt)
            p.restore()
        p.end()

    def _drawBlobs(self, p, c, r, since, now):
        """
        :param p: QPainter
        :param c: (QPointF) blob home
        :param r: (qreal | float | int) radius
        :param since: (qreal | float | int) time since the last copy
        :param now: qreal | float | int
        :return:
        """
        if since < SPLIT:
            # Mitosis: two halves separate, pinching at the waist.
            t = easeOut(since / SPLIT)  # type: float
            d = r * 0.85 * t  # type: float
            rr = r * (1.0 - 0.22 * sin(t * pi))  # type: float
            body = QPainterPath()  # type: QPainterPath
            body.addEllipse(QPointF(c.x() - d, c.y()), rr, rr)
            other = QPainterPath()  # type: QPainterPath
            other.addEllipse(QPointF(c.x() + d, c.y()), rr, rr)
            self._paintBlobShape(p, body.united(other))
            for dx in (-d, d):
                self._drawBlobFace(p, QPointF(c.x() + dx, c.y()), rr * 0.9, now, happy=True)
            return
        if since < SPLIT + HOP:
            t = (since - SPLIT) / HOP  # type: float
            # Original slides home; the clone arcs up into "the clipboard".
            home = QPointF(c.x() - r * 0.85 * (1.0 - easeOut(t * 2.0)), c.y())  # type: QPointF
            self._paintBlob(p, home, r, now, happy=True)
            k = clamp(t * 1.15, 0.0, 1.0)  # type: float
            cx = c.x() + r * 0.85 - k * r * 1.2  # type: float
            cy = c.y() - sin(k * pi * 0.8) * r * 3.2 - k * r * 0.8  # type: float
            cr = r * (1.0 - k) ** 0.7  # type: float
            if cr > 1.0:
                self._paintBlob(p, QPointF(cx, cy), cr, now, happy=True)
            elif k >= 1.0 and t < 0.95:
                sc = QColor('#FFF6C8')  # type: QColor
                p.setPen(QPen(sc, 1.6, Qt.SolidLine, Qt.RoundCap))
                for a in range(4):
                    ang = a * pi / 2.0 + now * 3.0  # type: float
                    p.drawLine(QPointF(cx, cy), QPointF(cx + cos(ang) * r * 0.5, cy + sin(ang) * r * 0.5))
            return
        bob = 1.0 + 0.04 * sin(now * 3.0)  # type: float
        self._paintBlob(p, c, r * bob, now, happy=False)

    def _paintBlobShape(self, p, shape):
        """
        :param p: QPainter
        :param shape: QPainterPath
        :return:
        """
        bc = self.__m_blobColor  # type: QColor
        p.setPen(QPen(bc.darker(140), 1.2))
        p.setBrush(bc)
        p.drawPath(shape)

    def _paintBlob(self, p, c, r, now, happy):
        """
        :param p: QPainter
        :param c: QPointF
        :param r: qreal | float | int
        :param now: qreal | float | int
        :param happy: bool
        :return:
        """
        shape = QPainterPath()  # type: QPainterPath
        shape.addEllipse(QPointF(c.x(), c.y() + r * 0.05), r * 1.05, r * 0.95)
        self._paintBlobShape(p, shape)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 80))
        p.drawEllipse(QPointF(c.x() - r * 0.4, c.y() - r * 0.4), r * 0.22, r * 0.13)
        self._drawBlobFace(p, c, r, now, happy)

    def _drawBlobFace(self, p, c, r, now, happy):
        """
        :param p: QPainter
        :param c: QPointF
        :param r: qreal | float | int
        :param now: qreal | float | int
        :param happy: bool
        :return:
        """
        ink = QColor('#1E2A12')  # type: QColor
        ex = r * 0.34  # type: float
        ey = c.y() - r * 0.1  # type: float
        pen = QPen(ink, max(1.0, r * 0.12), Qt.SolidLine, Qt.RoundCap)  # type: QPen
        blinking = self.__m_blinkAt <= now < self.__m_blinkAt + 0.14  # type: bool
        if happy or blinking:
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            span = (20 * 16, 140 * 16) if happy else (180 * 16, 180 * 16)  # type: tuple
            for d in (-1.0, 1.0):
                p.drawArc(QRectF(c.x() + d * ex - r * 0.16, ey - r * 0.1, r * 0.32, r * 0.24), span[0], span[1])
        else:
            cur = self.mapFromGlobal(QCursor.pos())  # type: QPoint
            lx = clamp((cur.x() - c.x()) / 120.0, -1.0, 1.0) * r * 0.08  # type: float
            ly = clamp((cur.y() - c.y()) / 120.0, -1.0, 1.0) * r * 0.08  # type: float
            p.setPen(Qt.NoPen)
            p.setBrush(QColor('#FFFFFF'))
            for d in (-1.0, 1.0):
                p.drawEllipse(QPointF(c.x() + d * ex, ey), r * 0.2, r * 0.22)
            p.setBrush(ink)
            for d in (-1.0, 1.0):
                p.drawEllipse(QPointF(c.x() + d * ex + lx, ey + ly), r * 0.1, r * 0.11)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawArc(QRectF(c.x() - r * 0.2, c.y() + r * 0.05, r * 0.4, r * 0.3), 200 * 16, 140 * 16)

    # ---------- Properties ----------
    text = pyqtProperty('QString', fget=getText, fset=setText)  # type: pyqtProperty
    label = pyqtProperty('QString', fget=getLabel, fset=setLabel)  # type: pyqtProperty
    prompt = pyqtProperty('QString', fget=getPrompt, fset=setPrompt)  # type: pyqtProperty
    blobColor = pyqtProperty(QColor, fget=getBlobColor, fset=setBlobColor)  # type: pyqtProperty
    chipColor = pyqtProperty(QColor, fget=getChipColor, fset=setChipColor)  # type: pyqtProperty
    textColor = pyqtProperty(QColor, fget=getTextColor, fset=setTextColor)  # type: pyqtProperty
