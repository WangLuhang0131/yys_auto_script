# -*- coding: utf-8 -*-
"""实测自愈：先杀掉 adb 服务（模拟刚重启电脑），再启动任务，看能否自动恢复。

这是这次 bug 的核心场景：重启电脑后直接点执行任务。
"""
import os
import subprocess
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

ADB = r"E:\MuMuPlayer\nx_main\adb.exe"
print("=== 1) 杀掉 adb 服务，模拟刚重启 ===", flush=True)
subprocess.run([ADB, "kill-server"], capture_output=True)
time.sleep(1)
out = subprocess.run([ADB, "devices"], capture_output=True, text=True).stdout
print("   devices:", out.strip().replace("\n", " | "), flush=True)

print("\n=== 2) 立刻启动任务（以前这一步会炸）===", flush=True)
from core.runner import TaskRunner            # noqa: E402
from core.tasks import discover               # noqa: E402

runner = TaskRunner(logdir=os.path.join(_ROOT, "logs"))
tasks = dict(discover())
runner.start(tasks["event_dungeon"](), target_runs=1, shot_mode="color")

t0 = time.time()
while runner.running and time.time() - t0 < 150:
    for kind, payload in runner.poll():
        if kind == "log":
            print(payload, flush=True)
        elif kind == "done":
            print("   [结束]", payload, flush=True)
    time.sleep(0.3)

print("\n=== 3) 结束后设备状态 ===", flush=True)
out = subprocess.run([ADB, "devices"], capture_output=True, text=True).stdout
print("   ", out.strip().replace("\n", " | "))
