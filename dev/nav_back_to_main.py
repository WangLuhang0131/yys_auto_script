# -*- coding: utf-8 -*-
"""导航回活动页，便于验证任务。步骤：确定刷新 -> 返回探索 -> 返回庭院 -> 点「活动」。"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from adbkit import Adb  # noqa: E402

a = Adb()
base = r"D:\Program Files\WKSPC\yys\shots"


def snap(name):
    im = a.grab_land(None, raw=False)
    im.save(os.path.join(base, name + ".png"))
    return im


print("1) 点弹窗「确定」刷新结界")
a.shell("input tap 1090 662")
time.sleep(4)
snap("nav1_after_confirm")

print("2) 左上返回（回探索页）")
a.shell("input tap 57 42")
time.sleep(3.5)
snap("nav2_explore")

print("3) 左上返回（回庭院）")
a.shell("input tap 57 42")
time.sleep(3.5)
im = snap("nav3_courtyard")
print("   已保存 nav3_courtyard.png")
