# -*- coding: utf-8 -*-
"""完全复刻 runner 的收尾流程，把每一步看到什么全打出来。"""
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

from adbkit import Adb                                    # noqa: E402
from human_click import Human                             # noqa: E402
from core.nav import Returner, TAP_BACK                   # noqa: E402
from core.runner import TaskRunner                        # noqa: E402
from core.tasks import discover                           # noqa: E402

a = Adb()
h = Human(a, log=lambda m: None)
r = Returner(a, h, print)

runner = TaskRunner(logdir=os.path.join(_ROOT, "logs"))
tasks = dict(discover())
runner.start(tasks["event_dungeon"](), target_runs=1, shot_mode="color")
t0 = time.time()
while runner.running and time.time() - t0 < 150:
    for kind, payload in runner.poll():
        if kind == "log" and ("收尾" in payload or "回庭院" in payload):
            print("  runner:", payload, flush=True)
    time.sleep(0.3)

print("\n=== runner 自己的收尾已经跑完了，现在手工重放一遍 ===", flush=True)
time.sleep(1)
print("此刻 detect() =", r.detect(), flush=True)

# 如果还在活动页，手工点一次返回，然后每 0.6 秒看一次
page = r.detect()
if page == "activity":
    print("点一次返回...", flush=True)
    h.tap("back", *TAP_BACK, note="返回")
    for i in range(12):
        time.sleep(0.6)
        p = r.detect()
        print(f"  +{(i+1)*0.6:.1f}s detect={p}", flush=True)
        if p == "courtyard":
            break
