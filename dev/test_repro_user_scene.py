# -*- coding: utf-8 -*-
"""模拟用户的失败场景：adb 服务停掉 + 游戏开着，然后用 GUI 的同一套代码跑任务。

同时每 2 秒独立记录一次 adb 状态，这样能看出"哪一刻 devices 是空的"。
"""
import os
import subprocess
import sys
import threading
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

import adbkit                                            # noqa: E402
from core.runner import TaskRunner                       # noqa: E402
from core.tasks import discover                          # noqa: E402

ADB = adbkit.ADB
print("adb:", ADB, flush=True)

print("\n=== 1) 停掉 adb 服务，做成你重启后的状态 ===", flush=True)
subprocess.run([ADB, "kill-server"], capture_output=True)
time.sleep(0.5)
p = subprocess.run([ADB, "devices"], capture_output=True, text=True, errors="replace")
print("   立刻 devices:", p.stdout.strip().replace("\n", " | "), flush=True)

# 后台每 2 秒记录一次设备状态（用独立 adb 调用，不干扰主流程的判定）
monitor_stop = threading.Event()
records = []


def monitor():
    while not monitor_stop.is_set():
        try:
            q = subprocess.run([ADB, "devices"], capture_output=True, text=True,
                               errors="replace", timeout=20)
            line = [l for l in q.stdout.splitlines()[1:] if l.strip()]
            records.append((round(time.time() - t_start, 1),
                            line[0].strip() if line else "(空)"))
        except Exception as e:
            records.append((round(time.time() - t_start, 1), f"异常 {e}"))
        monitor_stop.wait(2)


print("\n=== 2) 启动任务（同时后台监控设备）===", flush=True)
t_start = time.time()
threading.Thread(target=monitor, daemon=True).start()

runner = TaskRunner(logdir=os.path.join(_ROOT, "logs"))
tasks = dict(discover())
runner.start(tasks["event_dungeon"](), target_runs=1, shot_mode="color")

while runner.running and time.time() - t_start < 150:
    for kind, payload in runner.poll():
        if kind == "log":
            print(payload, flush=True)
        elif kind == "done":
            print("   [结束]", payload, flush=True)
    time.sleep(0.3)

monitor_stop.set()
time.sleep(0.5)
print("\n=== 3) 后台监控记录（时间秒 -> 第一行设备）===", flush=True)
for t, line in records:
    print(f"   {t:6.1f}s  {line}", flush=True)
print("\n最终页面:", flush=True)
from core.nav import Returner                            # noqa: E402
from human_click import Human                            # noqa: E402
a = adbkit.Adb()
print("  ", Returner(a, Human(a, log=lambda m: None), lambda m: None).detect(), flush=True)
