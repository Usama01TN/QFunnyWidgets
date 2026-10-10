# -*- coding: utf-8 -*-
"""
Shared data for the Qt Designer plugins: one WidgetInfo per widget plus helpers that pick the Qt binding
of the hosting Designer and make the QFunnyWidgets package importable from a source checkout.
Deliberately free of plugin classes, so neither Designer loader registers anything from this file.
"""
from os.path import dirname, abspath, join
from sys import modules, path, stderr
from os import environ

GROUP_INPUTS = 'QFunnyWidgets: Inputs'  # type: str
GROUP_BUTTONS = 'QFunnyWidgets: Buttons'  # type: str
GROUP_NAVIGATION = 'QFunnyWidgets: Navigation'  # type: str
GROUP_FEEDBACK = 'QFunnyWidgets: Feedback'  # type: str
GROUP_HELPERS = 'QFunnyWidgets: Containers & helpers'  # type: str
GROUP_MASCOTS = 'QFunnyWidgets: Mascots'  # type: str
# Qt binding modules a Designer can host, mapped to ManyQt's QT_API values (Qt 6 first).
HOSTS = (('PyQt6', 'pyqt6'), ('PyQt5', 'pyqt5'), ('PyQt4', 'pyqt4'),
         ('PySide6', 'pyside6'), ('PySide2', 'pyside2'), ('PySide', 'pyside'))  # type: tuple


class WidgetInfo(object):
    """
    Everything Designer needs to know about one widget.
    """

    def __init__(self, className='', package='', title='', group='', toolTip='', width=200, height=100):
        """
        :param className: (str | unicode | QString) e.g. 'GooglyEyesWidget'
        :param package: (str | unicode | QString) sub-package of QFunnyWidgets, e.g. 'googlyeyes'
        :param title: (str | unicode | QString) human-readable name shown in Designer's widget box
        :param group: (str | unicode | QString) widget box group
        :param toolTip: (str | unicode | QString) one-line description
        :param width: (int) default width on the form
        :param height: (int) default height on the form
        """
        self.className = className  # type: str
        self.package = package  # type: str
        self.title = title  # type: str
        self.group = group  # type: str
        self.toolTip = toolTip  # type: str
        self.width = int(width)  # type: int
        self.height = int(height)  # type: int

    def module(self):
        """
        :return: (str | unicode | QString) Import path used by uic: "from <module> import <className>".
        """
        return 'QFunnyWidgets.{}'.format(self.package)

    def objectName(self):
        """
        :return: (str | unicode | QString) Default object name on a form, e.g. 'googlyEyes'.
        """
        base = self.className[:-6] if self.className.endswith('Widget') else self.className  # type: str
        return base[0].lower() + base[1:]

    def domXml(self):
        """
        :return: (str | unicode | QString) Designer DOM XML for a freshly dropped instance.
        """
        tip = self.toolTip.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')  # type: str
        return ('<ui language="c++" displayname="{title}">\n'
                ' <widget class="{cls}" name="{name}">\n'
                '  <property name="geometry">\n'
                '   <rect><x>0</x><y>0</y><width>{w}</width><height>{h}</height></rect>\n'
                '  </property>\n'
                '  <property name="toolTip"><string>{tip}</string></property>\n'
                ' </widget>\n'
                '</ui>\n').format(title=self.title, cls=self.className, name=self.objectName(),
                                  w=self.width, h=self.height, tip=tip)


