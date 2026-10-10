# QFunnyWidgets

[![PyPI](https://img.shields.io/pypi/v/QFunnyWidgets)](https://pypi.org/project/QFunnyWidgets/)
[![Python](https://img.shields.io/pypi/pyversions/QFunnyWidgets)](https://pypi.org/project/QFunnyWidgets/)
[![Downloads](https://img.shields.io/pypi/dm/QFunnyWidgets)](https://pypi.org/project/QFunnyWidgets/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](https://github.com/Usama01TN/QFunnyWidgets/blob/main/LICENSE.md)
[![Release](https://github.com/Usama01TN/QFunnyWidgets/actions/workflows/release.yml/badge.svg)](https://github.com/Usama01TN/QFunnyWidgets/actions/workflows/release.yml)

**Definition.** A library of 35 custom-painted, animated Qt widgets with a sense of humour, written on top of
[ManyQt](https://github.com/Usama01TN/ManyQt) so the same code runs on PyQt5, PyQt6, PySide6 (and the other
bindings ManyQt supports), under Python 2.7 and Python 3.

**Goal.** Give serious applications a little personality: every widget is a drop-in, fully
configurable `QWidget` that behaves like a normal control (signals, properties, keyboard support)
but animates like a cartoon. Pure Python: ManyQt + one Qt binding, nothing else.

## Quick start:

```bash
pip install QFunnyWidgets[pyqt5]     # or [pyqt6], [pyside6], [pyside2]
funnywidgets-mainwindow              # opens the gallery of all 35 widgets
```

```python
from ManyQt.QtWidgets import QApplication, QVBoxLayout, QWidget
from QFunnyWidgets import JellySwitchWidget, HeartLikeButtonWidget
from sys import argv, exit

app = QApplication(argv)  # type: QApplication
window = QWidget()  # type: QWidget
layout = QVBoxLayout(window)  # type: QVBoxLayout
layout.addWidget(JellySwitchWidget(checked=True, toggled=lambda on: print('on' if on else 'off')))
layout.addWidget(HeartLikeButtonWidget(count=41))
window.show()
exit(app.exec_())
```

![Logos](https://raw.githubusercontent.com/Usama01TN/QFunnyWidgets/main/docs/logos.png)

![Classics](https://raw.githubusercontent.com/Usama01TN/QFunnyWidgets/main/docs/gallery.png)

<details>
<summary>More screenshots (6 more gallery pages)</summary>

![New arrivals](https://raw.githubusercontent.com/Usama01TN/QFunnyWidgets/main/docs/gallery2.png)
![Fresh batch](https://raw.githubusercontent.com/Usama01TN/QFunnyWidgets/main/docs/gallery3.png)
![Daily drivers](https://raw.githubusercontent.com/Usama01TN/QFunnyWidgets/main/docs/gallery4.png)
![Power tools](https://raw.githubusercontent.com/Usama01TN/QFunnyWidgets/main/docs/gallery5.png)
![Finishing touches](https://raw.githubusercontent.com/Usama01TN/QFunnyWidgets/main/docs/gallery6.png)
![Little details](https://raw.githubusercontent.com/Usama01TN/QFunnyWidgets/main/docs/gallery7.png)

</details>

## Contents:

### Interactive controls:

| Package           | Class                        | What it does                                                                                                                                                                                                                                              |
|-------------------|------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `jellyswitch`     | `JellySwitchWidget`          | Toggle switch whose jelly knob has a face: sleeps with floating "z" when off, wakes up blushing when on, squashes when pressed and wobbles as it slides.                                                                                                  |
| `moodslider`      | `MoodSliderWidget`           | Slider whose thumb is a face that goes from furious (red, shaking, steaming) to ecstatic (heart eyes, floating hearts). Tilts with drag speed, shows a mood bubble.                                                                                       |
| `runawaybutton`   | `RunawayButtonWidget`        | A button that dodges the cursor with springy squash & stretch and taunts you; after `maxEscapes` it gets tired, sweats and lets you click it (confetti).                                                                                                  |
| `ratingstars`     | `StarRatingWidget`           | Star rating where every star has a face: hover previews the mood, clicks send a bounce wave, 1 star makes the others cry, 5 stars makes them all dance.                                                                                                   |
| `holdbutton`      | `NervousHoldButtonWidget`    | Hold-to-confirm button for destructive actions. Fills while held, shakes and sweats more with each stage ("Are you sure?"), sighs "Phew!" if released early, faints when confirmed.                                                                       |
| `volumeknob`      | `VolumeKnobWidget`           | Rotary volume dial with a face: zipped mouth when muted, hums and sings (floating notes) at mid volume, squints with sound waves when loud, screams and turns red at 100 %. Drag, wheel, arrows, double-click or M to mute.                               |
| `dropzone`        | `DropZoneMonsterWidget`      | Real drag-and-drop upload zone guarded by a hungry monster: opens wide and drools when files hover, chomps and burps when they drop, sticks its tongue out at unaccepted extensions. Click to browse.                                                     |
| `ducklingpager`   | `DucklingPagerWidget`        | Carousel page indicator: pages are lily pads, mother duck swims to the current one with her ducklings in tow and quacks on arrival. Click, wheel or arrow keys.                                                                                           |
| `searchdetective` | `SearchDetectiveWidget`      | Debounced search field with a deerstalker detective: pipe smoke while idle, sweeping magnifier while typing, "Elementary!" on results, a personal rain cloud on none. Emits `searchRequested`; report with `setResultCount()` or pass a `searchFunction`. |
| `robotcheck`      | `RobotCheckWidget`           | "I'm not a robot" box with a robot hiding behind it: pops up sweating oil during the check, winks and gives a thumbs-up when you pass. Optional `failChance`.                                                                                             |
| `chameleonpicker` | `ChameleonColorPickerWidget` | Swatch color picker: the chameleon's eyes move independently, its tongue grabs the chosen color, and the color washes over it from head to tail.                                                                                                          |
| `snailstepper`    | `SnailStepperWidget`         | Wizard / checkout step indicator: a snail carries progress between steps at a strictly limited pace, leaving a glistening slime trail and complaining when rushed.                                                                                        |
| `pancakestepper`  | `PancakeStepperWidget`       | Quantity input (spin box) as a pancake stack: "+" drops one on with a squash, "-" flips the top one off; butter and syrup on top; it wobbles near the maximum and refuses more.                                                                           |
| `heartlike`       | `HeartLikeButtonWidget`      | Like button: liking pops the heart with a burst of mini hearts and a heartbeat; un-liking cracks it (then a bandage); toggling too fast makes it dizzy. Odometer-style counter.                                                                           |
| `copyblob`        | `CopyBlobButtonWidget`       | Copy-to-clipboard chip for commands, keys or codes: the blob mascot splits in two and the clone hops into the clipboard. Shows a masked label while copying the real text.                                                                                |
| `rockettop`       | `RocketBackToTop`            | Back-to-top button for any scroll area: appears after a threshold, launches with flame and smoke while smoothly scrolling up, returns by parachute. Only the rocket takes clicks.                                                                         |
| `dachshundtabs`   | `DachshundTabsWidget`        | Segmented control / tab bar whose selection highlight is a dachshund: the front end runs ahead, the body stretches across the tabs, the rear catches up.                                                                                                  |
| `puffercounter`   | `PufferCounterWidget`        | Text area with a character limit and a pufferfish that inflates as you approach it, grows spikes, and turns red and furious past it. Optional hard limit.                                                                                                 |
| `helpowl`         | `HelpOwlWidget`              | Inline "?" help icon that is a sleeping owl: hover and it wakes, swivels its head and shows a floating help bubble (flips side near window edges). Click to pin.                                                                                          |
| `antbreadcrumb`   | `AntBreadcrumbWidget`        | Breadcrumb navigation of real bread crumbs: ants march underneath, carry away crumbs when you go up and carry in new ones when you go deeper.                                                                                                             |
| `passwordjudge`   | `PasswordJudgeWidget`        | Password field reviewed live by a powdered-wig judge: eyes follow the text cursor, monocle pops off at bad passwords, strength meter, covers his eyes on "Show". `JudgeFaceWidget` and `passwordStrength()` are usable on their own.                      |

### Feedback & indicators:

| Package           | Class                     | What it does                                                                                                                                                                                                           |
|-------------------|---------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `typingindicator` | `TypingIndicatorWidget`   | Chat "..." indicator whose dots are creatures: bouncing (Typing), staring up with a "?" (Thinking), vibrating while vanishing one by one (Deleting) or snoozing (Sleeping). `autoCycle` simulates an indecisive human. |
| `pigeontoast`     | `PigeonToast`             | Toast overlay for any widget: a flapping carrier pigeon flies in with your message on a swinging banner, drops a few feathers and flies off. Queued, mouse-transparent, follows the parent's size.                     |
| `autosave`        | `AutosaveSquirrelWidget`  | Autosave status with built-in debounce and retry: the squirrel naps (saved), sits up (unsaved), stashes acorns (saving) or drops one and facepalms (error). Shows "Saved 2 min ago".                                   |
| `batterybuddy`    | `BatteryBuddyWidget`      | Battery indicator that bounces when full, yawns when low, sweats and slumps near empty, flickers at 3 % and happily munches electricity while charging. Emits `lowBattery()`.                                          |
| `deadline`        | `DeadlineCountdownWidget` | Countdown timer hosted by a tear-off calendar: sunglasses with plenty of time, focus, sweat, shaking red panic, and calmly on fire ("This is fine") when overdue. `extend()` brings relief.                            |
| `panicbell`       | `PanicBellWidget`         | Notification bell that naps at 0, swings and dings on new items, sweats past `panicThreshold`, melts down at "99+" (spiral eyes, alarm glow). Click to clear; it sighs with relief.                                    |
| `hamsterloader`   | `HamsterLoaderWidget`     | Progress indicator powered by a hamster in a wheel. Runs faster as progress grows, sweats past 60 %, cycles silly status messages, celebrates at 100 %. Indeterminate mode with `progress < 0`.                        |

### Banners & placeholders:

| Package         | Class                 | What it does                                                                                                                                                                                                                |
|-----------------|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `errorgremlin`  | `ErrorGremlinWidget`  | Inline alert banner whose gremlin matches the severity: napping (Info), peeking with a wrench (Warning), chewing a cable with sparks (Error), bouncing in front of a fire (Critical). Retry scares it off; close fades out. |
| `cookieconsent` | `CookieConsentWidget` | Cookie banner starring a cookie: hopeful puppy eyes, excited when you hover Accept, lip quivering at Decline. Accepted, it is eaten in three bites with crumbs; declined, it sobs.                                          |
| `emptystate`    | `EmptyStateWidget`    | "Nothing here yet" placeholder in a tiny desert: bouncing tumbleweed, bored cactus, chirping crickets and a call-to-action button.                                                                                          |

### Containers:

| Package      | Class                    | What it does                                                                                                                                                                                 |
|--------------|--------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `catsection` | `SleepyCatSectionWidget` | Collapsible section with animated height and a cat on the header: asleep when collapsed, startled awake on expand, yawning on collapse. Holds any widget. `CatHeaderWidget` is usable alone. |

### Identity:

| Package          | Class                  | What it does                                                                                                                                                                            |
|------------------|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `presenceavatar` | `PresenceAvatarWidget` | Initials avatar with a name-derived color whose presence status is its mood: online (eyes follow you), away (dozing, moon badge), busy (headphones, frown), offline (a floating ghost). |

### Decorative / mascots:

| Package      | Class              | What it does                                                                                                                                                   |
|--------------|--------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `googlyeyes` | `GooglyEyesWidget` | Googly eyes with real spring + gravity physics that follow the cursor anywhere on screen, blink, spin dizzy when poked and get angry if poked 3 times quickly. |
| `rubberduck` | `RubberDuckWidget` | Rubber-duck-debugging companion bobbing on water. Squeaks on click and dispenses dev advice; `listen(text)` makes it nod thoughtfully before answering.        |

## Key features:

- 60 fps animation driven by `QTimer` + `QElapsedTimer` (frame-rate independent physics); timers stop when the widget is
  hidden.
- Everything painted with `QPainter` and antialiasing, scales cleanly to any size.
- Every option is a constructor kwarg, a `getX()/setX()` pair (setters are `@pyqtSlot`s) and a `pyqtProperty`.
- Every event is a `pyqtSignal`, also accepted as a callable kwarg (`toggled=self.onToggled`).
- Colours accept `QColor`, `Qt.GlobalColor`, hex strings or ints. Painted text follows the palette, so widgets work on
  light and dark themes.
- Each package is standalone: copy one folder into your project and it works.
- One code base for every Qt binding (through ManyQt) and for Python 2.7 / 3.x (see *Compatibility*).
- Every widget ships its own icon, `<widget>/logo.png`, right beside its module (used as the demo window icon).
- Qt Designer plugins for 33 widgets in a single `plugins/` directory (PyQt and PySide6 Designer), with live
  property editing and `uic` support.
- Installable with pip (universal Python 2/3 wheel), with `funnywidgets-mainwindow` and `funnywidgets-designer` commands.

## Installation:

From [PyPI](https://pypi.org/project/QFunnyWidgets/), with the Qt binding of your choice:

```bash
pip install QFunnyWidgets[pyqt5]      # or [pyqt6], [pyside6], [pyside2]
pip install QFunnyWidgets             # library only, when a binding is already installed
pip install --upgrade QFunnyWidgets   # update to the latest release
```

QFunnyWidgets depends on [ManyQt](https://github.com/Usama01TN/ManyQt), which pip installs automatically. Python 2.7
installs the same way; `enum34` is pulled in there too (it backs the four widgets that use enums).

From source (for development):

```bash
git clone https://github.com/Usama01TN/QFunnyWidgets.git
cd QFunnyWidgets
pip install -e .[pyqt5]               # editable install
python -m build                       # dist/qfunnywidgets-<version>-py2.py3-none-any.whl and .tar.gz
```

Installing also adds two commands:

| Command                               | What it does                                                                 |
|---------------------------------------|------------------------------------------------------------------------------|
| `funnywidgets-mainwindow`             | Opens the seven-page gallery of all widgets.                                 |
| `funnywidgets-designer [form.ui ...]` | Opens Qt Designer with the QFunnyWidgets plugins loaded (see *Qt Designer*). |

## Run:

Installed:

```bash
funnywidgets-mainwindow
QT_API=pyqt6 funnywidgets-mainwindow           # pick a backend explicitly (pyqt4/pyqt5/pyqt6/pyside/pyside2/pyside6)
```

From a source checkout (no install needed, just `pip install ManyQt PyQt5`):

```bash
python QFunnyWidgets/main.py                 # the full gallery
python QFunnyWidgets/googlyeyes/main.py      # any single widget demo
```

## Qt Designer:

All Designer plugins live in one directory, `plugins/` (installed as `QFunnyWidgets.plugins`):

| File                      | Used by                                                                               |
|---------------------------|---------------------------------------------------------------------------------------|
| `funnywidgetsplugin.py`   | Qt Designer of **PyQt4 / PyQt5 / PyQt6** (loads `*plugin.py` from `PYQTDESIGNERPATH`) |
| `registerfunnywidgets.py` | Qt Designer of **PySide6** (runs `register*.py` from `PYSIDE_DESIGNER_PLUGINS`)       |
| `funnywidgetsinfo.py`     | Shared table of the 33 widgets (class, group, tooltip, default size) and helpers      |

**Easiest:** `funnywidgets-designer` (or `python -m QFunnyWidgets.designer` from a checkout) finds the plugins,
sets the environment and starts the first Designer it finds: `pyside6-designer` (comes with PySide6),
`pyqt5-tools designer` / `pyqt6-tools designer`, or a system `designer`. Set `QT_API` to prefer one.
`funnywidgets-designer --print-env` prints the variables if you prefer to start Designer yourself:

```bash
export PYQTDESIGNERPATH=/path/to/plugins         # PyQt Designer
export PYSIDE_DESIGNER_PLUGINS=/path/to/plugins  # PySide6 Designer
export PYTHONPATH=/path/to/project               # only for a source checkout
```

In Designer the widgets appear in six groups (*QFunnyWidgets: Inputs, Buttons, Navigation, Feedback,
Containers & helpers, Mascots*) with their logos as icons. Every option shows up in the property editor (they
are `pyqtProperty`s), and saved forms compile normally: `pyuic5`, `pyuic6` and `pyside6-uic` generate
`from QFunnyWidgets.<package> import <Class>`.

Notes:

- `PigeonToast` and `RocketBackToTop` are not in Designer: they are overlays that attach to a parent widget or a
  scroll area when created, so create them in code.
- Each plugin makes ManyQt use the binding of the Designer that loads it (the PySide6 file selects `pyside6`),
  so widgets never load a second Qt binding into Designer.
- If a widget does not appear, start Designer with `FUNNYWIDGETS_DESIGNER_DEBUG=1` to see what the plugins did.
- PyQt's Designer comes from `pyqt5-tools` / `pyqt6-tools`, which currently publish no wheels for Python 3.12;
  use Python 3.11 or earlier for those, or PySide6 Designer.

## Compatibility:

|                            | Status                                                                                                                                                                                         |
|----------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **PyQt5** (ManyQt default) | All 35 demos, the 7-page gallery and interaction tests pass.                                                                                                                                   |
| **PyQt6**                  | All 35 demos, the gallery and interaction tests pass.                                                                                                                                          |
| **PySide6**                | Same results, but see *Known issue* below (a ManyQt bug, not a QFunnyWidgets one).                                                                                                             |
| **Python 3**               | Tested in CI on 3.9 and 3.12 with PyQt5 and PyQt6 on every release.                                                                                                                            |
| **Python 2.7**             | Every file compiles with CPython 2.7.18; the sdist and the universal wheel install with Python 2.7's pip, and `enum34` (installed automatically) covers the four widgets with enums.           |
| **PySide6 Designer**       | Tested in the real `pyside6-designer`: all 33 widgets register, from a checkout and from an installed wheel.                                                                                   |
| **PyQt5 / PyQt6 Designer** | The plugin is tested the way Designer's loader uses it (all 33 classes, icons, XML, include paths) on both bindings in CI; PyQt's Designer itself needs `pyqt5-tools` / `pyqt6-tools` (see *Qt Designer* notes). |

How the code stays neutral:

- Imports come from `ManyQt.QtCore / QtGui / QtWidgets`; `pyqtSignal`, `pyqtSlot` and `pyqtProperty` are provided by
  ManyQt under every binding.
- APIs that differ between Qt versions are feature-detected: mouse positions through a small `eventPos(e)` helper (
  `position()` on Qt 6, `localPos()` on Qt 5, `posF()` on Qt 4), `QWidget.screen()` vs `QDesktopWidget`,
  `QButtonGroup.idClicked` vs `buttonClicked[int]`, Qt-5-only HiDPI attributes.
- Properties use types every binding can register (`QObject`, `object`, `'QString'`, `'QStringList'`).

**Known issue (ManyQt 0.4.8 + PySide6 >= 6.8 on Python >= 3.11).** `import ManyQt.QtCore` raises
`AttributeError: <enum 'RegexFlag'> cannot set attribute 'NOFLAG'` from `ManyQt/_fixes.py`
(`lift_enum_namespace` calls `setattr` on Python's own `re.RegexFlag`). It happens before any QFunnyWidgets
code runs. Wrapping that `setattr(type_, name, value)` in `try/except AttributeError` fixes it; until ManyQt
ships a fix, use PyQt5 or PyQt6, or patch locally.

## Integration:

1. `pip install QFunnyWidgets[pyqt5]` (see *Installation*), **or** copy the `QFunnyWidgets` package folder (or a single
   widget folder such as `jellyswitch/`) into your project and `pip install ManyQt` plus a binding.
2. Design forms in Qt Designer with the plugins (see *Qt Designer*), or create widgets in code.
3. Import and use it like any other widget:

```python
from QFunnyWidgets import JellySwitchWidget, HamsterLoaderWidget, MoodSliderWidget, NervousHoldButtonWidget

switch = JellySwitchWidget(checked=True, onColor='#5E60CE', toggled=lambda on: print('on' if on else 'off'))
loader = HamsterLoaderWidget(progress=0.0, finished=lambda: print('done'))
loader.setProgress(0.42)                  # 0..1, or -1 for indeterminate
mood = MoodSliderWidget(value=50, moodChanged=print)
delete = NervousHoldButtonWidget(holdDuration=2000, confirmed=self.deleteEverything)

from QFunnyWidgets import PigeonToast
toast = PigeonToast(self.centralWidget())   # overlay, follows the parent's size
toast.showMessage('File saved successfully.')
layout.addWidget(switch)
```

## Logos:

Each package contains `logo.png` (256 x 256, transparent corners) right beside its module, e.g.
`heartlike/heartlike.py` + `heartlike/logo.png`, so copying the folder copies the icon too. Use it anywhere:

```python
from os.path import dirname, join
from ManyQt.QtGui import QIcon
import QFunnyWidgets.googlyeyes as pkg
icon = QIcon(join(dirname(pkg.__file__), 'logo.png'))
```

The logos are rendered from the real widgets by `makelogos.py`, which puts each widget in its most
characteristic state, crops to the character and places it on a rounded-square tile. After changing a widget,
regenerate them with `python QFunnyWidgets/makelogos.py` (optionally `python QFunnyWidgets/makelogos.py 512`).

## Options at a glance:

- **GooglyEyesWidget**: `eyeCount`, `eyeColor`, `pupilColor`, `lidColor`, `wobble` (0..1), `gravity`, `blinkInterval`,
  `autoBlink`; signals `poked(int)`, `gotAngry()`; slots `blink()`, `makeDizzy()`.
- **RunawayButtonWidget**: `text`, `tiredText`, `color`, `textColor`, `dodgeRadius`, `maxEscapes` (0 = never gives up),
  `taunts`, `autoReset`; signals `clicked()`, `escaped(int)`, `caught(int)`; slot `reset()`.
- **JellySwitchWidget**: `checked`, `onColor`, `offColor`, `knobColor`, `wobbliness`, `showFace`; signal
  `toggled(bool)`; slot `toggle()`. Space/Enter toggles.
- **HamsterLoaderWidget**: `progress`, `speed`, `hamsterColor`, `wheelColor`, `accentColor`, `messages`,
  `messageInterval`, `doneText`, `showPercent`; signals `finished()`, `progressChanged(float)`; slot `reset()`.
- **StarRatingWidget**: `rating`, `maxRating`, `starColor`, `emptyColor`, `labels`, `placeholder`, `showLabel`,
  `allowClear`; signals `ratingChanged(int)`, `hovered(int)`. Arrow and number keys.
- **NervousHoldButtonWidget**: `stages`, `doneText`, `reliefText`, `holdDuration`, `color`, `textColor`, `autoReset`;
  signals `confirmed()`, `cancelled(float)`; slot `reset()`. Hold Space works too.
- **PanicBellWidget**: `count`, `color`, `badgeColor`, `panicThreshold`, `maxDisplay`, `clearOnClick`; signals
  `clicked()`, `countChanged(int)`; slots `increment()`, `clear()`, `ring()`.
- **RubberDuckWidget**: `duckColor`, `beakColor`, `waterColor`, `advice`, `adviceOnClick`, `adviceDuration`,
  `squeakText`; signals `squeaked(int)`, `adviceGiven(str)`; slots `squeak()`, `listen(text)`.
- **PasswordJudgeWidget**: `text`, `placeholder`, `minLength`, `showToggle`, `revealed`; signals
  `strengthChanged(int)` (-1 empty, 0 terrible .. 4 strong), `textChanged(str)`, `returnPressed()`; `getLineEdit()` /
  `getFace()` give access to the children.
- **CookieConsentWidget**: `title`, `message`, `acceptText`, `declineText`, `acceptedMessage`, `declinedMessage`,
  `accentColor`, `panelColor`, `textColor`, `cookieColor`, `autoReset`; signals `accepted()`, `declined()`; slots
  `accept()`, `decline()`, `reset()`.
- **TypingIndicatorWidget**: `state` (`Typing`, `Thinking`, `Deleting`, `Sleeping`), `name`, `bubbleColor`, `dotColor`,
  `autoCycle`; signal `stateChanged(int)`.
- **EmptyStateWidget**: `title`, `subtitle`, `actionText` (empty hides the button), `accentColor`, `sandColor`, `speed`;
  signal `actionClicked()`.
- **VolumeKnobWidget**: `value` (0..100), `knobColor`, `trackColor`, `showLabel`; signal `valueChanged(int)`; slot
  `toggleMute()`.
- **PigeonToast**: create with the widget to cover, e.g. `PigeonToast(self.centralWidget())`; `duration`, `bannerColor`,
  `textColor`, `pigeonColor`, `caption`, `margin`; slots `showMessage(text, duration=-1)`, `dismiss()`; signals
  `messageShown(str)`, `messageFinished(str)`.
- **DropZoneMonsterWidget**: `acceptedExtensions` (empty = all), `hint`, `subtitle`, `monsterColor`, `accentColor`,
  `clickToBrowse`; signals `filesDropped(list)`, `filesRejected(list)`; slots `feed(paths)`, `browse()`.
- **BatteryBuddyWidget**: `level` (0..100), `charging`, `lowThreshold`, `caseColor`, `showLabel`; signals
  `levelChanged(int)`, `chargingChanged(bool)`, `lowBattery()`.
- **PresenceAvatarWidget**: `name`, `status` (`Online`, `Away`, `Busy`, `Offline`), `color` (default derived from the
  name), `badgeBorderColor`; signals `clicked()`, `statusChanged(int)`.
- **DucklingPagerWidget**: `count`, `current`, `ducklings` (0..6), `wrap`, `duckColor`, `ducklingColor`, `padColor`;
  signal `currentChanged(int)`; slots `next()`, `previous()`.
- **DeadlineCountdownWidget**: `duration` (s), `title`, `timeScale`, `accentColor`; signals `expired()`,
  `remainingChanged(int)`; slots `start(seconds=-1)`, `pause()`, `resume()`, `extend(seconds)`.
- **SearchDetectiveWidget**: `text`, `placeholder`, `debounce` (ms), `searchFunction` (text -> count); signals
  `searchRequested(str)`, `textChanged(str)`, `returnPressed()`; slot `setResultCount(int)`. `DetectiveFaceWidget` is
  usable on its own.
- **RobotCheckWidget**: `text`, `verifiedText`, `failChance`, `panelColor`, `textColor`, `robotColor`; signals
  `verified()`, `failed()`; slots `verify()`, `reset()`.
- **ChameleonColorPickerWidget**: `color`, `colors`, `columns`, `showHex`, `branchColor`; signal `colorChanged(QColor)`.
  Arrow keys move between swatches.
- **ErrorGremlinWidget**: `severity` (`Info`, `Warning`, `Error`, `Critical`), `title`, `message`, `retryText` (empty
  hides it), `closable`, `panelColor`, `textColor`; signals `retryClicked()`, `dismissed()`; slots
  `showAlert(severity, title, message)`, `dismiss()`.
- **SnailStepperWidget**: `steps`, `current`, `speed` (px/s), `clickable`, `accentColor`, `shellColor`; signals
  `currentChanged(int)`, `arrived(int)`; slots `next()`, `previous()`.
- **PancakeStepperWidget**: `value`, `minimum`, `maximum` (<= 20), `unit`, `accentColor`; signal `valueChanged(int)`;
  slots `increment()`, `decrement()`. Wheel, arrows, +/-.
- **HeartLikeButtonWidget**: `liked`, `count`, `color`, `showCount`; signals `likedChanged(bool)`, `countChanged(int)`;
  slot `toggle()`.
- **CopyBlobButtonWidget**: `text` (copied), `label` (shown, optional), `prompt`, `blobColor`, `chipColor`, `textColor`;
  signal `copied(str)`; slot `copy()`. Ctrl+C works when focused.
- **RocketBackToTop**: create with the scroll area, e.g. `RocketBackToTop(myScrollArea)`; `threshold` (px), `color`,
  `bodyColor`, `label`; signal `launched()`; slot `launch()`.
- **SleepyCatSectionWidget**: `title`, `expanded`, `contentWidget` (or `content=` kwarg), header colours via kwargs
  `catColor`, `barColor`, `textColor`; signal `toggled(bool)`; slots `toggle()`, `setExpanded(bool)`. For accordion
  behaviour, collapse the others on `toggled(True)`.
- **DachshundTabsWidget**: `tabs`, `current`, `dogColor`, `trackColor`; signal `currentChanged(int)`. Left/Right keys.
- **PufferCounterWidget**: `text`, `placeholder`, `maxLength`, `enforceLimit`; signals `textChanged(str)`,
  `limitExceeded(bool)`; `getEditor()` returns the `QPlainTextEdit`. `PufferFooterWidget` is usable alone.
- **HelpOwlWidget**: `helpText`, `title`, `owlColor`; signals `shown()`, `hidden()`; slots `showHelp()`, `hideHelp()`.
  F1/Space toggles, Esc closes. `HelpBubble` is usable alone.
- **AntBreadcrumbWidget**: `path`, `crumbColor`, `antColor`, `marchingAnts`; signals `crumbClicked(int)`,
  `pathChanged(list)`; slots `push(name)`, `navigateTo(index)`, `setPath(list)`.
- **AutosaveSquirrelWidget**: `status` (`Saved`, `Unsaved`, `Saving`, `Error`), `autosaveDelay`, `retryDelay`,
  `squirrelColor`; signals `saveRequested()`, `statusChanged(int)`; slots `markDirty()`, `requestSave()`,
  `saveFinished(ok)`. Wire your editor's change signal to `markDirty` and your save routine to `saveRequested`.
- **MoodSliderWidget**: `value`, `minimum`, `maximum`, `labels`, `showLabel`, `trackColor`; signals `valueChanged(int)`,
  `moodChanged(str)`. Mouse drag, wheel, arrows, PageUp/Down, Home/End.

## Development:

```bash
QT_API=pyqt5 python tests/smoke.py     # every demo + the Designer plugins, headless
```

Releases are automated by `.github/workflows/release.yml`: bump `__version__` in `QFunnyWidgets/__init__.py`, then
create a GitHub release with a matching tag (e.g. `v1.0.1`). The workflow tests, builds, publishes to PyPI and
attaches the files to the release.

## Links:

- **PyPI:** [pypi.org/project/QFunnyWidgets](https://pypi.org/project/QFunnyWidgets/)
- **Releases and changelog:** [GitHub Releases](https://github.com/Usama01TN/QFunnyWidgets/releases)
- **Bug reports and ideas:** [GitHub Issues](https://github.com/Usama01TN/QFunnyWidgets/issues)
- **ManyQt** (the binding layer): [github.com/Usama01TN/ManyQt](https://github.com/Usama01TN/ManyQt)

## Support:

If QFunnyWidgets is useful to you, feel free to support its development:

<p>
  <a href="https://ba9chich.com/fr/IninouUsama"><img src="https://img.shields.io/badge/ba9chich-Support%20me-E4002B?style=for-the-badge" alt="Support me on ba9chich"></a>
  <a href="https://ko-fi.com/usamatn"><img src="https://img.shields.io/badge/Ko--fi-Buy%20me%20a%20coffee-FF5E5B?style=for-the-badge&logo=ko-fi&logoColor=white" alt="Buy me a coffee on Ko-fi"></a>
</p>

- **ba9chich:** [ba9chich.com/fr/IninouUsama](https://ba9chich.com/fr/IninouUsama)
- **Ko-fi:** [ko-fi.com/usamatn](https://ko-fi.com/usamatn)

Thank you :)

## License:

MIT, see [LICENSE.md](https://github.com/Usama01TN/QFunnyWidgets/blob/main/LICENSE.md).
