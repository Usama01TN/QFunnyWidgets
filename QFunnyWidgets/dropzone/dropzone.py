# -*- coding: utf-8 -*-
"""
DropZoneMonsterWidget: a file-upload drop zone guarded by a hungry monster. Drag files over it and
it opens wide (drooling, "FEED ME!"); drop them and it chomps three times, sprays paper bits and
burps. Files with the wrong extension make it stick its tongue out. Click it to browse instead.
"""
from ManyQt.QtCore import Qt, QTimer, QElapsedTimer, QSize, QRectF, QPointF, pyqtSignal, pyqtSlot, pyqtProperty
from ManyQt.QtGui import QPainter, QColor, QPen, QPainterPath, QFont, QCursor
from ManyQt.QtWidgets import QWidget, QFileDialog
from math import sin, cos, pi
from os.path import splitext
from random import uniform

IDLE, HUNGRY, YUCK, EATING, REFUSED = range(5)  # type: tuple


def clamp(x, a, b):
    """
    :param x: qreal | float | int
    :param a: qreal | float | int
    :param b: qreal | float | int
    :return: qreal | float | int
    """
    return a if x < a else b if x > b else x


class Bit(object):
    """
    A shredded paper bit.
    """

    def __init__(self, x=0.0, y=0.0, vx=0.0, vy=0.0, rot=0.0, vrot=0.0, life=1.0):
        """
        :param x: qreal | float | int
        :param y: qreal | float | int
        :param vx: qreal | float | int
        :param vy: qreal | float | int
        :param rot: (qreal | float | int) degrees
        :param vrot: (qreal | float | int) degrees/s
        :param life: (qreal | float | int) s
        """
        self.x = float(x)  # type: float
        self.y = float(y)  # type: float
        self.vx = float(vx)  # type: float
        self.vy = float(vy)  # type: float
        self.rot = float(rot)  # type: float
        self.vrot = float(vrot)  # type: float
        self.life = float(life)  # type: float


