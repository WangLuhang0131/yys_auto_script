# -*- coding: utf-8 -*-
"""实测打包后的 exe：从"adb 服务没跑"的冷启动状态开始跑任务，看会不会炸。

复现用户的场景：游戏开着、MuMu 开着，但 adb 服务没跑（重启后就是这样）。
"""
import os
import subprocess
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

ADB = r"E:\MuMuPlayer\nx_main\adb.exe"
EXE = os.path.join(_ROOT, "release", "阴阳师脚本控制台_文件夹版",
                   "阴阳师脚本控制台_文件夹版.exe")

print("=== 1) 把 adb 服务停掉，做出冷启动状态 ===", flush=True)
subprocess.run([ADB, "kill-server"], capture_output=True)
time.sleep(1)
p = subprocess.run([ADB, "devices"], capture_output=True, text=True, errors="replace")
print("   第一次 devices:", " | ".join(p.stdout.strip().splitlines()), flush=True)
p = subprocess.run([ADB, "devices"], capture_output=True, text=True, errors="replace")
print("   第二次 devices:", " | ".join(p.stdout.strip().splitlines()), flush=True)

print("\n=== 2) 现在跑 exe 的自检（它会调 adb 截图）===", flush=True)
logf = os.path.join(os.path.dirname(EXE), "selftest.log")
if os.path.exists(logf):
    os.remove(logf)
subprocess.run([EXE, "--selftest"], cwd=os.path.dirname(EXE), timeout=180)
time.sleep(2)
if os.path.exists(logf):
    with open(logf, encoding="utf-8", errors="replace") as f:
        for line in f.read().splitlines():
            if any(k in line for k in ("adb", "自检", "no-window")):
                print("   ", line, flush=True)
else:
    print("   !! 没有 selftest.log", flush=True)

print("\n=== 3) 再确认一次设备状态 ===", flush=True)
p = subprocess.run([ADB, "devices"], capture_output=True, text=True, errors="replace")
print("   ", " | ".join(p.stdout.strip().splitlines()))
