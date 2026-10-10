# -*- coding: utf-8 -*-
"""
Generates <package>/logo.png (beside the widget module) for every widget package by rendering the real widget in its most
characteristic state, cropping to the character and placing it on a rounded-square icon background.
Run from anywhere: python makelogos.py [size]   (QFunnyWidgets/makelogos.py)
"""
from os.path import dirname, join, abspath
from sys import path, argv, exit
from os import environ

environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
ROOT = dirname(abspath(__file__))  # type: str
if dirname(ROOT) not in path:
    path.insert(0, dirname(ROOT))

from ManyQt.QtGui import QImage, QPainter, QColor, QLinearGradient, QPainterPath, QPen, QRegion, QDragEnterEvent
from ManyQt.QtCore import Qt, QTimer, QRect, QRectF, QPoint, QMimeData, QUrl
from ManyQt.QtWidgets import QApplication, QWidget, QScrollArea, QLabel


def contentBox(img, region):
    """
    Bounding box of the non-transparent pixels of img inside region.
    :param img: QImage
    :param region: QRect
    :return: QRect | None
    """
    x0, y0, x1, y1 = region.right(), region.bottom(), region.left(), region.top()
    found = False  # type: bool
    for y in range(region.top(), region.bottom() + 1, 2):
        for x in range(region.left(), region.right() + 1, 2):
            if QColor.fromRgba(img.pixel(x, y)).alpha() > 40:
                found = True  # type: bool
                x0, y0, x1, y1 = min(x0, x), min(y0, y), max(x1, x), max(y1, y)
    if not found:
        return None
    return QRect(x0, y0, x1 - x0 + 2, y1 - y0 + 2).intersected(region)


def clearFaint(img, threshold=40):
    """
    Make almost-transparent pixels (background tints, hairlines) fully transparent.

    :param img: QImage
    :param threshold: (int) alpha below which pixels are removed
    :return: QImage
    """
    out = img.convertToFormat(QImage.Format_ARGB32)  # type: QImage
    for y in range(out.height()):
        for x in range(out.width()):
            if QColor.fromRgba(out.pixel(x, y)).alpha() < threshold:
                out.setPixel(x, y, 0)
    return out


def compose(art, colors, size):
    """
    Place art on a rounded-square gradient icon.

    :param art: (QImage) cropped artwork with alpha
    :param colors: (tuple) top-left, bottom-right hex colours
    :param size: (int) icon size in px
    :return: QImage
    """
    icon = QImage(size, size, QImage.Format_ARGB32_Premultiplied)  # type: QImage
    icon.fill(Qt.transparent)
    p = QPainter(icon)  # type: QPainter
    p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform, True)
    s = float(size)  # type: float
    rect = QRectF(s * 0.03, s * 0.03, s * 0.94, s * 0.94)  # type: QRectF
    shape = QPainterPath()  # type: QPainterPath
    shape.addRoundedRect(rect, s * 0.22, s * 0.22)
    p.fillPath(shape.translated(0, s * 0.012), QColor(0, 0, 0, 60))
    grad = QLinearGradient(rect.topLeft(), rect.bottomRight())  # type: QLinearGradient
    grad.setColorAt(0.0, QColor(colors[0]))
    grad.setColorAt(1.0, QColor(colors[1]))
    p.fillPath(shape, grad)
    p.save()
    p.setClipPath(shape)
    p.fillRect(QRectF(rect.left(), rect.top(), rect.width(), rect.height() * 0.45), QColor(255, 255, 255, 28))
    p.restore()
    p.setPen(QPen(QColor(255, 255, 255, 70), max(1.0, s * 0.008)))
    p.setBrush(Qt.NoBrush)
    p.drawPath(shape)
    # Fit the artwork into ~74 % of the tile, with a soft drop shadow.
    box = s * 0.74  # type: float
    k = min(box / art.width(), box / art.height())  # type: float
    w, h = art.width() * k, art.height() * k
    target = QRectF((s - w) / 2.0, (s - h) / 2.0 + s * 0.01, w, h)  # type: QRectF
    shadow = QImage(art.size(), QImage.Format_ARGB32_Premultiplied)  # type: QImage
    shadow.fill(Qt.transparent)
    sp = QPainter(shadow)  # type: QPainter
    sp.drawImage(0, 0, art)
    sp.setCompositionMode(QPainter.CompositionMode_SourceIn)
    sp.fillRect(shadow.rect(), QColor(0, 0, 0, 70))
    sp.end()
    p.drawImage(target.translated(0, s * 0.018), shadow, QRectF(shadow.rect()))
    p.drawImage(target, art, QRectF(art.rect()))
    p.end()
    return icon