class DropZoneMonsterWidget(QWidget):
    """
    Drag-and-drop file zone with an appetite.
    """
    EAT_TIME = 1.25  # type: float
    BURP_TIME = 0.9  # type: float
    filesDropped = pyqtSignal(list)  # type: pyqtSignal
    filesRejected = pyqtSignal(list)  # type: pyqtSignal

    def __init__(self, *args, **kwargs):
        """
        :param acceptedExtensions: (list[str | unicode | QString]) e.g. ['png', 'jpg']; empty accepts everything.
        :param hint: (str | unicode | QString) Main label while idle.
        :param subtitle: (str | unicode | QString) Small label while idle.
        :param monsterColor: QColor | Qt.GlobalColor | int | str | QString
        :param accentColor: QColor | Qt.GlobalColor | int | str | QString
        :param clickToBrowse: (bool) Clicking opens a file dialog.
        :param filesDropped: callable | None
        :param filesRejected: callable | None
        :param args: any
        :param kwargs: any
        """
        acceptedExtensions = kwargs.pop('acceptedExtensions', [])  # type: list[str]
        hint = kwargs.pop('hint', 'Drop files here')  # type: str
        subtitle = kwargs.pop('subtitle', "He's hungry. Or click to browse.")  # type: str
        monsterColor = kwargs.pop('monsterColor', '#7BD389')  # type: QColor
        accentColor = kwargs.pop('accentColor', '#5E60CE')  # type: QColor
        clickToBrowse = kwargs.pop('clickToBrowse', True)  # type: bool
        filesDropped = kwargs.pop('filesDropped', None)  # type: callable | None
        filesRejected = kwargs.pop('filesRejected', None)  # type: callable | None
        super(DropZoneMonsterWidget, self).__init__(*args, **kwargs)
        # Options.
        self.__m_exts = [e.lower().lstrip('.') for e in acceptedExtensions]  # type: list[str]
        self.__m_hint = hint  # type: str
        self.__m_subtitle = subtitle  # type: str
        self.__m_monsterColor = QColor(monsterColor)  # type: QColor
        self.__m_accentColor = QColor(accentColor)  # type: QColor
        self.__m_clickToBrowse = bool(clickToBrowse)  # type: bool
        if callable(filesDropped):
            self.filesDropped.connect(filesDropped)
        if callable(filesRejected):
            self.filesRejected.connect(filesRejected)
        # Widget flags.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor if clickToBrowse else Qt.ArrowCursor)
        # State.
        self.__m_mode = IDLE  # type: int
        self.__m_modeAt = 0.0  # type: float
        self.__m_eaten = 0  # type: int
        self.__m_lastBatch = 0  # type: int
        self.__m_bits = []  # type: list[Bit]
        self.__m_bitAcc = 0.0  # type: float
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

    def _setMode(self, mode):
        """
        :param mode: int
        :return:
        """
        self.__m_mode = mode  # type: int
        self.__m_modeAt = self._now()  # type: float
        self.update()

    def _accepts(self, path):
        """
        :param path: str
        :return: bool
        """
        if not self.__m_exts:
            return True
        return splitext(path)[1].lower().lstrip('.') in self.__m_exts

    def _split(self, mime):
        """
        :param mime: QMimeData
        :return: (tuple) accepted list[str], rejected list[str]
        """
        paths = [u.toLocalFile() or u.toString() for u in mime.urls()] if mime.hasUrls() else []  # type: list[str]
        good = [p for p in paths if self._accepts(p)]  # type: list[str]
        bad = [p for p in paths if not self._accepts(p)]  # type: list[str]
        return good, bad

    def _geometry(self):
        """
        :return: (tuple) zone QRectF, monster center QPointF, monster size float
        """
        zone = QRectF(self.rect()).adjusted(4, 4, -4, -4)  # type: QRectF
        s = max(30.0, min(zone.width() * 0.42, (zone.height() - 60.0) * 0.8))  # type: float
        c = QPointF(zone.center().x(), zone.top() + 14.0 + s * 0.55)  # type: QPointF
        return zone, c, s

    # ---------- Public API ----------
    @pyqtSlot(list)
    def feed(self, paths):
        """
        Hand files to the monster programmatically.

        :param paths: list[str | unicode | QString]
        :return:
        """
        good = [p for p in paths if self._accepts(p)]  # type: list[str]
        bad = [p for p in paths if not self._accepts(p)]  # type: list[str]
        if bad:
            self.filesRejected.emit(bad)
        if good:
            self.__m_eaten += len(good)
            self.__m_lastBatch = len(good)  # type: int
            self._setMode(EATING)
            self.filesDropped.emit(good)
        elif bad:
            self._setMode(REFUSED)

    @pyqtSlot()
    def browse(self):
        """
        Open a file dialog and feed the chosen files.
        :return:
        """
        filt = 'Tasty files ({})'.format(' '.join('*.' + e for e in self.__m_exts)) if self.__m_exts else 'All files (*)'  # type: str
        paths, _ = QFileDialog.getOpenFileNames(self, self.tr('Feed the monster'), '', filt)
        if paths:
            self.feed(paths)

    def getEaten(self):
        """
        :return: (int) Total files eaten.
        """
        return self.__m_eaten

    def getAcceptedExtensions(self):
        """
        :return: list[str | unicode | QString]
        """
        return list(self.__m_exts)

    @pyqtSlot(list)
    def setAcceptedExtensions(self, exts):
        """
        :param exts: list[str]
        :return:
        """
        self.__m_exts = [e.lower().lstrip('.') for e in exts]  # type: list[str]

    def getHint(self):
        """
        :return: str | unicode | QString
        """
        return self.__m_hint

    @pyqtSlot('QString')
    @pyqtSlot(str)
    def setHint(self, hint):
        """
        :param hint: str | unicode | QString
        :return:
        """
        self.__m_hint = hint  # type: str
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

    def getMonsterColor(self):
        """
        :return: QColor
        """
        return self.__m_monsterColor

    @pyqtSlot(QColor)
    @pyqtSlot(Qt.GlobalColor)
    @pyqtSlot(int)
    @pyqtSlot(str)
    @pyqtSlot('QString')
    def setMonsterColor(self, color):
        """
        :param color: QColor | Qt.GlobalColor | int | str | QString
        :return:
        """
        if not isinstance(color, QColor):
            color = QColor(color)  # type: QColor
        if self.__m_monsterColor != color:
            self.__m_monsterColor = color  # type: QColor
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

    def isClickToBrowse(self):
        """
        :return: bool
        """
        return self.__m_clickToBrowse

    @pyqtSlot(bool)
    @pyqtSlot(int)
    def setClickToBrowse(self, clickToBrowse):
        """
        :param clickToBrowse: bool
        :return:
        """
        self.__m_clickToBrowse = bool(clickToBrowse)  # type: bool
        self.setCursor(Qt.PointingHandCursor if clickToBrowse else Qt.ArrowCursor)

    # ---------- Qt overrides ----------
    def sizeHint(self):
        """
        :return: QSize
        """
        return QSize(360, 300)

    def minimumSizeHint(self):
        """
        :return: QSize
        """
        return QSize(200, 180)

    def showEvent(self, event):
        """
        :param event: QShowEvent
        :return:
        """
        super(DropZoneMonsterWidget, self).showEvent(event)
        if not self.__m_timer.isActive():
            self.__m_timer.start(16)

    def hideEvent(self, event):
        """
        :param event: QHideEvent
        :return:
        """
        self.__m_timer.stop()
        super(DropZoneMonsterWidget, self).hideEvent(event)

    def dragEnterEvent(self, e):
        """
        :param e: QDragEnterEvent
        :return:
        """
        if e.mimeData().hasUrls():
            good, bad = self._split(e.mimeData())
            self._setMode(HUNGRY if good else YUCK)
            e.acceptProposedAction()
        else:
            e.ignore()

    def dragLeaveEvent(self, e):
        """
        :param e: QDragLeaveEvent
        :return:
        """
        if self.__m_mode in (HUNGRY, YUCK):
            self._setMode(IDLE)
        super(DropZoneMonsterWidget, self).dragLeaveEvent(e)

    def dropEvent(self, e):
        """
        :param e: QDropEvent
        :return:
        """
        good, bad = self._split(e.mimeData())
        e.acceptProposedAction()
        self.feed(good + bad)

    def mouseReleaseEvent(self, e):
        """
        :param e: QMouseEvent
        :return:
        """
        if e.button() == Qt.LeftButton and self.__m_clickToBrowse and self.rect().contains(e.pos()) \
                and self.__m_mode in (IDLE, REFUSED):
            self.browse()
        super(DropZoneMonsterWidget, self).mouseReleaseEvent(e)

    # ---------- Animation tick ----------
    def _tick(self):
        """
        :return:
        """
        now = self._now()  # type: float
        dt = min(0.05, max(0.0, now - self.__m_last))  # type: float
        self.__m_last = now  # type: float
        since = now - self.__m_modeAt  # type: float
        zone, c, s = self._geometry()
        if self.__m_mode == EATING:
            if since < self.EAT_TIME:
                self.__m_bitAcc += dt * 30.0
                while self.__m_bitAcc > 1.0:
                    self.__m_bitAcc -= 1.0
                    a = uniform(-pi * 0.9, -pi * 0.1)  # type: float
                    sp = uniform(80, 220)  # type: float
                    self.__m_bits.append(Bit(c.x() + uniform(-s * 0.15, s * 0.15), c.y() + s * 0.12, cos(a) * sp,
                                             sin(a) * sp, uniform(0, 360), uniform(-600, 600), uniform(0.6, 1.0)))
            elif since > self.EAT_TIME + self.BURP_TIME + 0.4:
                self._setMode(IDLE)
        elif self.__m_mode == REFUSED and since > 1.6:
            self._setMode(IDLE)
        if now >= self.__m_blinkAt + 0.14:
            self.__m_blinkAt = now + uniform(2.0, 4.5)  # type: float
        alive = []  # type: list[Bit]
        for b in self.__m_bits:
            b.vy += 600.0 * dt
            b.x += b.vx * dt
            b.y += b.vy * dt
            b.rot += b.vrot * dt
            b.life -= dt
            if b.life > 0:
                alive.append(b)
        self.__m_bits = alive  # type: list[Bit]
        self.update()

    # ---------- Painting ----------
    def paintEvent(self, event):
        """
        :param event: QPaintEvent
        :return:
        """
        now = self._now()  # type: float
        zone, c, s = self._geometry()
        mode = self.__m_mode  # type: int
        since = now - self.__m_modeAt  # type: float
        p = QPainter(self)  # type: QPainter
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing, True)
        # Zone with marching-ants border.
        txt = QColor(self.palette().text().color())  # type: QColor
        if mode == HUNGRY:
            bc = QColor(self.__m_accentColor)  # type: QColor
        elif mode in (YUCK, REFUSED):
            bc = QColor('#E63946')  # type: QColor
        else:
            bc = QColor(txt)  # type: QColor
            bc.setAlpha(80)
        fill = QColor(bc)  # type: QColor
        fill.setAlpha(28 if mode in (HUNGRY, YUCK) else 0)
        pen = QPen(bc, 2.0)  # type: QPen
        pen.setDashPattern([6.0, 5.0])
        pen.setDashOffset(-now * 20.0 if mode == HUNGRY else 0.0)
        p.setPen(pen)
        p.setBrush(fill)
        p.drawRoundedRect(zone, 18, 18)
        # Monster.
        p.save()
        shake = sin(since * 30.0) * s * 0.05 * max(0.0, 1.0 - since / 0.8) if mode in (YUCK, REFUSED) else 0.0  # type: float
        p.translate(c.x() + shake, c.y())
        self._drawMonster(p, s, mode, since, now)
        p.restore()
        # Paper bits.
        p.setPen(Qt.NoPen)
        for b in self.__m_bits:
            pc = QColor('#FFFFFF')  # type: QColor
            pc.setAlpha(int(255 * clamp(b.life, 0.0, 1.0)))
            p.save()
            p.translate(b.x, b.y)
            p.rotate(b.rot)
            p.setBrush(pc)
            p.drawRect(QRectF(-4, -2.5, 8, 5))
            p.setPen(QPen(QColor(120, 140, 200, pc.alpha()), 0.8))
            p.drawLine(QPointF(-3, 0), QPointF(3, 0))
            p.setPen(Qt.NoPen)
            p.restore()
        # Labels.
        if mode == HUNGRY:
            main, sub = self.tr('FEED ME!'), self.tr('Let go. He has been waiting.')
        elif mode in (YUCK, REFUSED):
            main = self.tr('Yuck!')  # type: str
            sub = self.tr('I only eat: {}').format(', '.join('.' + e for e in self.__m_exts)) if self.__m_exts else ''  # type: str
        elif mode == EATING:
            if since < self.EAT_TIME:
                main, sub = self.tr('Nom nom nom...'), self.tr('{} file(s) incoming').format(self.__m_lastBatch)
            else:
                main, sub = self.tr('*burp*'), self.tr('Thanks! That hit the spot.')
        else:
            main, sub = self.__m_hint, self.__m_subtitle
        ty = c.y() + s * 0.62 + 6.0  # type: float
        f = QFont(self.font())  # type: QFont
        f.setBold(True)
        f.setPointSizeF(clamp(s * 0.1, 10.0, 15.0))
        p.setFont(f)
        p.setPen(bc if mode in (HUNGRY, YUCK, REFUSED) else txt)
        p.drawText(QRectF(zone.left(), ty, zone.width(), 24.0), Qt.AlignCenter, main)
        if sub:
            f2 = QFont(self.font())  # type: QFont
            f2.setPointSizeF(8.5)
            p.setFont(f2)
            sc = QColor(txt)  # type: QColor
            sc.setAlpha(160)
            p.setPen(sc)
            p.drawText(QRectF(zone.left() + 8, ty + 24.0, zone.width() - 16, 18.0), Qt.AlignCenter, sub)
        if self.__m_eaten:
            f3 = QFont(self.font())  # type: QFont
            f3.setPointSizeF(8.0)
            p.setFont(f3)
            cc = QColor(txt)  # type: QColor
            cc.setAlpha(140)
            p.setPen(cc)
            p.drawText(QRectF(zone.left() + 12, zone.top() + 8, zone.width() - 24, 16), Qt.AlignRight | Qt.AlignVCenter,
                       self.tr('Eaten: {}').format(self.__m_eaten))
        p.end()

    def _drawMonster(self, p, s, mode, since, now):
        """
        :param p: QPainter
        :param s: (qreal | float | int) size
        :param mode: int
        :param since: (qreal | float | int) time in mode
        :param now: qreal | float | int
        :return:
        """
        mc = self.__m_monsterColor  # type: QColor
        if mode in (YUCK, REFUSED):
            mc = QColor(int(mc.red() * 0.7 + 60), int(mc.green() * 0.85 + 30), int(mc.blue() * 0.5))  # queasy
        ink = QColor('#1E2A22')  # type: QColor
        r = s * 0.5  # type: float
        # Chomp amount: 0 closed .. 1 wide open.
        if mode == HUNGRY:
            mouth = 0.85 + 0.15 * sin(now * 6.0)  # type: float
        elif mode == EATING and since < self.EAT_TIME:
            mouth = abs(sin(since / self.EAT_TIME * pi * 3.0))  # type: float
        else:
            mouth = 0.0  # type: float
        squash = 1.0 - 0.08 * (1.0 - mouth) if mode == EATING and since < self.EAT_TIME else 1.0  # type: float
        bob = sin(now * 2.2) * r * 0.04  # type: float
        if mode == EATING and self.EAT_TIME <= since < self.EAT_TIME + self.BURP_TIME:
            k = (since - self.EAT_TIME) / self.BURP_TIME  # type: float
            squash = 1.0 + 0.12 * sin(k * pi)  # type: float  # burp inflation
        p.translate(0, bob)
        p.scale(1.0 + (1.0 - squash) * 0.6, squash)
        # Horns.
        p.setPen(QPen(mc.darker(150), max(1.0, r * 0.03)))
        p.setBrush(QColor('#F6E7C1'))
        for d in (-1.0, 1.0):
            horn = QPainterPath()  # type: QPainterPath
            horn.moveTo(d * r * 0.45, -r * 0.78)
            horn.quadTo(d * r * 0.7, -r * 1.15, d * r * 0.62, -r * 1.25)
            horn.quadTo(d * r * 0.55, -r * 1.0, d * r * 0.25, -r * 0.88)
            horn.closeSubpath()
            p.drawPath(horn)
        # Wobbly blob body.
        body = QPainterPath()  # type: QPainterPath
        for k in range(49):
            a = k / 48.0 * 2.0 * pi  # type: float
            rr = r * (1.0 + 0.035 * sin(a * 5.0 + now * 3.0))  # type: float
            pt = QPointF(cos(a) * rr * 1.08, sin(a) * rr * 0.95)  # type: QPointF
            if k == 0:
                body.moveTo(pt)
            else:
                body.lineTo(pt)
        body.closeSubpath()
        p.setPen(QPen(mc.darker(140), max(1.5, r * 0.04)))
        p.setBrush(mc)
        p.drawPath(body)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 45))
        p.drawEllipse(QPointF(-r * 0.4, -r * 0.45), r * 0.25, r * 0.14)
        # Spots.
        p.setBrush(mc.darker(115))
        for sx, sy, sr in ((0.7, -0.3, 0.1), (0.78, 0.1, 0.07), (-0.8, 0.2, 0.08)):
            p.drawEllipse(QPointF(sx * r, sy * r), sr * r, sr * r)
        # Eyes (one big, one small, like any respectable monster).
        cur = self.mapFromGlobal(QCursor.pos())  # type: QPoint
        zone, c, s2 = self._geometry()
        lx = clamp((cur.x() - c.x()) / 200.0, -1.0, 1.0)  # type: float
        ly = clamp((cur.y() - c.y()) / 200.0, -1.0, 1.0)  # type: float
        blinking = self.__m_blinkAt <= now < self.__m_blinkAt + 0.14  # type: bool
        happy = mode == EATING  # type: bool
        pen = QPen(ink, max(1.5, r * 0.07), Qt.SolidLine, Qt.RoundCap)  # type: QPen
        for ex, ey, er in ((-r * 0.32, -r * 0.35, r * 0.24), (r * 0.3, -r * 0.4, r * 0.17)):
            if mode in (YUCK, REFUSED):
                p.setPen(pen)
                d = -1.0 if ex < 0 else 1.0  # type: float
                p.drawLine(QPointF(ex - d * er * 0.7, ey - er * 0.6), QPointF(ex + d * er * 0.5, ey))
                p.drawLine(QPointF(ex + d * er * 0.5, ey), QPointF(ex - d * er * 0.7, ey + er * 0.6))
                continue
            if happy or blinking:
                p.setPen(pen)
                p.setBrush(Qt.NoBrush)
                span = (20 * 16, 140 * 16) if happy else (180 * 16, 180 * 16)  # type: tuple
                p.drawArc(QRectF(ex - er * 0.8, ey - er * 0.4, er * 1.6, er * 0.9), span[0], span[1])
                continue
            big = er * (1.25 if mode == HUNGRY else 1.0)  # type: float
            p.setPen(QPen(mc.darker(150), max(1.0, r * 0.03)))
            p.setBrush(QColor('#FFFFFF'))
            p.drawEllipse(QPointF(ex, ey), big, big)
            p.setPen(Qt.NoPen)
            p.setBrush(ink)
            pr = big * (0.6 if mode == HUNGRY else 0.48)  # type: float
            p.drawEllipse(QPointF(ex + lx * (big - pr) * 0.8, ey + ly * (big - pr) * 0.8), pr, pr)
            p.setBrush(QColor('#FFFFFF'))
            p.drawEllipse(QPointF(ex + lx * (big - pr) * 0.8 - pr * 0.35, ey + ly * (big - pr) * 0.8 - pr * 0.35),
                          pr * 0.3, pr * 0.3)
        # Mouth.
        my = r * 0.25  # type: float
        mw = r * 0.62  # type: float
        if mode in (YUCK, REFUSED):
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            wav = QPainterPath()  # type: QPainterPath
            wav.moveTo(-mw * 0.6, my)
            for k in range(1, 7):
                wav.lineTo(-mw * 0.6 + k * mw * 1.2 / 6.0, my + (r * 0.05 if k % 2 else -r * 0.05))
            p.drawPath(wav)
            p.setPen(QPen(QColor('#C2405A'), max(1.0, r * 0.03)))
            p.setBrush(QColor('#FF7A90'))
            p.drawRoundedRect(QRectF(r * 0.02, my + r * 0.02, r * 0.2, r * 0.28), r * 0.1, r * 0.1)  # bleh
            return
        mh = r * 0.55 * mouth  # type: float
        if mh < r * 0.06:
            # Closed grin with one tooth poking out.
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            p.drawArc(QRectF(-mw * 0.6, my - r * 0.2, mw * 1.2, r * 0.35), 200 * 16, 140 * 16)
            p.setPen(QPen(mc.darker(150), max(1.0, r * 0.02)))
            p.setBrush(QColor('#FFFFFF'))
            tooth = QPainterPath()  # type: QPainterPath
            tooth.moveTo(r * 0.12, my + r * 0.13)
            tooth.lineTo(r * 0.26, my + r * 0.1)
            tooth.lineTo(r * 0.2, my + r * 0.26)
            tooth.closeSubpath()
            p.drawPath(tooth)
            return
        mrect = QRectF(-mw, my - mh * 0.4, mw * 2.0, mh)  # type: QRectF
        mp = QPainterPath()  # type: QPainterPath
        mp.addEllipse(mrect)
        p.setPen(pen)
        p.setBrush(QColor('#3B1020'))
        p.drawPath(mp)
        p.save()
        p.setClipPath(mp)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor('#FF7A90'))
        p.drawEllipse(QPointF(0, mrect.bottom()), mw * 0.55, mh * 0.45)
        p.setBrush(QColor('#FFFFFF'))
        n = 6  # type: int
        for k in range(n):
            x = -mw + (k + 0.5) * (2.0 * mw / n)  # type: float
            tw = mw / n * 0.8  # type: float
            top = QPainterPath()  # type: QPainterPath
            top.moveTo(x - tw, mrect.top())
            top.lineTo(x + tw, mrect.top())
            top.lineTo(x, mrect.top() + mh * 0.28)
            top.closeSubpath()
            p.drawPath(top)
            if k % 2 == 1:
                bot = QPainterPath()  # type: QPainterPath
                bot.moveTo(x - tw, mrect.bottom())
                bot.lineTo(x + tw, mrect.bottom())
                bot.lineTo(x, mrect.bottom() - mh * 0.22)
                bot.closeSubpath()
                p.drawPath(bot)
        p.restore()
        # Drool.
        if mode == HUNGRY:
            dl = r * (0.1 + 0.25 * ((now * 0.7) % 1.0))  # type: float
            dc = QColor('#BEE9FF')  # type: QColor
            dc.setAlpha(200)
            p.setPen(QPen(dc, max(2.0, r * 0.06), Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(-mw * 0.5, mrect.bottom() - mh * 0.15), QPointF(-mw * 0.5, mrect.bottom() + dl))

    # ---------- Properties ----------
    acceptedExtensions = pyqtProperty('QStringList', fget=getAcceptedExtensions, fset=setAcceptedExtensions)  # type: pyqtProperty
    hint = pyqtProperty('QString', fget=getHint, fset=setHint)  # type: pyqtProperty
    subtitle = pyqtProperty('QString', fget=getSubtitle, fset=setSubtitle)  # type: pyqtProperty
    monsterColor = pyqtProperty(QColor, fget=getMonsterColor, fset=setMonsterColor)  # type: pyqtProperty
    accentColor = pyqtProperty(QColor, fget=getAccentColor, fset=setAccentColor)  # type: pyqtProperty
    clickToBrowse = pyqtProperty(bool, fget=isClickToBrowse, fset=setClickToBrowse)  # type: pyqtProperty
