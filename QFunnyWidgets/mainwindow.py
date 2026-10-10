# coding=utf-8
"""
QFunnyWidgets mainwindow: every widget of the library on one dark, dashboard-style window.
"""
from ManyQt.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout, QWidget, QLabel, QFrame, \
    QGraphicsDropShadowEffect, QPushButton, QButtonGroup, QStackedWidget, QScrollArea, QLineEdit, QPlainTextEdit
from ManyQt.QtGui import QColor, QPalette, QPixmap, QIcon
from ManyQt.QtCore import Qt, QTimer, pyqtSlot
from os.path import dirname, join, exists
from random import choice, random
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .chameleonpicker import ChameleonColorPickerWidget
    from .typingindicator import TypingIndicatorWidget
    from .searchdetective import SearchDetectiveWidget
    from .presenceavatar import PresenceAvatarWidget
    from .pancakestepper import PancakeStepperWidget
    from .holdbutton import NervousHoldButtonWidget
    from .runawaybutton import RunawayButtonWidget
    from .passwordjudge import PasswordJudgeWidget
    from .hamsterloader import HamsterLoaderWidget
    from .cookieconsent import CookieConsentWidget
    from .ducklingpager import DucklingPagerWidget
    from .dachshundtabs import DachshundTabsWidget
    from .antbreadcrumb import AntBreadcrumbWidget
    from .puffercounter import PufferCounterWidget
    from .catsection import SleepyCatSectionWidget
    from .deadline import DeadlineCountdownWidget
    from .batterybuddy import BatteryBuddyWidget
    from .snailstepper import SnailStepperWidget
    from .errorgremlin import ErrorGremlinWidget
    from .heartlike import HeartLikeButtonWidget
    from .autosave import AutosaveSquirrelWidget
    from .dropzone import DropZoneMonsterWidget
    from .copyblob import CopyBlobButtonWidget
    from .jellyswitch import JellySwitchWidget
    from .ratingstars import StarRatingWidget
    from .googlyeyes import GooglyEyesWidget
    from .moodslider import MoodSliderWidget
    from .rubberduck import RubberDuckWidget
    from .emptystate import EmptyStateWidget
    from .volumeknob import VolumeKnobWidget
    from .robotcheck import RobotCheckWidget
    from .rockettop import RocketBackToTop
    from .panicbell import PanicBellWidget
    from .pigeontoast import PigeonToast
    from .helpowl import HelpOwlWidget
except:
    from chameleonpicker import ChameleonColorPickerWidget
    from typingindicator import TypingIndicatorWidget
    from searchdetective import SearchDetectiveWidget
    from presenceavatar import PresenceAvatarWidget
    from pancakestepper import PancakeStepperWidget
    from holdbutton import NervousHoldButtonWidget
    from runawaybutton import RunawayButtonWidget
    from passwordjudge import PasswordJudgeWidget
    from hamsterloader import HamsterLoaderWidget
    from cookieconsent import CookieConsentWidget
    from ducklingpager import DucklingPagerWidget
    from dachshundtabs import DachshundTabsWidget
    from antbreadcrumb import AntBreadcrumbWidget
    from puffercounter import PufferCounterWidget
    from catsection import SleepyCatSectionWidget
    from deadline import DeadlineCountdownWidget
    from batterybuddy import BatteryBuddyWidget
    from snailstepper import SnailStepperWidget
    from errorgremlin import ErrorGremlinWidget
    from heartlike import HeartLikeButtonWidget
    from autosave import AutosaveSquirrelWidget
    from dropzone import DropZoneMonsterWidget
    from copyblob import CopyBlobButtonWidget
    from jellyswitch import JellySwitchWidget
    from ratingstars import StarRatingWidget
    from googlyeyes import GooglyEyesWidget
    from moodslider import MoodSliderWidget
    from rubberduck import RubberDuckWidget
    from emptystate import EmptyStateWidget
    from volumeknob import VolumeKnobWidget
    from robotcheck import RobotCheckWidget
    from rockettop import RocketBackToTop
    from panicbell import PanicBellWidget
    from pigeontoast import PigeonToast
    from helpowl import HelpOwlWidget

PIGEON_MESSAGES = ['File saved successfully.', 'Your build passed! (Somehow.)', '3 new comments on your pull request.',
                   'Meeting moved to 4 pm. Again.', 'Backup complete. Your data is safe-ish.',
                   'Reminder: drink water. Signed, the pigeon.']  # type: list[str]

BACKGROUND = QColor('#121318')  # type: QColor
TEXT = QColor('#ECEDF2')  # type: QColor
STYLE = '''
QMainWindow, #root { background: #121318; }
QFrame#card { background: #1C1E26; border: 1px solid #2A2D38; border-radius: 18px; }
QLabel { color: #ECEDF2; background: transparent; }
QLabel#cardTitle { font-size: 14pt; font-weight: 700; }
QLabel#cardSub { color: #8B8FA3; font-size: 9pt; }
QLabel#appTitle { font-size: 24pt; font-weight: 800; }
QLabel#appSub { color: #8B8FA3; font-size: 11pt; }
QLabel#status { color: #A5A8FF; font-size: 10pt; }
QLabel#pill { background: #2A2D38; color: #C9CBD6; border-radius: 10px; padding: 3px 10px; font-size: 8.5pt; }
QPushButton#nav { background: transparent; color: #8B8FA3; border: 1px solid #2A2D38; border-radius: 16px;
                  padding: 6px 16px; font-weight: 600; font-size: 11pt; }
QPushButton#nav:hover { color: #ECEDF2; border-color: #4A4E5E; }
QPushButton#nav:checked { background: #7B7FFF; color: #FFFFFF; border-color: #7B7FFF; }
QLineEdit { background: #14151B; color: #ECEDF2; border: 1px solid #343846; border-radius: 10px;
            padding: 6px 12px; selection-background-color: #7B7FFF; font-size: 11pt; }
QLineEdit:focus { border-color: #7B7FFF; }
QPushButton#passwordJudgeToggle { background: #2A2D38; color: #ECEDF2; border: none; border-radius: 10px;
                                  padding: 6px 16px; font-weight: 600; font-size: 10.5pt; }
QPushButton#passwordJudgeToggle:checked { background: #7B7FFF; }
QPushButton#action { background: #7B7FFF; color: #FFFFFF; border: none; border-radius: 12px;
                     padding: 8px 18px; font-weight: 700; font-size: 10.5pt; }
QPushButton#action:hover { background: #9295FF; }
QPushButton#ghost { background: transparent; color: #C9CBD6; border: 1px solid #343846; border-radius: 12px;
                    padding: 8px 18px; font-weight: 600; font-size: 10.5pt; }
QPushButton#ghost:hover { border-color: #7B7FFF; color: #FFFFFF; }
QLabel#chatThem { background: #2A2D38; color: #ECEDF2; border-radius: 12px; padding: 8px 12px; }
QLabel#chatMe { background: #7B7FFF; color: #FFFFFF; border-radius: 12px; padding: 8px 12px; }
QLabel#slide { background: #262935; color: #ECEDF2; border-radius: 14px; font-size: 15pt; font-weight: 700; }
QLabel#avatarName { color: #8B8FA3; font-size: 8.5pt; }
QLabel#post { color: #ECEDF2; font-size: 11pt; }
QLabel#changelog { color: #C9CBD6; font-size: 9.5pt; }
QLabel#sectionText { color: #C9CBD6; font-size: 9.5pt; }
QScrollArea#feed { background: transparent; border: none; }
QScrollArea#feed > QWidget > QWidget { background: transparent; }
QScrollBar:vertical { background: #1C1E26; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: #3A3E4C; border-radius: 5px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QPlainTextEdit { background: #14151B; color: #ECEDF2; border: 1px solid #343846; border-radius: 10px;
                 padding: 6px; font-size: 10.5pt; selection-background-color: #7B7FFF; }
QPlainTextEdit:focus { border-color: #7B7FFF; }
QLabel#formLabel { color: #C9CBD6; font-size: 9.5pt; }
QLabel#tabPage { background: #262935; color: #ECEDF2; border-radius: 14px; font-size: 13pt; font-weight: 600; }
'''  # type: str