def grabWidget(wdg):
    """
    Render a widget (and its children) without its window background.

    :param wdg: QWidget
    :return: QImage
    """
    img = QImage(wdg.size(), QImage.Format_ARGB32_Premultiplied)  # type: QImage
    img.fill(Qt.transparent)
    p = QPainter(img)  # type: QPainter
    wdg.render(p, QPoint(), QRegion(), QWidget.DrawChildren)
    p.end()
    return img


def configs(F):
    """
    One entry per package: (package, factory, size, waitMs, crop, colours).
    factory(holder) builds the widget, crop is (x0, y0, x1, y1) relative or None.

    :param F: module
    :return: list[tuple]
    """
    import QFunnyWidgets.searchdetective.searchdetective as SD
    from QFunnyWidgets.passwordjudge import JudgeFaceWidget
    from QFunnyWidgets.puffercounter import PufferFooterWidget
    from QFunnyWidgets.catsection import CatHeaderWidget

    def runaway(h):
        """
        :param h: dict
        :return: QWidget
        """
        return F.RunawayButtonWidget(maxEscapes=0)

    def hold(h):
        """
        :param h: dict
        :return: QWidget
        """
        w = F.NervousHoldButtonWidget(stages=['', '', '', ''])  # type: QWidget
        QTimer.singleShot(50, w._NervousHoldButtonWidget__press if hasattr(w, '_NervousHoldButtonWidget__press') else w._press)
        return w

    def toast(h):
        """
        :param h: dict
        :return: QWidget
        """
        holder = QWidget()  # type: QWidget
        holder.resize(330, 170)
        t = F.PigeonToast(holder, caption='', duration=5000)  # type: QWidget
        QTimer.singleShot(30, lambda: t.showMessage('Hi!'))
        h['keep'] = t
        return holder

    def zone(h):
        """
        :param h: dict
        :return: QWidget
        """
        w = F.DropZoneMonsterWidget(hint='', subtitle='', clickToBrowse=False)  # type: QWidget
        m = QMimeData()  # type: QMimeData
        m.setUrls([QUrl.fromLocalFile('/tmp/snack.png')])
        h['mime'] = m
        QTimer.singleShot(50, lambda: QApplication.sendEvent(
            w, QDragEnterEvent(w.rect().center(), Qt.CopyAction, m, Qt.LeftButton, Qt.NoModifier)))
        return w

    def deadline(h):
        """
        :param h: dict
        :return: QWidget
        """
        w = F.DeadlineCountdownWidget(duration=100)  # type: QWidget
        QTimer.singleShot(30, lambda: w.extend(0))
        QTimer.singleShot(40, lambda: w.setTimeScale(400.0))
        return w

    def rocket(h):
        """
        :param h: dict
        :return: QWidget
        """
        area = QScrollArea()  # type: QScrollArea
        lbl = QLabel('\n\n'.join(['x'] * 120))  # type: QLabel
        area.setWidget(lbl)
        area.resize(220, 300)
        area.show()
        r = F.RocketBackToTop(area, threshold=50)  # type: QWidget
        QTimer.singleShot(60, lambda: area.verticalScrollBar().setValue(600))
        h['keep'] = area
        h['target'] = r
        return None

    def copyblob(h):
        """
        :param h: dict
        :return: QWidget
        """
        w = F.CopyBlobButtonWidget(text='', label=' ', prompt='', chipColor=QColor(0, 0, 0, 0))  # type: QWidget
        QTimer.singleShot(820, w.copy)
        return w

    def dachshund(h):
        """
        :param h: dict
        :return: QWidget
        """
        return F.DachshundTabsWidget(tabs=['', ''], trackColor=QColor(0, 0, 0, 0))

    def avatar(h):
        """
        :param h: dict
        :return: QWidget
        """
        return F.PresenceAvatarWidget(name='Funny Widgets', badgeBorderColor='#FFFFFF')

    def pager(h):
        """
        :param h: dict
        :return: QWidget
        """
        w = F.DucklingPagerWidget(count=3, current=0)  # type: QWidget
        QTimer.singleShot(200, lambda: w.setCurrent(2))
        return w

    def robot(h):
        """
        :param h: dict
        :return: QWidget
        """
        w = F.RobotCheckWidget(text='', verifiedText='')  # type: QWidget
        QTimer.singleShot(50, w.verify)
        return w

    def autosave(h):
        """
        :param h: dict
        :return: QWidget
        """
        w = F.AutosaveSquirrelWidget(autosaveDelay=0)  # type: QWidget
        QTimer.singleShot(30, w.markDirty)
        return w

    return [
        ('googlyeyes', lambda h: F.GooglyEyesWidget(), (260, 150), 900, None, ('#FFD23F', '#FF9F1C')),
        ('runawaybutton', runaway, (300, 190), 700, (0.18, 0.28, 0.82, 0.72), ('#FFE5EC', '#FFB3C6')),
        ('jellyswitch', lambda h: F.JellySwitchWidget(checked=True), (150, 90), 900, None, ('#D8F3DC', '#74C69D')),
        ('hamsterloader', lambda h: F.HamsterLoaderWidget(progress=0.55, showPercent=False), (300, 270), 1200,
         (0.0, 0.0, 1.0, 0.7), ('#FFF1E6', '#FFC6A5')),
        ('moodslider', lambda h: F.MoodSliderWidget(value=100, showLabel=False), (110, 110), 900, None, ('#EBFBEE', '#8CE99A')),
        ('ratingstars', lambda h: F.StarRatingWidget(rating=3, maxRating=3, showLabel=False), (260, 110), 1200, None,
         ('#5E60CE', '#7B5CFF')),
        ('holdbutton', hold, (300, 110), 1000, None, ('#FFE3E3', '#FFA8A8')),
        ('panicbell', lambda h: F.PanicBellWidget(count=15, clearOnClick=False), (200, 200), 900, None, ('#E7F5FF', '#74C0FC')),
        ('rubberduck', lambda h: F.RubberDuckWidget(adviceOnClick=False), (240, 220), 900, None, ('#E3FAFC', '#66D9E8')),
        ('passwordjudge', lambda h: JudgeFaceWidget(strength=3, comment=''), (300, 150), 900, (0.0, 0.0, 0.47, 1.0),
         ('#F3F0FF', '#B197FC')),
        ('cookieconsent', lambda h: F.CookieConsentWidget(panelColor=QColor(0, 0, 0, 0), title='', message=''),
         (520, 160), 600, (0.0, 0.0, 0.27, 1.0), ('#FFF4E6', '#FFC078')),
        ('typingindicator', lambda h: F.TypingIndicatorWidget(name=''), (200, 80), 700, None, ('#EDF2FF', '#91A7FF')),
        ('emptystate', lambda h: F.EmptyStateWidget(title='', subtitle='', actionText='', speed=0.35), (260, 200), 2600,
         (0.0, 0.3, 1.0, 1.0), ('#FFF9DB', '#FFE066')),
        ('volumeknob', lambda h: F.VolumeKnobWidget(value=60, showLabel=False), (200, 200), 900, None, ('#343A40', '#212529')),
        ('pigeontoast', toast, (330, 170), 1500, None, ('#E7F5FF', '#A5D8FF')),
        ('dropzone', zone, (300, 260), 700, (0.24, 0.03, 0.76, 0.6), ('#EBFBEE', '#69DB7C')),
        ('batterybuddy', lambda h: F.BatteryBuddyWidget(level=88, showLabel=False), (220, 140), 900, None,
         ('#E6FCF5', '#63E6BE')),
        ('presenceavatar', avatar, (140, 150), 700, None, ('#F8F0FC', '#E599F7')),
        ('ducklingpager', pager, (230, 90), 2200, None, ('#E3FAFC', '#3BC9DB')),
        ('deadline', deadline, (420, 170), 1500, (0.0, 0.0, 0.3, 1.0), ('#FFF0F6', '#FFA8C5')),
        ('searchdetective', lambda h: SD.DetectiveFaceWidget(state=SD.FOUND, comment=''), (330, 150), 900,
         (0.0, 0.0, 0.42, 1.0), ('#FFF4E6', '#FFD8A8')),
        ('robotcheck', robot, (360, 190), 2300, (0.57, 0.0, 0.93, 0.6), ('#E7F5FF', '#4DABF7')),
        ('chameleonpicker', lambda h: F.ChameleonColorPickerWidget(color='#3BCEAC', showHex=False), (460, 220), 900,
         (0.0, 0.05, 0.5, 0.95), ('#F4FCE3', '#C0EB75')),
        ('errorgremlin', lambda h: F.ErrorGremlinWidget(severity=2, title='', message='', retryText='', closable=False),
         (520, 110), 900, (0.03, 0.06, 0.22, 0.94), ('#FFE3E3', '#FF8787')),
        ('snailstepper', lambda h: F.SnailStepperWidget(steps=['', '']), (240, 130), 700, (0.0, 0.0, 0.45, 0.72),
         ('#F4FCE3', '#A9E34B')),
        ('pancakestepper', lambda h: F.PancakeStepperWidget(value=4, maximum=8), (260, 280), 1300, (0.12, 0.25, 0.88, 0.8),
         ('#FFF4E6', '#FFA94D')),
        ('heartlike', lambda h: F.HeartLikeButtonWidget(liked=True, showCount=False), (160, 140), 700, None,
         ('#3D405B', '#2B2D42')),
        ('copyblob', copyblob, (220, 110), 1000, (0.7, 0.48, 1.0, 1.0), ('#F4FCE3', '#94D82D')),
        ('rockettop', rocket, None, 1400, None, ('#3A3F7A', '#1B1F3B')),
        ('catsection', lambda h: CatHeaderWidget(title='', expanded=False), (240, 82), 700, (0.66, 0.0, 1.0, 0.57),
         ('#FFF4E6', '#FFC078')),
        ('dachshundtabs', dachshund, (220, 64), 600, (0.0, 0.0, 0.62, 1.0), ('#FFF4E6', '#E8A87C')),
        ('puffercounter', lambda h: PufferFooterWidget(count=262, maxLength=280), (360, 64), 1200, (0.72, 0.0, 1.0, 1.0),
         ('#E3FAFC', '#3BC9DB')),
        ('helpowl', lambda h: F.HelpOwlWidget(), (120, 140), 700, None, ('#F3F0FF', '#9775FA')),
        ('antbreadcrumb', lambda h: F.AntBreadcrumbWidget(path=['Home']), (120, 60), 900, None,
         ('#FFF9DB', '#FCC419')),
        ('autosave', autosave, (300, 84), 900, (0.0, 0.0, 0.38, 1.0), ('#F4FCE3', '#C0EB75')),
    ]


