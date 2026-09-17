#!/usr/bin/env python3
"""Launch mGBA (Qt AppImage) on the local X display, drive it with XTEST key presses and capture its window.
usage: mgba_capture.py ROM OUTDIR [script]   script: comma list of <seconds>[:key]  (key = X keysym name, e.g. Return, x, z, Left)"""
import os, subprocess, sys, time
from Xlib import display, X, XK
from Xlib.ext import xtest
from PIL import Image
rom, out = sys.argv[1], sys.argv[2]
script = sys.argv[3] if len(sys.argv) > 3 else "4,0.2:Return,3,0.2:Left,2"
os.makedirs(out, exist_ok=True)
mgba = os.path.expanduser('~/.local/opt/mgba.appimage')
proc = subprocess.Popen([mgba, '-3', rom], env=dict(os.environ, DISPLAY=':0'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
d = display.Display(':0'); root = d.screen().root
def find_win(w):
    try:
        name = w.get_wm_name() or ''; cls = w.get_wm_class() or ('', '')
    except Exception: name, cls = '', ('', '')
    if 'mgba' in (name or '').lower() or 'mgba' in ' '.join(cls).lower():
        g = w.get_geometry()
        if g.width > 100: return w
    for c in w.query_tree().children:
        r = find_win(c)
        if r: return r
    return None
def shot(tag, w):
    g = w.get_geometry(); p = w.translate_coords(root, 0, 0)
    x, y = -p.x, -p.y
    img = root.get_image(x, y, g.width, g.height, X.ZPixmap, 0xffffffff)
    im = Image.frombytes('RGB', (g.width, g.height), img.data, 'raw', 'BGRX')
    im.save(os.path.join(out, tag + '.png')); print('saved', tag, im.size)
def key(name):
    w.set_input_focus(X.RevertToParent, X.CurrentTime); d.sync(); time.sleep(0.1)
    kc = d.keysym_to_keycode(XK.string_to_keysym(name))
    xtest.fake_input(d, X.KeyPress, kc); d.sync(); time.sleep(0.08)
    xtest.fake_input(d, X.KeyRelease, kc); d.sync()
w = None
for _ in range(40):
    time.sleep(0.25); w = find_win(root)
    if w: break
if not w: print('mGBA window not found'); proc.kill(); sys.exit(1)
w.set_input_focus(X.RevertToParent, X.CurrentTime); d.sync()
n = 0
for part in script.split(','):
    secs, k = (part.split(':') + [None])[:2]
    if k: key(k)
    time.sleep(float(secs))
    shot(f'{n:02d}_{k or "idle"}', w); n += 1
proc.kill()
