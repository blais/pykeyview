#!/usr/bin/env python
"""
A live keyviewer uses OSD, for making demos and presentations.

When this was written, it was for a demo of an Emacs-related topic. Some of the
way the keys are displayed _may_ (or not) be influenced by that. I wrote this
fast, so it'll look it's put together with duct-tape.
"""
__author__ = 'Martin Blais <blais@furius.ca>'
# Note: A whole bunch of this code was copied from Matt Harrison's pykeyview and
# revamped for the osd version.

import string
from time import sleep
from StringIO import StringIO
from threading import Timer
import pyxhook, pyosd


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
    }


pressed_modifiers = set()
keys = [] # stack of keys typed

show_backspace = False
show_transients = False
limit_chars = 44

timer = None

hide_timeout = 1.1



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
        pass
    else:
        typed = KEY_MAP.get(key, key)
        keys.append(get_modifiers() + typed)
    update()

def gettext():
    "Join strings with a space except between simple letters."
    allkeys = keys
    if show_transients:
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
            keys.pop(0)
            text = gettext()

        osd.display(text, line=0)
        osd.show()

    # Reset the timer.
    global timer
    if timer:
        timer.cancel()
    timer = Timer(hide_timeout, on_timeout)
    timer.start()

def on_timeout():
    osd.hide()
    keys[:] = []
    timer = None

def get_hook_manager():
    hm = pyxhook.HookManager()
    hm.HookKeyboard()
    hm.HookMouse()
    hm.start()
    hm.KeyDown = on_keydown
    hm.KeyUp = on_keyup
    return hm


font = '-*-lucidatypewriter-*-r-*-*-34-*-*-*-*-*-*-*'
font = "-adobe-helvetica-bold-r-normal-*-*-320-*-*-p-*-*"
font = "-adobe-helvetica-bold-r-normal-*-*-480-*-*-p-*-*"
font = "-adobe-helvetica-bold-r-normal-*-*-400-*-*-p-*-*"

def main():
    import optparse
    parser = optparse.OptionParser(__doc__.strip())
    opts, args = parser.parse_args()

    global osd
    osd = pyosd.osd(font, "#22B022",
                    timeout=-1,
                    pos=pyosd.POS_BOT,
                    lines=2, # leave space for minibuffer
                    shadow=2,
                    )

    hm = get_hook_manager()

    # Allow interrupts.
    import signal; signal.signal(signal.SIGINT, signal.SIG_DFL)

if __name__ == '__main__':
    main()

#-------------------------------------------------------------------------------
# FIXME: TODO
# Add an option to ignore the Super modifier
# May make unmodified SPC behave like any other character
# Display transients modifiers
# Establish a delay for transient modifiers (hysteresis)
# Insert a spacer when paused
# Deal with overflow of line
# Don't make the characters disappear as long as I'm holding a modifier key
# Perhaps insert two spaces where there is a longer pause
# Make some of the parameters cmdline options
