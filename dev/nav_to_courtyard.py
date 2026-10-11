# -*- coding: utf-8 -*-
"""导航回庭院主界面并采图（用于做「庭院」识别模板）。

计划：活动总览 -> 返回(到活动详情/总览) -> 返回(庭院)，
每步都存图，最后确认哪张是庭院。
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adbkit import Adb                                   # noqa: E402

a = Adb()
for i in range(1, 5):
    im = a.screenshot()
    im.save(f"shots/nav_step{i}.png")
    print(f"第 {i} 张已存 shots/nav_step{i}.png")
    # 左上返回
    a.shell("input tap 57 42")
    time.sleep(3.0)
im = a.screenshot()
im.save("shots/nav_step5.png")
print("第 5 张已存 shots/nav_step5.png")