# 33 widgets; PigeonToast and RocketBackToTop are runtime overlays (they attach to a parent or a scroll
# area at construction), so they are created in code rather than placed in Designer.
WIDGETS = [
    WidgetInfo('JellySwitchWidget', 'jellyswitch', 'Jelly Switch', GROUP_INPUTS,
               'Toggle switch with a jelly knob that sleeps when off.', 130, 70),
    WidgetInfo('MoodSliderWidget', 'moodslider', 'Mood Slider', GROUP_INPUTS,
               'Slider whose thumb is a face from furious to ecstatic.', 340, 110),
    WidgetInfo('StarRatingWidget', 'ratingstars', 'Star Rating', GROUP_INPUTS,
               'Star rating where every star has feelings.', 320, 110),
    WidgetInfo('VolumeKnobWidget', 'volumeknob', 'Volume Knob', GROUP_INPUTS,
               'Rotary dial that goes from zipped mouth to screaming.', 240, 260),
    WidgetInfo('PasswordJudgeWidget', 'passwordjudge', 'Password Judge', GROUP_INPUTS,
               'Password field reviewed live by a powdered-wig judge.', 400, 194),
    WidgetInfo('SearchDetectiveWidget', 'searchdetective', 'Search Detective', GROUP_INPUTS,
               'Debounced search field with an investigating detective.', 400, 184),
    WidgetInfo('ChameleonColorPickerWidget', 'chameleonpicker', 'Chameleon Color Picker', GROUP_INPUTS,
               'Swatch color picker; the chameleon eats the color you pick.', 460, 220),
    WidgetInfo('PancakeStepperWidget', 'pancakestepper', 'Pancake Stepper', GROUP_INPUTS,
               'Quantity spin box served as a stack of pancakes.', 260, 280),
    WidgetInfo('PufferCounterWidget', 'puffercounter', 'Puffer Counter', GROUP_INPUTS,
               'Text area with a character limit and an inflating pufferfish.', 360, 262),
    WidgetInfo('RunawayButtonWidget', 'runawaybutton', 'Runaway Button', GROUP_BUTTONS,
               'A button that dodges the cursor until it gets tired.', 460, 260),
    WidgetInfo('NervousHoldButtonWidget', 'holdbutton', 'Nervous Hold Button', GROUP_BUTTONS,
               'Hold-to-confirm button that panics, then faints.', 320, 110),
    WidgetInfo('HeartLikeButtonWidget', 'heartlike', 'Heart Like Button', GROUP_BUTTONS,
               'Like button that pops when liked and cracks when un-liked.', 200, 120),
    WidgetInfo('CopyBlobButtonWidget', 'copyblob', 'Copy Blob Button', GROUP_BUTTONS,
               'Copy-to-clipboard chip whose blob clones itself.', 340, 110),
    WidgetInfo('RobotCheckWidget', 'robotcheck', 'Robot Check', GROUP_BUTTONS,
               '"I am not a robot" box with a nervous robot behind it.', 360, 190),
    WidgetInfo('DucklingPagerWidget', 'ducklingpager', 'Duckling Pager', GROUP_NAVIGATION,
               'Carousel page indicator: a duck family on lily pads.', 360, 100),
    WidgetInfo('SnailStepperWidget', 'snailstepper', 'Snail Stepper', GROUP_NAVIGATION,
               'Wizard step indicator carried by a slow snail.', 520, 130),
    WidgetInfo('DachshundTabsWidget', 'dachshundtabs', 'Dachshund Tabs', GROUP_NAVIGATION,
               'Segmented control whose highlight is a stretchy dachshund.', 480, 64),
    WidgetInfo('AntBreadcrumbWidget', 'antbreadcrumb', 'Ant Breadcrumb', GROUP_NAVIGATION,
               'Breadcrumb trail of bread crumbs carried by ants.', 420, 56),
    WidgetInfo('HamsterLoaderWidget', 'hamsterloader', 'Hamster Loader', GROUP_FEEDBACK,
               'Progress indicator powered by a hamster wheel.', 300, 260),
    WidgetInfo('PanicBellWidget', 'panicbell', 'Panic Bell', GROUP_FEEDBACK,
               'Notification bell that panics as the count grows.', 180, 180),
    WidgetInfo('TypingIndicatorWidget', 'typingindicator', 'Typing Indicator', GROUP_FEEDBACK,
               'Chat typing dots that type, think, delete or sleep.', 260, 90),
    WidgetInfo('BatteryBuddyWidget', 'batterybuddy', 'Battery Buddy', GROUP_FEEDBACK,
               'Battery status with moods from energized to empty.', 280, 200),
    WidgetInfo('DeadlineCountdownWidget', 'deadline', 'Deadline Countdown', GROUP_FEEDBACK,
               'Countdown with a calendar that ends up "fine" in flames.', 440, 170),
    WidgetInfo('AutosaveSquirrelWidget', 'autosave', 'Autosave Squirrel', GROUP_FEEDBACK,
               'Autosave status run by an acorn-stashing squirrel.', 300, 76),
    WidgetInfo('ErrorGremlinWidget', 'errorgremlin', 'Error Gremlin', GROUP_FEEDBACK,
               'Inline alert banner with a severity-matched gremlin.', 520, 110),
    WidgetInfo('CookieConsentWidget', 'cookieconsent', 'Cookie Consent', GROUP_FEEDBACK,
               'Cookie banner starring an emotionally invested cookie.', 520, 160),
    WidgetInfo('EmptyStateWidget', 'emptystate', 'Empty State', GROUP_FEEDBACK,
               '"Nothing here yet" placeholder with a rolling tumbleweed.', 420, 300),
    WidgetInfo('SleepyCatSectionWidget', 'catsection', 'Sleepy Cat Section', GROUP_HELPERS,
               'Collapsible section with a cat napping on its header.', 360, 82),
    WidgetInfo('HelpOwlWidget', 'helpowl', 'Help Owl', GROUP_HELPERS,
               'Inline help icon: an owl that wakes up and explains.', 34, 40),
    WidgetInfo('DropZoneMonsterWidget', 'dropzone', 'Drop Zone Monster', GROUP_HELPERS,
               'File drop zone guarded by a hungry monster.', 360, 300),
    WidgetInfo('PresenceAvatarWidget', 'presenceavatar', 'Presence Avatar', GROUP_HELPERS,
               'Initials avatar whose online status is its mood.', 130, 150),
    WidgetInfo('GooglyEyesWidget', 'googlyeyes', 'Googly Eyes', GROUP_MASCOTS,
               'Googly eyes that follow the cursor with real physics.', 260, 140),
    WidgetInfo('RubberDuckWidget', 'rubberduck', 'Rubber Duck', GROUP_MASCOTS,
               'Rubber-duck-debugging companion with dubious advice.', 320, 260),
]  # type: list[WidgetInfo]