class Card(QFrame):
    """
    A rounded dashboard card with a title, subtitle and content area.
    """

    def __init__(self, *args, **kwargs):
        """
        :param title: str | unicode | QString
        :param subtitle: str | unicode | QString
        :param tag: (str | unicode | QString) Small pill label at the top right.
        :param logo: (str | unicode | QString) Package name whose logo.png is shown next to the title.
        :param args: any
        :param kwargs: any
        """
        title = kwargs.pop('title', '')  # type: str
        subtitle = kwargs.pop('subtitle', '')  # type: str
        tag = kwargs.pop('tag', '')  # type: str
        logo = kwargs.pop('logo', '')  # type: str
        super(Card, self).__init__(*args, **kwargs)
        self.setObjectName('card')
        shadow = QGraphicsDropShadowEffect(self)  # type: QGraphicsDropShadowEffect
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 120))
        self.setGraphicsEffect(shadow)
        head = QHBoxLayout()  # type: QHBoxLayout
        logoPath = join(dirname(__file__), logo, 'logo.png') if logo else ''  # type: str
        if logoPath and exists(logoPath):
            icon = QLabel()  # type: QLabel
            pix = QPixmap(logoPath)  # type: QPixmap
            icon.setPixmap(pix.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            icon.setFixedSize(42, 42)
            head.addWidget(icon, 0, Qt.AlignTop)
        texts = QVBoxLayout()  # type: QVBoxLayout
        texts.setSpacing(2)
        t = QLabel(title)  # type: QLabel
        t.setObjectName('cardTitle')
        s = QLabel(subtitle)  # type: QLabel
        s.setObjectName('cardSub')
        s.setWordWrap(True)
        texts.addWidget(t)
        texts.addWidget(s)
        head.addLayout(texts, 1)
        if tag:
            pill = QLabel(tag)  # type: QLabel
            pill.setObjectName('pill')
            head.addWidget(pill, 0, Qt.AlignTop)
        self.__m_body = QVBoxLayout()  # type: QVBoxLayout
        layout = QVBoxLayout(self)  # type: QVBoxLayout
        layout.setContentsMargins(20, 18, 20, 18)
        layout.addLayout(head)
        layout.addLayout(self.__m_body, 1)

    def body(self):
        """
        :return: QVBoxLayout
        """
        return self.__m_body


class MainWindow(QMainWindow):
    """
    MainWindow class.
    """

    def __init__(self, *args, **kwargs):
        """
        :param args: any
        :param kwargs: any
        """
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle(self.tr('QFunnyWidgets - Gallery'))
        self.setWindowIcon(QIcon(join(dirname(__file__), 'googlyeyes', 'logo.png')))
        self.resize(1180, 760)
        self.setStyleSheet(STYLE)
        pal = self.palette()  # type: QPalette
        pal.setColor(QPalette.Window, BACKGROUND)
        pal.setColor(QPalette.WindowText, TEXT)
        pal.setColor(QPalette.Text, TEXT)
        self.setPalette(pal)
        # Header.
        title = QLabel(self.tr('QFunnyWidgets'))  # type: QLabel
        title.setObjectName('appTitle')
        sub = QLabel(self.tr('Seriously professional. Professionally unserious.'))  # type: QLabel
        sub.setObjectName('appSub')
        self.status = QLabel(self.tr('Go ahead, poke things.'))  # type: QLabel
        self.status.setObjectName('status')
        header = QHBoxLayout()  # type: QHBoxLayout
        htxt = QVBoxLayout()  # type: QVBoxLayout
        htxt.addWidget(title)
        htxt.addWidget(sub)
        header.addLayout(htxt, 1)
        header.addWidget(self.status, 0, Qt.AlignBottom)
        # Googly eyes.
        eyesCard = Card(title=self.tr('Googly Eyes'), logo='googlyeyes', tag='physics',
                        subtitle=self.tr('Wobbly pupils follow your cursor. Click to poke; poke fast to annoy.'))
        self.eyes = GooglyEyesWidget(eyeCount=2, lidColor='#E9A98F', poked=self.onPoked,
                                     gotAngry=self.onAngry)  # type: GooglyEyesWidget
        eyesCard.body().addWidget(self.eyes)
        # Jelly switches.
        jellyCard = Card(title=self.tr('Jelly Switch'), logo='jellyswitch', tag='toggle',
                         subtitle=self.tr('Sleeps when off, wakes up delighted when on.'))
        row = QHBoxLayout()  # type: QHBoxLayout
        for label, color, checked in ((self.tr('Wi-Fi'), '#34C759', True), (self.tr('Dark mode'), '#5E60CE', False),
                                      (self.tr('Party'), '#FF4D6D', False)):
            col = QVBoxLayout()  # type: QVBoxLayout
            sw = JellySwitchWidget(checked=checked, onColor=color, offColor='#4A4E5E', knobColor='#F7F7FA',
                                   toggled=lambda on, n=label: self.onToggled(n, on))  # type: JellySwitchWidget
            sw.setMinimumSize(96, 64)
            lbl = QLabel(label)  # type: QLabel
            lbl.setObjectName('cardSub')
            lbl.setAlignment(Qt.AlignCenter)
            col.addWidget(sw, 1)
            col.addWidget(lbl)
            row.addLayout(col)
        jellyCard.body().addLayout(row)
        # Mood slider.
        moodCard = Card(title=self.tr('Mood Slider'), logo='moodslider', tag='input',
                        subtitle=self.tr('How do you feel about Mondays? Be honest.'))
        self.mood = MoodSliderWidget(value=35, trackColor=QColor(255, 255, 255, 30),
                                     moodChanged=self.onMood)  # type: MoodSliderWidget
        self.mood.setMinimumHeight(110)
        moodCard.body().addStretch(1)
        moodCard.body().addWidget(self.mood)
        moodCard.body().addStretch(1)
        # Runaway button.
        runCard = Card(title=self.tr('Runaway Button'), logo='runawaybutton', tag='button',
                       subtitle=self.tr('The submit button your users deserve. Gives up after 7 escapes.'))
        self.runner = RunawayButtonWidget(text=self.tr('Submit'), color='#FF4D6D', maxEscapes=7,
                                          caught=self.onCaught)  # type: RunawayButtonWidget
        runCard.body().addWidget(self.runner)
        # Hamster loader.
        hamCard = Card(title=self.tr('Hamster Loader'), logo='hamsterloader', tag='progress',
                       subtitle=self.tr('Renewable-energy progress indicator.'))
        self.hamster = HamsterLoaderWidget(progress=0.0, wheelColor='#6C7186', accentColor='#7B7FFF',
                                           finished=self.onLoaded)  # type: HamsterLoaderWidget
        hamCard.body().addWidget(self.hamster)
        self.__m_progressTimer = QTimer(self)  # type: QTimer
        self.__m_progressTimer.timeout.connect(self._advance)
        self.__m_progressTimer.start(120)
        # Grid.
        grid = QGridLayout()  # type: QGridLayout
        grid.setSpacing(20)
        grid.addWidget(eyesCard, 0, 0)
        grid.addWidget(jellyCard, 0, 1)
        grid.addWidget(moodCard, 0, 2)
        grid.addWidget(runCard, 1, 0, 1, 2)
        grid.addWidget(hamCard, 1, 2)
        grid.setRowStretch(0, 4)
        grid.setRowStretch(1, 5)
        for c in range(3):
            grid.setColumnStretch(c, 1)
        page1 = QWidget()  # type: QWidget
        page1.setLayout(grid)
        grid.setContentsMargins(0, 0, 0, 0)
        # Page 2: the second batch.
        page2 = self._buildSecondPage()  # type: QWidget
        page3 = self._buildThirdPage()  # type: QWidget
        page4 = self._buildFourthPage()  # type: QWidget
        page5 = self._buildFifthPage()  # type: QWidget
        page6 = self._buildSixthPage()  # type: QWidget
        page7 = self._buildSeventhPage()  # type: QWidget
        self.__m_pages = QStackedWidget()  # type: QStackedWidget
        self.__m_pages.addWidget(page1)
        self.__m_pages.addWidget(page2)
        self.__m_pages.addWidget(page3)
        self.__m_pages.addWidget(page4)
        self.__m_pages.addWidget(page5)
        self.__m_pages.addWidget(page6)
        self.__m_pages.addWidget(page7)
        # Navigation pills.
        nav = QHBoxLayout()  # type: QHBoxLayout
        nav.setSpacing(8)
        self.__m_navGroup = QButtonGroup(self)  # type: QButtonGroup
        for i, name in enumerate(
                (self.tr('Classics'), self.tr('New arrivals'), self.tr('Fresh batch'), self.tr('Daily drivers'),
                 self.tr('Power tools'), self.tr('Finishing touches'), self.tr('Little details'))):
            b = QPushButton(name)  # type: QPushButton
            b.setObjectName('nav')
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.setChecked(i == 0)
            self.__m_navGroup.addButton(b, i)
            nav.addWidget(b)
        nav.addStretch(1)
        # Qt 5.15+/6: idClicked(int); older Qt: the buttonClicked[int] overload.
        clickedId = self.__m_navGroup.idClicked if hasattr(self.__m_navGroup, 'idClicked') \
            else self.__m_navGroup.buttonClicked[int]
        clickedId.connect(self.__m_pages.setCurrentIndex)
        root = QWidget()  # type: QWidget
        root.setObjectName('root')
        layout = QVBoxLayout(root)  # type: QVBoxLayout
        layout.setContentsMargins(28, 22, 28, 28)
        layout.setSpacing(16)
        layout.addLayout(header)
        layout.addLayout(nav)
        layout.addWidget(self.__m_pages, 1)
        self.setCentralWidget(root)
        # The pigeon flies over the whole window.
        self.toast = PigeonToast(root, bannerColor='#F7F7FA', pigeonColor='#A9B4C2')  # type: PigeonToast
        # Stylesheets stop palette propagation, so give painted widgets the theme text color directly.
        painted = (self.eyes, self.mood, self.runner, self.hamster, self.stars, self.holdBtn, self.bell,
                   self.duck, self.judge.getFace(), self.typing, self.empty, self.knob, self.deadline,
                   self.battery, self.dropzone, self.pager, self.detective.getFace(), self.robot, self.chameleon,
                   self.gremlin, self.snail, self.pancakes, self.heart, self.dogTabs, self.puffer.getFooter(),
                   self.crumbs, self.squirrel) + tuple(self.avatars) + tuple(self.owls) + tuple(
            self.findChildren(JellySwitchWidget))  # type: tuple
        for wdg in painted:
            wp = wdg.palette()  # type: QPalette
            wp.setColor(QPalette.Text, TEXT)
            wp.setColor(QPalette.WindowText, TEXT)
            wp.setColor(QPalette.Window, QColor('#1C1E26'))
            wdg.setPalette(wp)

    def showPage(self, index):
        """
        :param index: (int) 0 = classics, 1 = new arrivals, 2 = fresh batch, 3 = daily drivers, 4 = power tools,
            5 = finishing touches, 6 = little details
        :return:
        """
        btn = self.__m_navGroup.button(int(index))  # type: QPushButton
        if btn is not None:
            btn.setChecked(True)
        self.__m_pages.setCurrentIndex(int(index))

    def _buildSecondPage(self):
        """
        :return: QWidget
        """
        # Password judge.
        judgeCard = Card(title=self.tr('Password Judge'), logo='passwordjudge', tag='form',
                         subtitle=self.tr('A live password review by a very qualified critic.'))
        self.judge = PasswordJudgeWidget(placeholder=self.tr('Choose a password (he is watching)'),
                                         strengthChanged=self.onStrength)  # type: PasswordJudgeWidget
        judgeCard.body().addWidget(self.judge)
        # Panic bell.
        bellCard = Card(title=self.tr('Panic Bell'), logo='panicbell', tag='badge',
                        subtitle=self.tr('Notifications arrive on their own. Click to clear before it melts down.'))
        self.bell = PanicBellWidget(count=2, color='#FFB703', countChanged=self.onBell)  # type: PanicBellWidget
        bellCard.body().addWidget(self.bell)
        self.__m_bellTimer = QTimer(self)  # type: QTimer
        self.__m_bellTimer.timeout.connect(self._notify)
        self.__m_bellTimer.start(1400)
        # Star rating.
        starCard = Card(title=self.tr('Star Rating'), logo='ratingstars', tag='input',
                        subtitle=self.tr('Every star has feelings. Choose wisely.'))
        self.stars = StarRatingWidget(emptyColor='#4A4E5E', ratingChanged=self.onRated)  # type: StarRatingWidget
        starCard.body().addWidget(self.stars)
        # Nervous hold button.
        holdCard = Card(title=self.tr('Nervous Hold Button'), logo='holdbutton', tag='button',
                        subtitle=self.tr('Hold-to-confirm for destructive actions. It is not ok.'))
        self.holdBtn = NervousHoldButtonWidget(confirmed=self.onDeleted,
                                               cancelled=self.onChickened)  # type: NervousHoldButtonWidget
        holdCard.body().addWidget(self.holdBtn)
        # Rubber duck.
        duckCard = Card(title=self.tr('Rubber Duck'), logo='rubberduck', tag='mascot',
                        subtitle=self.tr('Senior debugging consultant. Click for wisdom.'))
        self.duck = RubberDuckWidget(waterColor='#3A86FF')  # type: RubberDuckWidget
        duckCard.body().addWidget(self.duck)
        grid = QGridLayout()  # type: QGridLayout
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(20)
        grid.addWidget(judgeCard, 0, 0, 1, 2)
        grid.addWidget(bellCard, 0, 2)
        grid.addWidget(starCard, 1, 0)
        grid.addWidget(holdCard, 1, 1)
        grid.addWidget(duckCard, 1, 2)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        for c in range(3):
            grid.setColumnStretch(c, 1)
        page = QWidget()  # type: QWidget
        page.setLayout(grid)
        return page

    def _buildThirdPage(self):
        """
        :return: QWidget
        """
        # Cookie consent.
        cookieCard = Card(title=self.tr('Cookie Consent'), logo='cookieconsent', tag='banner',
                          subtitle=self.tr('GDPR compliant. Emotionally, less so.'))
        self.cookie = CookieConsentWidget(panelColor='#262935', textColor='#ECEDF2', accentColor='#7B7FFF',
                                          autoReset=4500, accepted=self.onCookieAccepted,
                                          declined=self.onCookieDeclined)  # type: CookieConsentWidget
        cookieCard.body().addWidget(self.cookie)
        # Volume knob.
        knobCard = Card(title=self.tr('Volume Knob'), logo='volumeknob', tag='dial',
                        subtitle=self.tr('Drag, scroll or double-click to mute.'))
        self.knob = VolumeKnobWidget(value=55, knobColor='#DADCE5', trackColor=QColor(255, 255, 255, 25),
                                     valueChanged=self.onVolume)  # type: VolumeKnobWidget
        knobCard.body().addWidget(self.knob)
        # Typing indicator in a tiny chat.
        typingCard = Card(title=self.tr('Typing Indicator'), logo='typingindicator', tag='chat',
                          subtitle=self.tr('Shows what they are really doing.'))
        them = QLabel(self.tr('Did you finish the report?'))  # type: QLabel
        them.setObjectName('chatThem')
        me = QLabel(self.tr('Almost! One more tweak.'))  # type: QLabel
        me.setObjectName('chatMe')
        self.typing = TypingIndicatorWidget(name=self.tr('Your manager'), autoCycle=True,
                                            bubbleColor='#2A2D38', dotColor='#9DA0FF')  # type: TypingIndicatorWidget
        self.typing.setMinimumHeight(80)
        typingCard.body().addWidget(them, 0, Qt.AlignLeft)
        typingCard.body().addWidget(me, 0, Qt.AlignRight)
        typingCard.body().addWidget(self.typing)
        typingCard.body().addStretch(1)
        # Empty state.
        emptyCard = Card(title=self.tr('Empty State'), logo='emptystate', tag='placeholder',
                         subtitle=self.tr('For lists that have nothing to say.'))
        self.empty = EmptyStateWidget(title=self.tr('No projects yet'), actionText=self.tr('New project'),
                                      sandColor='#C9A55A', accentColor='#7B7FFF',
                                      actionClicked=self.onEmptyAction)  # type: EmptyStateWidget
        emptyCard.body().addWidget(self.empty)
        # Pigeon toast.
        pigeonCard = Card(title=self.tr('Carrier Pigeon Toast'), logo='pigeontoast', tag='toast',
                          subtitle=self.tr('Notifications, delivered the traditional way. Watch the top-right corner.'))
        send = QPushButton(self.tr('Send a pigeon'))  # type: QPushButton
        send.setObjectName('action')
        send.setCursor(Qt.PointingHandCursor)
        send.clicked.connect(lambda: self.toast.showMessage(choice(PIGEON_MESSAGES)))
        flock = QPushButton(self.tr('Send a flock (3)'))  # type: QPushButton
        flock.setObjectName('ghost')
        flock.setCursor(Qt.PointingHandCursor)
        flock.clicked.connect(self._sendFlock)
        hint = QLabel(self.tr('Messages queue up politely. The pigeon does not.'))  # type: QLabel
        hint.setObjectName('cardSub')
        hint.setWordWrap(True)
        pigeonCard.body().addStretch(1)
        pigeonCard.body().addWidget(send)
        pigeonCard.body().addWidget(flock)
        pigeonCard.body().addWidget(hint)
        pigeonCard.body().addStretch(1)
        grid = QGridLayout()  # type: QGridLayout
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(20)
        grid.addWidget(cookieCard, 0, 0, 1, 2)
        grid.addWidget(knobCard, 0, 2, 2, 1)
        grid.addWidget(typingCard, 1, 0, 2, 1)
        grid.addWidget(emptyCard, 1, 1, 2, 1)
        grid.addWidget(pigeonCard, 2, 2)
        grid.setRowStretch(0, 4)
        grid.setRowStretch(1, 3)
        grid.setRowStretch(2, 3)
        for c in range(3):
            grid.setColumnStretch(c, 1)
        page = QWidget()  # type: QWidget
        page.setLayout(grid)
        return page

    def _buildFourthPage(self):
        """
        :return: QWidget
        """
        # Deadline.
        deadlineCard = Card(title=self.tr('Deadline Countdown'), logo='deadline', tag='timer',
                            subtitle=self.tr('A 45 second deadline, on loop. Relatable.'))
        self.deadline = DeadlineCountdownWidget(duration=45, title=self.tr('Quarterly report due'),
                                                expired=self.onDeadline)  # type: DeadlineCountdownWidget
        extend = QPushButton(self.tr('Ask for an extension (+20 s)'))  # type: QPushButton
        extend.setObjectName('ghost')
        extend.setCursor(Qt.PointingHandCursor)
        extend.clicked.connect(lambda: self.deadline.extend(20))
        deadlineCard.body().addWidget(self.deadline, 1)
        deadlineCard.body().addWidget(extend, 0, Qt.AlignRight)
        # Battery.
        batteryCard = Card(title=self.tr('Battery Buddy'), logo='batterybuddy', tag='status',
                           subtitle=self.tr('Drains, complains, recharges. Like us.'))
        self.battery = BatteryBuddyWidget(level=100, caseColor='#8B8FA3',
                                          lowBattery=self.onLowBattery)  # type: BatteryBuddyWidget
        batteryCard.body().addWidget(self.battery)
        self.__m_batteryTimer = QTimer(self)  # type: QTimer
        self.__m_batteryTimer.timeout.connect(self._batteryStep)
        self.__m_batteryTimer.start(220)
        # Drop zone.
        dropCard = Card(title=self.tr('Drop Zone Monster'), logo='dropzone', tag='upload',
                        subtitle=self.tr('Drag files from your desktop. He eats images, PDFs and text.'))
        self.dropzone = DropZoneMonsterWidget(acceptedExtensions=['png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'md'],
                                              accentColor='#7B7FFF',
                                              filesDropped=self.onFilesEaten)  # type: DropZoneMonsterWidget
        dropCard.body().addWidget(self.dropzone)
        # Presence avatars.
        teamCard = Card(title=self.tr('Presence Avatars'), logo='presenceavatar', tag='identity',
                        subtitle=self.tr('Hover to say hi. Click to change their status.'))
        team = QGridLayout()  # type: QGridLayout
        self.avatars = []  # type: list[PresenceAvatarWidget]
        for i, (name, st) in enumerate((('Ada Lovelace', PresenceAvatarWidget.Online),
                                        ('Alan Turing', PresenceAvatarWidget.Away),
                                        ('Grace Hopper', PresenceAvatarWidget.Busy),
                                        ('Charles Babbage', PresenceAvatarWidget.Offline))):
            av = PresenceAvatarWidget(name=name, status=st, badgeBorderColor='#1C1E26')  # type: PresenceAvatarWidget
            av.clicked.connect(lambda a=av: a.setStatus((int(a.getStatus()) + 1) % 4))
            self.avatars.append(av)
            lbl = QLabel(name)  # type: QLabel
            lbl.setObjectName('avatarName')
            lbl.setAlignment(Qt.AlignCenter)
            team.addWidget(av, (i // 2) * 2, i % 2)
            team.addWidget(lbl, (i // 2) * 2 + 1, i % 2)
        teamCard.body().addLayout(team)
        # Duckling pager with an onboarding carousel.
        pagerCard = Card(title=self.tr('Duckling Pager'), logo='ducklingpager', tag='navigation',
                         subtitle=self.tr('Carousel dots, but make it ducks. Click a lily pad.'))
        slides = QStackedWidget()  # type: QStackedWidget
        for text in (self.tr('Welcome aboard'), self.tr('Meet your dashboard'), self.tr('Invite your team'),
                     self.tr('Set your goals'), self.tr('You are ready!')):
            sl = QLabel(text)  # type: QLabel
            sl.setObjectName('slide')
            sl.setAlignment(Qt.AlignCenter)
            slides.addWidget(sl)
        self.pager = DucklingPagerWidget(count=5, ducklings=3, padColor='#4FA36A',
                                         currentChanged=slides.setCurrentIndex)  # type: DucklingPagerWidget
        self.pager.setMinimumHeight(80)
        pagerCard.body().addWidget(slides, 1)
        pagerCard.body().addWidget(self.pager)
        self.__m_pagerTimer = QTimer(self)  # type: QTimer
        self.__m_pagerTimer.timeout.connect(self.pager.next)
        self.__m_pagerTimer.start(3200)
        grid = QGridLayout()  # type: QGridLayout
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(20)
        grid.addWidget(deadlineCard, 0, 0, 1, 2)
        grid.addWidget(batteryCard, 0, 2)
        grid.addWidget(dropCard, 1, 0)
        grid.addWidget(teamCard, 1, 1)
        grid.addWidget(pagerCard, 1, 2)
        grid.setRowStretch(0, 2)
        grid.setRowStretch(1, 3)
        for c in range(3):
            grid.setColumnStretch(c, 1)
        page = QWidget()  # type: QWidget
        page.setLayout(grid)
        return page

    def _buildFifthPage(self):
        """
        :return: QWidget
        """
        # Search detective.
        searchCard = Card(title=self.tr('Search Detective'), logo='searchdetective', tag='search',
                          subtitle=self.tr('Try "report", "cat" or "xyz".'))
        self.detective = SearchDetectiveWidget(placeholder=self.tr('Search files...'),
                                               searchFunction=self._findFiles)  # type: SearchDetectiveWidget
        searchCard.body().addWidget(self.detective)
        # Robot check.
        robotCard = Card(title=self.tr('Robot Check'), logo='robotcheck', tag='verify',
                         subtitle=self.tr('Human verification, administered by a robot.'))
        self.robot = RobotCheckWidget(panelColor='#262935', textColor='#ECEDF2', failChance=0.25,
                                      verified=lambda: self.status.setText(self.tr('Verified human. Allegedly.')),
                                      failed=lambda: self.status.setText(
                                          self.tr('Flagged as a robot. Beep boop.')))  # type: RobotCheckWidget
        again = QPushButton(self.tr('Reset'))  # type: QPushButton
        again.setObjectName('ghost')
        again.setCursor(Qt.PointingHandCursor)
        again.clicked.connect(self.robot.reset)
        robotCard.body().addWidget(self.robot, 1)
        robotCard.body().addWidget(again, 0, Qt.AlignRight)
        # Chameleon color picker: it also recolors the navigation pills.
        chamCard = Card(title=self.tr('Chameleon Picker'), logo='chameleonpicker', tag='color',
                        subtitle=self.tr('Pick a color. It also themes the tabs up there.'))
        self.chameleon = ChameleonColorPickerWidget(color='#7B7FFF', branchColor='#7A5232',
                                                    colors=['#E63946', '#FF9F1C', '#FFD23F', '#9BDB4D', '#3BCEAC',
                                                            '#4CC9F0', '#4361EE', '#7B7FFF', '#C77DFF', '#FF70A6',
                                                            '#8D6E63', '#6C757D'],
                                                    colorChanged=self._themeTabs)  # type: ChameleonColorPickerWidget
        chamCard.body().addWidget(self.chameleon)
        # Error gremlin.
        gremCard = Card(title=self.tr('Error Gremlin'), logo='errorgremlin', tag='alert',
                        subtitle=self.tr(
                            'Inline alerts with a culprit. Retry scares it off; pick a severity to bring it back.'))
        self.gremlin = ErrorGremlinWidget(severity=ErrorGremlinWidget.Error, panelColor='#262935', textColor='#ECEDF2',
                                          title=self.tr('Connection lost'),
                                          message=self.tr(
                                              'We could not reach the server. Someone appears to be chewing the cable.'
                                          ),
                                          retryClicked=self._onRetry,
                                          dismissed=lambda: self.status.setText(
                                              self.tr('Alert dismissed. The gremlin is still out there.'))
                                          )  # type: ErrorGremlinWidget
        self.gremlin.setMinimumHeight(110)
        sevRow = QHBoxLayout()  # type: QHBoxLayout
        alerts = ((ErrorGremlinWidget.Info, self.tr('Info'), self.tr('Heads up'),
                   self.tr('Scheduled maintenance tonight at 2 am. The gremlin is resting up for it.')),
                  (ErrorGremlinWidget.Warning, self.tr('Warning'), self.tr('Disk almost full'),
                   self.tr('Only 3% space left. Something is hoarding cat pictures.')),
                  (ErrorGremlinWidget.Error, self.tr('Error'), self.tr('Connection lost'),
                   self.tr('We could not reach the server. Someone appears to be chewing the cable.')),
                  (ErrorGremlinWidget.Critical, self.tr('Critical'), self.tr('Production is on fire'),
                   self.tr('Literally. Please do not panic. Panic quietly.')))
        for sev, label, title, msg in alerts:
            b = QPushButton(label)  # type: QPushButton
            b.setObjectName('ghost')
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, a=(sev, title, msg): self.gremlin.showAlert(*a))
            sevRow.addWidget(b)
        gremCard.body().addWidget(self.gremlin)
        gremCard.body().addStretch(1)
        gremCard.body().addLayout(sevRow)
        # Snail stepper.
        snailCard = Card(title=self.tr('Snail Stepper'), logo='snailstepper', tag='wizard',
                         subtitle=self.tr('Checkout progress at a sustainable pace.'))
        self.snail = SnailStepperWidget(
            steps=[self.tr('Cart'), self.tr('Shipping'), self.tr('Payment'), self.tr('Done')],
            arrived=lambda i: self.status.setText(
                self.tr('The snail reached step {}.').format(i + 1)))  # type: SnailStepperWidget
        nav = QHBoxLayout()  # type: QHBoxLayout
        back = QPushButton(self.tr('Back'))  # type: QPushButton
        back.setObjectName('ghost')
        back.clicked.connect(self.snail.previous)
        nxt = QPushButton(self.tr('Next'))  # type: QPushButton
        nxt.setObjectName('action')
        nxt.clicked.connect(self.snail.next)
        for b in (back, nxt):
            b.setCursor(Qt.PointingHandCursor)
        nav.addWidget(back)
        nav.addStretch(1)
        nav.addWidget(nxt)
        snailCard.body().addWidget(self.snail, 1)
        snailCard.body().addLayout(nav)
        grid = QGridLayout()  # type: QGridLayout
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(20)
        grid.addWidget(searchCard, 0, 0)
        grid.addWidget(robotCard, 0, 1)
        grid.addWidget(chamCard, 0, 2)
        grid.addWidget(gremCard, 1, 0, 1, 2)
        grid.addWidget(snailCard, 1, 2)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        for c in range(3):
            grid.setColumnStretch(c, 1)
        page = QWidget()  # type: QWidget
        page.setLayout(grid)
        return page

    def _buildSixthPage(self):
        """
        :return: QWidget
        """
        # Pancakes.
        panCard = Card(title=self.tr('Pancake Stepper'), logo='pancakestepper', tag='quantity',
                       subtitle=self.tr('A spin box, served warm. Wheel, arrows or +/-.'))
        self.pancakes = PancakeStepperWidget(value=3, maximum=8, accentColor='#C47F3A',
                                             valueChanged=lambda v: self.status.setText(
                                                 self.tr('Order: {} pancake(s). ${:.2f}').format(v, v * 2.5))
                                             )  # type: PancakeStepperWidget
        panCard.body().addWidget(self.pancakes)
        # Heart like.
        heartCard = Card(title=self.tr('Heart Like Button'), logo='heartlike', tag='social',
                         subtitle=self.tr('Liking is caring. Un-liking leaves a mark.'))
        post = QLabel(self.tr(
            'Just shipped a new feature on a Friday afternoon. What could possibly go wrong?'))  # type: QLabel
        post.setObjectName('post')
        post.setWordWrap(True)
        self.heart = HeartLikeButtonWidget(count=41, color='#FF4D6D')  # type: HeartLikeButtonWidget
        heartCard.body().addWidget(post)
        heartCard.body().addWidget(self.heart, 1)
        # Copy blobs.
        copyCard = Card(title=self.tr('Copy Blob'), logo='copyblob', tag='clipboard',
                        subtitle=self.tr('Click a chip. The blob copies itself (and your text).'))
        copyCard.body().addStretch(1)
        for text, label, prompt, color in (('pip install funnywidgets', '', '$', '#9BDB4D'),
                                           ('sk-live-8f3a9c2e7b1d4f60', 'sk-live-****************', '', '#FF9F1C')):
            chip = CopyBlobButtonWidget(text=text, label=label, prompt=prompt, blobColor=color, chipColor='#14151B',
                                        copied=lambda t: self.status.setText(
                                            self.tr('Copied to clipboard ({} chars).').format(
                                                len(t))))  # type: CopyBlobButtonWidget
            chip.setMinimumHeight(84)
            copyCard.body().addWidget(chip)
        copyCard.body().addStretch(1)
        # Cat sections.
        catCard = Card(title=self.tr('Sleepy Cat Sections'), logo='catsection', tag='container',
                       subtitle=self.tr('Collapsible panels. Please do not wake the cat. (Wake the cat.)'))
        adv = QLabel(
            self.tr('Turbo mode: ON    Cache size: 1 tuna can\nTelemetry: off (the cat insisted)'))  # type: QLabel
        adv.setObjectName('sectionText')
        notes = QLabel(self.tr('v6.0: Added pancakes, hearts, blobs, rockets and cats.\n'
                               'Removed: one bug (it was a feature).'))  # type: QLabel
        notes.setObjectName('sectionText')
        notes.setWordWrap(True)
        self.catSections = [SleepyCatSectionWidget(title=self.tr('Advanced settings'), content=adv, barColor='#262935',
                                                   textColor='#ECEDF2', catColor='#F4A261'),
                            SleepyCatSectionWidget(
                                title=self.tr('Release notes'), content=notes, barColor='#262935',
                                textColor='#ECEDF2', catColor='#8D99AE', expanded=True)]  # type: list
        for sec in self.catSections:
            catCard.body().addWidget(sec)
            # Accordion behavior: opening one section puts the other cat to sleep.
            sec.toggled.connect(
                lambda on, me=sec: [o.setExpanded(False) for o in self.catSections if on and o is not me])
        catCard.body().addStretch(1)
        # Rocket back-to-top over a long changelog.
        rocketCard = Card(title=self.tr('Rocket Back-to-Top'), logo='rockettop', tag='navigation',
                          subtitle=self.tr('Scroll down. Then press the rocket.'))
        log = QLabel('\n\n'.join(self.tr(
            'Release {}.0: Fixed a bug where the previous fix introduced a bug. Also made the rocket faster.'
        ).format(40 - i) for i in range(40)))  # type: QLabel
        log.setObjectName('changelog')
        log.setWordWrap(True)
        log.setAlignment(Qt.AlignTop)
        log.setContentsMargins(4, 4, 90, 4)
        feed = QScrollArea()  # type: QScrollArea
        feed.setObjectName('feed')
        feed.setWidgetResizable(True)
        feed.setWidget(log)
        feed.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.rocket = RocketBackToTop(feed, threshold=200, color='#7B7FFF',
                                      launched=lambda: self.status.setText(
                                          self.tr('Houston, we have scrolled.')))  # type: RocketBackToTop
        rocketCard.body().addWidget(feed, 1)
        grid = QGridLayout()  # type: QGridLayout
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(20)
        grid.addWidget(panCard, 0, 0)
        grid.addWidget(heartCard, 0, 1)
        grid.addWidget(copyCard, 0, 2)
        grid.addWidget(catCard, 1, 0, 1, 2)
        grid.addWidget(rocketCard, 1, 2)
        grid.setRowStretch(0, 2)
        grid.setRowStretch(1, 3)  # room for the sections to expand
        for c in range(3):
            grid.setColumnStretch(c, 1)
        page = QWidget()  # type: QWidget
        page.setLayout(grid)
        return page

    def _buildSeventhPage(self):
        """
        :return: QWidget
        """
        # Dachshund tabs over a little stack of pages.
        tabsCard = Card(title=self.tr('Dachshund Tabs'), logo='dachshundtabs', tag='tabs',
                        subtitle=self.tr('Segmented control. Jump from the first tab to the last.'))
        names = [self.tr('Overview'), self.tr('Activity'), self.tr('Settings'), self.tr('Billing'), self.tr('Help')]
        pages = QStackedWidget()  # type: QStackedWidget
        for text in (self.tr('All systems nominal. The dog is a good boy.'),
                     self.tr('3 new events. All of them were the dog.'),
                     self.tr('Settings: everything set to "very good boy".'),
                     self.tr('Invoice: 1 treat. Paid in full.'),
                     self.tr('Help: have you tried belly rubs?')):
            lbl = QLabel(text)  # type: QLabel
            lbl.setObjectName('tabPage')
            lbl.setAlignment(Qt.AlignCenter)
            pages.addWidget(lbl)
        self.dogTabs = DachshundTabsWidget(tabs=names, dogColor='#B5651D', trackColor=QColor(255, 255, 255, 18),
                                           currentChanged=pages.setCurrentIndex)  # type: DachshundTabsWidget
        tabsCard.body().addWidget(self.dogTabs)
        tabsCard.body().addWidget(pages, 1)
        # Help owls on a small form.
        owlCard = Card(title=self.tr('Help Owl'), logo='helpowl', tag='tooltip',
                       subtitle=self.tr('Hover the owls for help. Click to pin.'))
        form = QGridLayout()  # type: QGridLayout
        self.owls = []  # type: list[HelpOwlWidget]
        for r, (label, ph, help_) in enumerate(((self.tr('Workspace'), 'acme-corp',
                                                 self.tr(
                                                     'The name your whole team sees. Choose wisely; the owl is judging.'
                                                 )),
                                                (self.tr('Retention'), '30 days',
                                                 self.tr(
                                                     'How long deleted items are kept. After that, the owl eats them.')
                                                 ),
                                                (self.tr('Webhook'), 'https://...',
                                                 self.tr('We POST JSON here whenever something happens. Hoo!')))):
            lbl = QLabel(label)  # type: QLabel
            lbl.setObjectName('formLabel')
            edit = QLineEdit()  # type: QLineEdit
            edit.setPlaceholderText(ph)
            owl = HelpOwlWidget(helpText=help_, title=label, owlColor='#A1887F')  # type: HelpOwlWidget
            owl.setFixedSize(34, 40)
            self.owls.append(owl)
            form.addWidget(lbl, r, 0)
            form.addWidget(edit, r, 1)
            form.addWidget(owl, r, 2)
        owlCard.body().addLayout(form)
        owlCard.body().addStretch(1)
        # Breadcrumb with "folders" to dive into.
        crumbCard = Card(title=self.tr('Ant Breadcrumb'), logo='antbreadcrumb', tag='navigation',
                         subtitle=self.tr('Open folders below; click a crumb to go back up.'))
        tree = {'Home': ['Projects', 'Photos'], 'Projects': ['QFunnyWidgets', 'Secret plan'],
                'QFunnyWidgets': ['src', 'docs'], 'Photos': ['Cats', 'More cats'], 'src': ['ants.py']}  # type: dict
        self.crumbs = AntBreadcrumbWidget(path=['Home', 'Projects'], antColor='#D8C3A5')  # type: AntBreadcrumbWidget
        folders = QHBoxLayout()  # type: QHBoxLayout
        crumbCard.body().addWidget(self.crumbs)
        crumbCard.body().addStretch(1)
        crumbCard.body().addLayout(folders)

        def refresh(path):
            """
            Rebuild the folder buttons for the current crumb.

            :param path: list[str]
            :return:
            """
            while folders.count():
                item = folders.takeAt(0)
                if item.widget() is not None:
                    item.widget().deleteLater()
            for name in tree.get(path[-1], []):
                b = QPushButton(self.tr('Open {}').format(name))  # type: QPushButton
                b.setObjectName('ghost')
                b.setCursor(Qt.PointingHandCursor)
                b.clicked.connect(lambda _=False, n=name: self.crumbs.push(n))
                folders.addWidget(b)
            if not tree.get(path[-1]):
                lbl = QLabel(self.tr('Empty folder. Just ants.'))  # type: QLabel
                lbl.setObjectName('formLabel')
                folders.addWidget(lbl)

        self.crumbs.pathChanged.connect(refresh)
        refresh(self.crumbs.getPath())
        # Puffer counter.
        pufferCard = Card(title=self.tr('Puffer Counter'), logo='puffercounter', tag='input',
                          subtitle=self.tr('A 100-character limit, enforced by a fish.'))
        self.puffer = PufferCounterWidget(maxLength=100, placeholder=self.tr("What's happening? (keep it short)"),
                                          limitExceeded=lambda o: self.status.setText(
                                              self.tr('Too long! The fish is furious.') if o else self.tr(
                                                  'Back under the limit.')))  # type: PufferCounterWidget
        pufferCard.body().addWidget(self.puffer)
        # Autosave squirrel.
        saveCard = Card(title=self.tr('Autosave Squirrel'), logo='autosave', tag='status',
                        subtitle=self.tr('Type, then pause. 20% of saves fail on purpose.'))
        notes = QPlainTextEdit()  # type: QPlainTextEdit
        notes.setPlaceholderText(self.tr('Your notes...'))
        self.squirrel = AutosaveSquirrelWidget(autosaveDelay=1200, retryDelay=2500)  # type: AutosaveSquirrelWidget
        self.squirrel.saveRequested.connect(
            lambda: QTimer.singleShot(1300, lambda: self.squirrel.saveFinished(random() > 0.2)))
        notes.textChanged.connect(self.squirrel.markDirty)
        saveCard.body().addWidget(notes, 1)
        saveCard.body().addWidget(self.squirrel)
        grid = QGridLayout()  # type: QGridLayout
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(20)
        grid.addWidget(tabsCard, 0, 0, 1, 2)
        grid.addWidget(owlCard, 0, 2)
        grid.addWidget(crumbCard, 1, 0)
        grid.addWidget(pufferCard, 1, 1)
        grid.addWidget(saveCard, 1, 2)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        for c in range(3):
            grid.setColumnStretch(c, 1)
        page = QWidget()  # type: QWidget
        page.setLayout(grid)
        return page

    def _findFiles(self, text):
        """
        :param text: str | unicode | QString
        :return: (int) Number of matching fake files.
        """
        files = ['quarterly_report_final.pdf', 'quarterly_report_final_v2.pdf', 'report_FINAL_really.docx',
                 'cat_photo_001.jpg', 'cat_photo_002.jpg', 'catalogue.xlsx', 'budget.xlsx', 'notes.txt'
                 ]  # type: list[str]
        n = len([f for f in files if text.lower() in f.lower()])  # type: int
        self.status.setText(self.tr('Search for "{}": {} result(s)').format(text, n))
        return n

    def _themeTabs(self, color):
        """
        Let the chameleon recolor the active navigation pill.

        :param color: QColor
        :return:
        """
        css = 'QPushButton#nav:checked {{ background: {0}; border-color: {0}; }}'.format(color.name())  # type: str
        for b in self.__m_navGroup.buttons():
            b.setStyleSheet(css)

    @pyqtSlot()
    def _onRetry(self):
        """
        :return:
        """
        self.status.setText(self.tr('Retrying...'))
        QTimer.singleShot(1700, lambda: self.gremlin.showAlert(
            ErrorGremlinWidget.Info, self.tr('Fixed! (for now)'), self.tr(
                'The gremlin has been relocated to a nice farm upstate.')))

    @pyqtSlot()
    def _batteryStep(self):
        """
        Simulated battery: drain to almost nothing, then charge back up.
        :return:
        """
        lv = self.battery.getLevel()  # type: int
        if self.battery.isCharging():
            if lv >= 100:
                self.battery.setCharging(False)
            else:
                self.battery.setLevel(lv + 2)
        elif lv <= 2:
            self.battery.setCharging(True)
        else:
            self.battery.setLevel(lv - 1)

    @pyqtSlot()
    def onLowBattery(self):
        """
        :return:
        """
        self.status.setText(self.tr('Battery low. It is being very dramatic about it.'))

    @pyqtSlot()
    def onDeadline(self):
        """
        :return:
        """
        self.status.setText(self.tr('Deadline missed. This is fine.'))
        QTimer.singleShot(7000, self.deadline.start)

    @pyqtSlot(list)
    def onFilesEaten(self, paths):
        """
        :param paths: list[str | unicode | QString]
        :return:
        """
        self.toast.showMessage(self.tr('The monster ate {} file(s). He says thanks.').format(len(paths)))

    @pyqtSlot()
    def _sendFlock(self):
        """
        :return:
        """
        for _ in range(3):
            self.toast.showMessage(choice(PIGEON_MESSAGES), 1400)

    @pyqtSlot()
    def onCookieAccepted(self):
        """
        :return:
        """
        self.status.setText(self.tr('Cookies accepted. The cookie was delicious.'))

    @pyqtSlot()
    def onCookieDeclined(self):
        """
        :return:
        """
        self.status.setText(self.tr('Cookies declined. Somewhere, a cookie weeps.'))

    @pyqtSlot(int)
    def onVolume(self, value):
        """
        :param value: int
        :return:
        """
        self.status.setText(self.tr('Volume {}%').format(value))

    @pyqtSlot()
    def onEmptyAction(self):
        """
        :return:
        """
        self.toast.showMessage(self.tr('Project created! (Not really. This is a demo.)'))

    @pyqtSlot()
    def _notify(self):
        """
        Simulated incoming notifications for the bell (they speed up, like real life).
        :return: None
        """
        n = self.bell.getCount()  # type: int
        self.bell.setCount(n + (1 if n < 8 else 3 if n < 30 else 12))

    @pyqtSlot(int)
    def onStrength(self, strength):
        """
        :param strength: int
        :return:
        """
        names = ['', 'terrible', 'weak', 'fair', 'good', 'strong']  # type: list[str]
        if strength >= 0:
            self.status.setText(self.tr('Password strength: {}').format(names[strength + 1]))

    @pyqtSlot(int)
    def onBell(self, count):
        """
        :param count: int
        :return:
        """
        if count == 0:
            self.status.setText(self.tr('Inbox zero. The bell can finally sleep.'))

    @pyqtSlot(int)
    def onRated(self, rating):
        """
        :param rating: int
        :return:
        """
        self.status.setText(self.tr('Rated {} star(s). The stars have been informed.').format(rating))

    @pyqtSlot()
    def onDeleted(self):
        """
        :return:
        """
        self.status.setText(self.tr('Deleted. The button needs a moment.'))

    @pyqtSlot('qreal')
    @pyqtSlot(float)
    def onChickened(self, progress):
        """
        :param progress: qreal | float | int
        :return:
        """
        self.status.setText(self.tr('Backed out at {}%. Wise.').format(int(progress * 100)))

    @pyqtSlot()
    def _advance(self):
        """
        Fake background work for the hamster; restarts a while after finishing.
        :return: None
        """
        p = self.hamster.getProgress()  # type: float
        if p >= 1.0:
            return
        self.hamster.setProgress(min(1.0, p + 0.012))

    @pyqtSlot()
    def onLoaded(self):
        """
        :return:
        """
        self.status.setText(self.tr('Loading complete. Hamster requests a snack.'))
        QTimer.singleShot(3500, self.hamster.reset)

    @pyqtSlot(int)
    def onPoked(self, count):
        """
        :param count: int
        :return:
        """
        self.status.setText(self.tr('Poke #{}. Rude.').format(count))

    @pyqtSlot()
    def onAngry(self):
        """
        :return:
        """
        self.status.setText(self.tr('The eyes are now angry. Happy?'))

    def onToggled(self, name, on):
        """
        :param name: str | unicode | QString
        :param on: bool
        :return:
        """
        self.status.setText(self.tr('{} is {}').format(name, self.tr('awake') if on else self.tr('asleep')))

    @pyqtSlot('QString')
    def onMood(self, mood):
        """
        :param mood: str | unicode | QString
        :return:
        """
        self.status.setText(self.tr('Current mood: {}').format(mood))

    @pyqtSlot(int)
    def onCaught(self, escapes):
        """
        :param escapes: int
        :return:
        """
        self.status.setText(self.tr('Submitted after only {} escapes. Impressive.').format(escapes))
