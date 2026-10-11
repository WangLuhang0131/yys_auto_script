# -*- coding: utf-8 -*-
"""坐标系实测：用左上「返回」按钮(横屏 60,45)做探针，判定 adb input 用哪套坐标。"""
import time
from adbkit import Adb
from game import Game

a = Adb()
g = Game(debug=False)

def st():
    s, i = g.detect()
    return s

CAND = {
    "identity(60,45)": (60, 45),
    "portrait(1034,60)": (1034, 60),
    "swap(45,60)": (45, 60),
    "mirror-x(1020,45)": (1020, 45),
    "mirror-y(60,1035)": (60, 1035),
}

print("初始状态:", st())
for name, (x, y) in CAND.items():
    print(f"\n>>> 试 {name}")
    a.shell(f"input tap {x} {y}")
    time.sleep(3.5)
    s = st()
    print(f"    3.5 秒后状态 = {s}")
    if s != "prep":
        print(f"    !! 命中！坐标系为 {name}")
        break
    # 若状态变了再退回来
else:
    print("所有候选都没反应")

a.screenshot().save("shots/coord_test_end.png")