def main():
    """
    :return: int
    """
    size = int(argv[1]) if len(argv) > 1 else 256  # type: int
    app = QApplication(argv)  # type: QApplication
    import QFunnyWidgets as F
    jobs = []  # type: list
    for name, factory, wsize, wait, crop, colors in configs(F):
        holder = {}  # type: dict
        wdg = factory(holder)  # type: QWidget | None
        if wdg is not None:
            wdg.resize(*wsize)
            wdg.show()
        target = holder.get('target', wdg)  # type: QWidget
        jobs.append((name, target, wait, crop, colors, holder, wdg))
    done = []  # type: list[str]

    def capture(job):
        """
        :param job: tuple
        :return:
        """
        name, target, wait, crop, colors, holder, wdg = job
        img = grabWidget(target)  # type: QImage
        r = QRect(0, 0, img.width(), img.height())  # type: QRect
        if crop:
            r = QRect(int(crop[0] * img.width()), int(crop[1] * img.height()),
                      int((crop[2] - crop[0]) * img.width()), int((crop[3] - crop[1]) * img.height()))
        box = contentBox(img, r)  # type: QRect | None
        if box is None:
            print('  empty render:', name)
            return
        icon = compose(clearFaint(img.copy(box)), colors, size)  # type: QImage
        icon.save(join(ROOT, name, 'logo.png'))  # beside the widget module
        done.append(name)

    for job in jobs:
        QTimer.singleShot(job[2], lambda j=job: capture(j))
    QTimer.singleShot(max(j[2] for j in jobs) + 300, app.quit)
    app.exec_()
    print('{} logos written'.format(len(done)))
    return 0 if len(done) == len(jobs) else 1


if __name__ == '__main__':
    exit(main())
