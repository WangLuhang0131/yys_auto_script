# -*- coding: utf-8 -*-
"""验证：截图彻底失败时，报错信息是否说清了"设备掉线"而不是只报 PIL 认不出。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import adbkit                                            # noqa: E402

a = adbkit.Adb()
print("真实设备状态:", a.device_state())

print("\n=== 1) 正常时 screenshot 可用 ===")
im = a.screenshot()
print("   ", im.size, im.mode)

print("\n=== 2) 模拟「设备掉线」时的报错（关键：要能看懂）===")
# 把会拖时间的自愈等待缩短，只验证文案
real_state = a.device_state


def fake_offline():
    return "offline"


a.device_state = fake_offline
a.wait_online_after_fail = lambda log=None: False      # 假设自愈也没成功
try:
    raise RuntimeError(a._explain_shot_failure("png", "cannot identify image file"))
except RuntimeError as e:
    print("   报错内容:", e)

print("\n=== 3) 设备在线但截图偶发失败时的报错 ===")
a.device_state = lambda: "device"
try:
    raise RuntimeError(a._explain_shot_failure("png", "cannot identify image file"))
except RuntimeError as e:
    print("   报错内容:", e)

print("\n=== 4) self-heal 全套（真实调用，会重启 adb）===")
a.device_state = real_state
a.wait_online_after_fail = real_state and adbkit.Adb.wait_online_after_fail.__get__(a)
ok = a.wait_online_after_fail(log=print)
print("   恢复到 device 状态:", ok, "| 当前:", a.device_state())
