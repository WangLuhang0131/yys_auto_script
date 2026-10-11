# -*- coding: utf-8 -*-
"""诊断：为什么结界突破页点不动。
依次尝试：① 把 MuMu 窗口置前 ② input touchscreen tap ③ input swipe 模拟长按 ④ mouse tap
每步都量化画面变化。"""
import ctypes
import os
import subprocess
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from adbkit import Adb  # noqa: E402

u = ctypes.windll.user32
found = []


@ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
def cb(h, l):
    if not u.IsWindowVisible(h):
        return True
    n = u.GetWindowTextLengthW(h)
    if n == 0:
        return True
    b = ctypes.create_unicode_buffer(n + 1)
    u.GetWindowTextW(h, b, n + 1)
    found.append((h, b.value))
    return True


u.EnumWindows(cb, None)
mumu = [w for w in found if w[1].startswith("MuMu")]
print("MuMu 窗口:", mumu)

a = Adb()
TARGET = (900, 300)          # 名字/进度圈区域


def change(before, tag, wait=3.0):
    time.sleep(wait)
    im = a.grab_land(None, raw=False)
    d = np.abs(np.asarray(before.convert("L"), dtype=np.int16)
               - np.asarray(im.convert("L"), dtype=np.int16))
    n = int((d > 40).sum())
    print(f"   {tag:34s} 变化像素 = {n:6d}   {'<<< 有反应' if n > 20000 else ''}")
    if n > 20000:
        im.save(r"D:\Program Files\WKSPC\yys\shots\jj_panel_found_now.png")
    return im


print("\n① 先把 MuMu 窗口置前")
for h, t in mumu:
    u.ShowWindow(h, 9)
    u.SetForegroundWindow(h)
time.sleep(1.5)

base = a.grab_land(None, raw=False)
print("\n② 普通 input tap")
a.shell(f"input tap {TARGET[0]} {TARGET[1]}")
base = change(base, "input tap")

print("\n③ input touchscreen tap")
a.shell(f"input touchscreen tap {TARGET[0]} {TARGET[1]}")
base = change(base, "input touchscreen tap")

print("\n④ input swipe（模拟按下-抬起，120ms）")
a.shell(f"input swipe {TARGET[0]} {TARGET[1]} {TARGET[0]} {TARGET[1]} 120")
base = change(base, "input swipe 120ms")

print("\n⑤ input mouse tap")
a.shell(f"input mouse tap {TARGET[0]} {TARGET[1]}")
base = change(base, "input mouse tap")

print("\n⑥ 回到 MuMu 窗口内点击（窗口坐标换算，先看窗口位置）")
for h, t in mumu:
    from ctypes import wintypes
    r = wintypes.RECT()
    u.GetWindowRect(h, ctypes.byref(r))
    print(f"   窗口 {t!r}: left={r.left} top={r.top} w={r.right-r.left} h={r.bottom-r.top}")
