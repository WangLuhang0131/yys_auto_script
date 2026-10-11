# -*- coding: utf-8 -*-
"""诊断：比较 Adb.tap 与直接 input tap，确认点击是否生效。"""
import time
from adbkit import Adb
from game import Game

a = Adb()
g = Game(debug=False)

def state():
    st, info = g.detect()
    return st, info

im = a.screenshot()
im.save("shots/diag_pre.png")
st, info = state()
print("当前状态:", st, info)
print("物理坐标 =", a.screen_xy(1727, 857))

print("\n[1] 直接用 adb shell input tap")
x, y = a.screen_xy(1727, 857)
out = a.shell(f"input tap {x} {y}")
print("   shell 返回:", repr(out))
time.sleep(3)
print("   3 秒后状态:", state())

print("\n[2] 用 Adb.tap()")
a.tap(1727, 857)
time.sleep(3)
print("   3 秒后状态:", state())

print("\n[3] 检查 dumpsys input 最近事件（确认点击是否被系统接收）")
print(a.shell("getevent -c 1 -t 1 2>/dev/null || echo 'getevent 不可用'")[:200])
