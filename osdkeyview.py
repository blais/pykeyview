#!/usr/bin/env python
"""
A live keyviewer uses OSD, for making demos and presentations.

When this was written, it was for a demo of an Emacs-related topic. Some of the
way the keys are displayed _may_ (or not) be influenced by that.
"""
__author__ = 'Martin Blais <blais@furius.ca>'
# Note: A whole bunch of this code was copied from Matt Harrison's pykeyview and
# revamped for the osd version.

import string
from time import sleep
from StringIO import StringIO
from threading import Timer
import pyxhook, pyosd


"""
Options (many of these could be cmdline arguments).
"""

# Whether we should display the backspace char.
show_backspace = False

# True if we should always display the intermediate state of modifiers.
IMMEDIATE, DELAYED, NODISPLAY = map(lambda x: object(), xrange(3))
modifier_display = NODISPLAY

# A set of modifiers to avoid displaying.
# I use 'Super' here because it's my winmgr key.
ignore_modifiers = set(['Super_L', 'Super_R'])

# The maximum nb. of characters to display on a line.
limit_chars = 44

# If set to a string, insert this string when there is a short time delay
# between keystrokes. Insure this is at least a length of 2, so it's treated by
# display as a modifier and spaces are automatically inserted around it.
gapchars = '  '; # '__'
assert(len(gapchars) >= 2)

# Various timeouts.
timeout_hide    = 3.0  # Text hiding
timeout_gap     = 0.6  # Insert a gap
timeout_showmod = 0.8  # Show delayed modifiers

# Appearance.
font = '-*-lucidatypewriter-*-r-*-*-34-*-*-*-*-*-*-*'
font = "-adobe-helvetica-bold-r-normal-*-*-320-*-*-p-*-*"
font = "-adobe-helvetica-bold-r-normal-*-*-480-*-*-p-*-*"
font = "-adobe-helvetica-bold-r-normal-*-*-400-*-*-p-*-*"

color = "#22B022"
color = "white"



MODIFIERS = {
    'Control_L': 'C-',
    'Control_R': 'C-',
    'Alt_L': 'M-',
    'Alt_R': 'M-',
    'Super_L': 'S-',
    'Super_R': 'S-',
    'Shift_L': '',
    'Shift_R': '',
    }

# Alter the appearance of some key events
KEY_MAP = {
    'Return': '\n',
    'space': 'SPC',
    'parenleft': '(',
    'parenright': ')',
    'bracketleft': '[',
    'bracketright': ']',
    'braceleft': '{',
    'braceright': '}',
    'bar': '|',
    'minus': '-',
    'plus': '+',
    'asterisk': '*',
    'equal': '=',
    'less': '<',
    'greater': '>',
    'semicolon': ';',
    'colon': ': ',
    'comma': ',',
    'apostrophe': "'",
    'quotedbl' : '"',
    'underscore' : '_',
    'numbersign' : '#',
    'percent' : '%',
    'exclam' : '!',
    'period' : '.',
    'slash' : '/',
    'backslash' : '\\',
    'question' : '?',
    'BackSpace' : '<-',
    }



# Current set of modifiers that are pressed.
pressed_modifiers = set()

# Current state of modifier display
show_modifiers = False

# The current list of character strings to display.
keystack = [] # stack of keys typed


class TimingDevice:
    "A slightly more abstract and convenient timer."

    def __init__(self, callback, timeout):
        self.timer = None
        self.callback = callback
        self.timeout = timeout

    def reset(self):
        if self.timer:
            self.timer.cancel()
        self.timer = Timer(self.timeout, self.callback)
        self.timer.start()

    def cancel(self):
        if self.timer:
            self.timer.cancel()
        self.timer = None



def get_modifiers():
    return ''.join(sorted(MODIFIERS.get(m, '') for m in pressed_modifiers))

def on_keyup(event):
    key = event.Key
    pressed_modifiers.discard(key)
    update()

def on_keydown(event):
    #hm.printevent(event)
    key = event.Key
    if key in MODIFIERS:
        pressed_modifiers.add(key)
    elif key == 'BackSpace' and not show_backspace:
        reset_showmod()
        if gapchars: tm_gap.reset()
    else:
        reset_showmod()
        if gapchars: tm_gap.reset()
        typed = KEY_MAP.get(key, key)
        if not (ignore_modifiers & pressed_modifiers):
            keystack.append(get_modifiers() + typed)
    update()

def gettext():
    "Join strings with a space except between simple letters."
    allkeys = list(keystack)

    if allkeys and allkeys[0] == gapchars:
        allkeys.pop(0)
    if allkeys and allkeys[-1] == gapchars:
        allkeys.pop(-1)

    if show_modifiers or modifier_display is IMMEDIATE:
        if not (ignore_modifiers & pressed_modifiers):
            allkeys.append(gapchars)
            allkeys.extend(get_modifiers())

    oss = StringIO()
    prev = True
    for k in allkeys:
        cur = len(k) == 1
        if not (prev and  cur):
            oss.write(' ')
        oss.write(k)
        prev = cur
    return oss.getvalue().strip()

def update():
    text = gettext()
    if not text:
        osd.hide()
    else:
        while 1:
            if len(text) < limit_chars:
                break
            keystack.pop(0)
            text = gettext()

        osd.display(text, line=0)
        osd.show()

    tm_hide.reset()




def on_hide():
    if not pressed_modifiers:
        osd.hide()
        keystack[:] = []
    tm_hide.cancel()

tm_hide = TimingDevice(on_hide, timeout_hide)




def on_showmod():
    if pressed_modifiers:
        global show_modifiers; show_modifiers = True
    update()

def reset_showmod():
    global show_modifiers; show_modifiers = False
    if modifier_display is DELAYED:
        tm_showmod.reset()

tm_showmod = TimingDevice(on_showmod, timeout_showmod)



def on_gap():
    keystack.append(gapchars)
    update()
    tm_gap.cancel()

tm_gap = TimingDevice(on_gap, timeout_gap)



def get_hook_manager():
    "Setup and start the key snooper thread."
    hm = pyxhook.HookManager()
    hm.HookKeyboard()
    hm.HookMouse()
    hm.start()
    hm.KeyDown = on_keydown
    hm.KeyUp = on_keyup
    return hm



def main():
    import optparse
    parser = optparse.OptionParser(__doc__.strip())
    opts, args = parser.parse_args()

    global osd
    osd = pyosd.osd(font, color,
                    timeout=-1,
                    pos=pyosd.POS_BOT,
                    lines=1, # leave space for minibuffer
                    shadow=2,
                    )

    hm = get_hook_manager()

    # Allow interrupts.
    import signal; signal.signal(signal.SIGINT, signal.SIG_DFL)

if __name__ == '__main__':
    main()
