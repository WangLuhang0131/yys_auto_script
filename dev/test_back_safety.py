# -*- coding: utf-8 -*-
"""检查回庭院的点击安全性：活动页连续点返回会不会弹"退出游戏"确认框。"""
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

from adbkit import Adb                                    # noqa: E402
from human_click import Human                             # noqa: E402
from core.nav import Returner                             # noqa: E402

a = Adb()
h = Human(a, log=print)
r = Returner(a, h, print)

print("当前页面:", r.detect(), flush=True)

# 去活动总览
if r.detect() == "courtyard":
    h.tap("activity_icon", 1835, 222, note="活动")
    time.sleep(4)
print("去活动后:", r.detect(), flush=True)

# 反复点返回，看每次页面怎么变（会不会出现确认框）
for i in range(5):
    img = a.screenshot()
    # 用"中央暗像素"粗略判断有没有弹窗（资料页/设置页/确认框都会变暗）
    from core.nav import warn_pixels
    print(f"  第{i+1}次点击前: 页面={r.detect()} 中央暗像素={warn_pixels(img)}", flush=True)
    h.tap("back", 57, 42, note="返回")
    time.sleep(2.5)

img = a.screenshot()
img.save("shots/after_multi_back.png")
from core.nav import warn_pixels
print("\n最终: 页面=%s 中央暗像素=%d" % (r.detect(), warn_pixels(img)), flush=True)
print("已存 shots/after_multi_back.png 供人工核对", flush=True)
