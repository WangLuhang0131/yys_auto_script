# -*- coding: utf-8 -*-
"""返回后逐帧记录所有判据分数，定位为什么几帧之内识别不出庭院。"""
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

from adbkit import Adb                                    # noqa: E402
from human_click import Human                             # noqa: E402
from core.nav import Returner                             # noqa: E402
import vision                                             # noqa: E402

J = os.path.join("tasks", "jiejie_tupo", "templates")
E = os.path.join("tasks", "event_dungeon", "templates")
a = Adb()
h = Human(a, log=lambda m: None)
r = Returner(a, h, lambda m: None)

print("当前:", r.detect(), flush=True)
if r.detect() == "courtyard":
    h.tap("activity_icon", 1835, 222, note="活动")
    time.sleep(4)
print("去活动页:", r.detect(), flush=True)
time.sleep(3)
print("（已稳定 3 秒）:", r.detect(), flush=True)

print("\n点返回，然后每 0.8 秒记一次分数：", flush=True)
h.tap("back", 57, 42, note="返回")
for i in range(8):
    time.sleep(0.8)
    img = a.screenshot()
    cy, _, _ = vision.match(img, os.path.join(J, "t_courtyard_bar.png"), region=(60, 830, 1880, 1070))
    ov, _, _ = vision.match(img, os.path.join(E, "t_overview.png"), region=(200, 10, 520, 100))
    dt, _, _ = vision.match(img, os.path.join(E, "t_detail.png"), region=(200, 5, 620, 110))
    ch, _, _ = vision.match(img, os.path.join(E, "t_challenge.png"), region=(1640, 790, 1815, 920))
    print(f"  +{(i+1)*0.8:.1f}s  庭院={cy:6.3f} 总览={ov:6.3f} 详情={dt:6.3f} "
          f"挑战键={ch:6.3f}  判定={r.detect(img)}", flush=True)
