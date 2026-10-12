# -*- coding: utf-8 -*-
"""验证 runner 在「设备未就绪」时会等待并给出提示，而不是直接炸。"""
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

import adbkit                                            # noqa: E402
from core.runner import TaskRunner                       # noqa: E402
from core.tasks import discover                          # noqa: E402

# 让 device_state 前 3 次报 offline，之后正常 —— 模拟"重启后等几秒才就绪"
real = adbkit.Adb.device_state
calls = {"n": 0}


def flaky(self):
    calls["n"] += 1
    if calls["n"] <= 3:
        return "offline"
    return real(self)


adbkit.Adb.device_state = flaky

runner = TaskRunner(logdir=os.path.join(_ROOT, "logs"))
tasks = dict(discover())
runner.start(tasks["event_dungeon"](), target_runs=1, shot_mode="color")

t0 = time.time()
seen_wait = False
seen_ready = False
while runner.running and time.time() - t0 < 150:
    for kind, payload in runner.poll():
        if kind == "log":
            print(payload, flush=True)
            if "等它就绪" in payload:
                seen_wait = True
            if "设备就绪" in payload:
                seen_ready = True
        elif kind == "done":
            print("   [结束]", payload, flush=True)
    time.sleep(0.3)
    if seen_wait and seen_ready:
        runner.stop()
        break

adbkit.Adb.device_state = real
print("\n出现等待提示:", seen_wait, "| 出现就绪提示:", seen_ready)
