# -*- coding: utf-8 -*-
"""找到 MuMu 窗口 -> 置前获得焦点 -> 再点返回键，看是否恢复响应。"""
import ctypes
import os
import subprocess
import sys
import time

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
    pid = ctypes.c_ulong()
    u.GetWindowThreadProcessId(h, ctypes.byref(pid))
    found.append((h, b.value, pid.value))
    return True


u.EnumWindows(cb, None)

target = None
for h, t, pid in found:
    out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True).stdout.strip()
    proc = out.split('","')[0].strip('"') if out else "?"
    if t.startswith("MuMu"):
        print(f"hwnd={h} proc={proc} title={t!r}")
        if target is None:
            target = (h, t, proc)

if not target:
    print("没找到 MuMu 窗口")
    sys.exit(1)

h, t, proc = target
print(f"\n>>> 把 {proc} / {t!r} 置前")
u.ShowWindow(h, 9)          # SW_RESTORE
u.SetForegroundWindow(h)
time.sleep(1.5)

a = Adb()
before = a.grab_land(None, raw=False)
print("点返回 (57,42) ...")
a.shell("input tap 57 42")
time.sleep(3.5)
after = a.grab_land(None, raw=False)
after.save(r"D:\Program Files\WKSPC\yys\shots\focus_tap_after.png")

import numpy as np  # noqa: E402
d = np.abs(np.asarray(before.convert("L"), dtype=np.int16)
           - np.asarray(after.convert("L"), dtype=np.int16))
print(f"画面变化: 平均 {d.mean():.2f}  变化像素 {(d>40).sum()}")
