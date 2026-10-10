# coding=utf-8
"""
Root package: aggregates all components.
"""
__version__ = '1.0.0'  # type: str

from os.path import dirname
from sys import path

if dirname(__file__) not in path:
    path.append(dirname(__file__))

try:
    from .googlyeyes import GooglyEyesWidget
    from .runawaybutton import RunawayButtonWidget
    from .jellyswitch import JellySwitchWidget
    from .hamsterloader import HamsterLoaderWidget
    from .moodslider import MoodSliderWidget
    from .ratingstars import StarRatingWidget
    from .holdbutton import NervousHoldButtonWidget
    from .panicbell import PanicBellWidget
    from .rubberduck import RubberDuckWidget
    from .passwordjudge import PasswordJudgeWidget
    from .cookieconsent import CookieConsentWidget
    from .typingindicator import TypingIndicatorWidget
    from .emptystate import EmptyStateWidget
    from .volumeknob import VolumeKnobWidget
    from .pigeontoast import PigeonToast
    from .dropzone import DropZoneMonsterWidget
    from .batterybuddy import BatteryBuddyWidget
    from .presenceavatar import PresenceAvatarWidget
    from .ducklingpager import DucklingPagerWidget
    from .deadline import DeadlineCountdownWidget
    from .searchdetective import SearchDetectiveWidget
    from .robotcheck import RobotCheckWidget
    from .chameleonpicker import ChameleonColorPickerWidget
    from .errorgremlin import ErrorGremlinWidget
    from .snailstepper import SnailStepperWidget
    from .pancakestepper import PancakeStepperWidget
    from .heartlike import HeartLikeButtonWidget
    from .copyblob import CopyBlobButtonWidget
    from .rockettop import RocketBackToTop
    from .catsection import SleepyCatSectionWidget
    from .dachshundtabs import DachshundTabsWidget
    from .puffercounter import PufferCounterWidget
    from .helpowl import HelpOwlWidget
    from .antbreadcrumb import AntBreadcrumbWidget
    from .autosave import AutosaveSquirrelWidget
except:
    from googlyeyes import GooglyEyesWidget
    from runawaybutton import RunawayButtonWidget
    from jellyswitch import JellySwitchWidget
    from hamsterloader import HamsterLoaderWidget
    from moodslider import MoodSliderWidget
    from ratingstars import StarRatingWidget
    from holdbutton import NervousHoldButtonWidget
    from panicbell import PanicBellWidget
    from rubberduck import RubberDuckWidget
    from passwordjudge import PasswordJudgeWidget
    from cookieconsent import CookieConsentWidget
    from typingindicator import TypingIndicatorWidget
    from emptystate import EmptyStateWidget
    from volumeknob import VolumeKnobWidget
    from pigeontoast import PigeonToast
    from dropzone import DropZoneMonsterWidget
    from batterybuddy import BatteryBuddyWidget
    from presenceavatar import PresenceAvatarWidget
    from ducklingpager import DucklingPagerWidget
    from deadline import DeadlineCountdownWidget
    from searchdetective import SearchDetectiveWidget
    from robotcheck import RobotCheckWidget
    from chameleonpicker import ChameleonColorPickerWidget
    from errorgremlin import ErrorGremlinWidget
    from snailstepper import SnailStepperWidget
    from pancakestepper import PancakeStepperWidget
    from heartlike import HeartLikeButtonWidget
    from copyblob import CopyBlobButtonWidget
    from rockettop import RocketBackToTop
    from catsection import SleepyCatSectionWidget
    from dachshundtabs import DachshundTabsWidget
    from puffercounter import PufferCounterWidget
    from helpowl import HelpOwlWidget
    from antbreadcrumb import AntBreadcrumbWidget
    from autosave import AutosaveSquirrelWidget

__all__ = ['GooglyEyesWidget', 'RunawayButtonWidget', 'JellySwitchWidget', 'HamsterLoaderWidget', 'MoodSliderWidget', 'StarRatingWidget', 'NervousHoldButtonWidget', 'PanicBellWidget', 'RubberDuckWidget', 'PasswordJudgeWidget', 'CookieConsentWidget', 'TypingIndicatorWidget', 'EmptyStateWidget', 'VolumeKnobWidget', 'PigeonToast', 'DropZoneMonsterWidget', 'BatteryBuddyWidget', 'PresenceAvatarWidget', 'DucklingPagerWidget', 'DeadlineCountdownWidget', 'SearchDetectiveWidget', 'RobotCheckWidget', 'ChameleonColorPickerWidget', 'ErrorGremlinWidget', 'SnailStepperWidget', 'PancakeStepperWidget', 'HeartLikeButtonWidget', 'CopyBlobButtonWidget', 'RocketBackToTop', 'SleepyCatSectionWidget', 'DachshundTabsWidget', 'PufferCounterWidget', 'HelpOwlWidget', 'AntBreadcrumbWidget', 'AutosaveSquirrelWidget']  # type: list[str]
