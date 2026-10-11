# -*- coding: utf-8 -*-
"""采集结界突破页的「加成」「刷新」两个界面，用于确认阵容锁定和刷新行为。"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from adbkit import Adb  # noqa: E402

a = Adb()
base = r"D:\Program Files\WKSPC\yys\shots"


def snap(name):
    im = a.grab_land(None, raw=False)
    p = os.path.join(base, name + ".png")
    im.save(p)
    print("saved", p, im.size)
    return im


print("=== 点左上「加成」 ===")
a.shell("input tap 88 60")
time.sleep(2.5)
snap("jj_jiacheng")

print("=== 点「刷新」 ===")
a.shell("input tap 1540 855")
time.sleep(3.0)
snap("jj_after_refresh")

print("=== 再点一次「加成」看是否关闭 ===")
a.shell("input tap 88 60")
time.sleep(2.0)
snap("jj_after_jiacheng2")