def pluginsDir():
    """
    :return: (str | unicode | QString) Directory containing these plugin files.
    """
    return dirname(abspath(__file__))


def selectBinding(default=None):
    """
    Make ManyQt use the same Qt binding as the Designer that is loading us. Must run before anything imports
    ManyQt, otherwise ManyQt falls back to its default backend (PyQt5) inside a foreign Designer.
    :param default: (str | unicode | QString | None) QT_API value to use when the host has not imported a binding yet
                    (PySide6 Designer runs register*.py files before any binding is imported).
    :return: (str | None) The QT_API value chosen.
    """
    for module, api in HOSTS:
        if module in modules:
            environ['QT_API'] = api
            return api
    if default:
        environ['QT_API'] = default
        return default
    return environ.get('QT_API')


def ensureImportable():
    """
    Import QFunnyWidgets, adding the project root to sys.path when running from a source checkout
    (plugins/ next to the QFunnyWidgets/ package).
    :return: module
    """
    try:
        import QFunnyWidgets
    except:
        root = dirname(pluginsDir())  # type: str
        if root not in path:
            path.insert(0, root)
        import QFunnyWidgets
    return QFunnyWidgets


def logoPath(info):
    """
    :param info: WidgetInfo
    :return: (str | unicode | QString) Path of the widget's logo.png (beside its module).
    """
    QFunnyWidgets = ensureImportable()
    return join(dirname(QFunnyWidgets.__file__), info.package, 'logo.png')


def widgetClass(info):
    """
    :param info: WidgetInfo
    :return: (type) The widget class.
    """
    QFunnyWidgets = ensureImportable()
    __import__(info.module())
    return getattr(modules[info.module()], info.className)


def debug(message):
    """
    Print to stderr when FUNNYWIDGETS_DESIGNER_DEBUG is set (handy when a plugin does not show up).
    :param message: str | unicode | QString
    :return:
    """
    if environ.get('FUNNYWIDGETS_DESIGNER_DEBUG'):
        stderr.write('[QFunnyWidgets designer] {}\n'.format(message))
