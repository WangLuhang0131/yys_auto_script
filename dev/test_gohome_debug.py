# -*- coding: utf-8 -*-
"""在任务刚结束时立刻调用 go_home（复现 runner 的场景），并逐步记录。"""
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

from adbkit import Adb                                    # noqa: E402
from human_click import Human                             # noqa: E402
from core.nav import Returner                             # noqa: E402
from core.runner import TaskRunner                        # noqa: E402
from core.tasks import discover                           # noqa: E402

a = Adb()
h = Human(a, log=lambda m: None)
r = Returner(a, h, print)

# 先跑一个很短的失败任务，让游戏停在活动页（模拟刚跑完的状态）
print("=== 先跑任务，把游戏停到活动页 ===", flush=True)
runner = TaskRunner(logdir=os.path.join(_ROOT, "logs"))
tasks = dict(discover())
runner.start(tasks["event_dungeon"](), target_runs=1, shot_mode="color")
t0 = time.time()
while runner.running and time.time() - t0 < 120:
    for kind, payload in runner.poll():
        if kind == "log" and ("任务完成" in payload or "回庭院" in payload):
            print("   ", payload, flush=True)
    time.sleep(0.3)
time.sleep(2)

print("\n=== 现在手动调 go_home，逐步看 ===", flush=True)
ok, steps = r.go_home()
print(f"\n结果: ok={ok} steps={steps}  当前页面={r.detect()}", flush=True)
