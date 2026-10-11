# -*- coding: utf-8 -*-
"""验证运行器的自动收尾：跑一个小任务，看结束后是否自动回庭院。"""
import os
import sys
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

from core.runner import TaskRunner            # noqa: E402
from core.tasks import discover               # noqa: E402
from core.nav import Returner                 # noqa: E402
from adbkit import Adb                        # noqa: E402
from humanize import Human                    # noqa: E402

LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 120

# 先把游戏带到「结界突破页」，模拟任务结束时的状态
a = Adb()
h = Human(a)
r = Returner(a, h, print)
print("起点:", r.detect(), flush=True)
if r.detect() == "courtyard":
    a.shell("input tap 1123 350")          # 探索
    time.sleep(3.5)
if r.detect() == "explore":
    a.shell("input tap 870 440")           # 结界突破
    time.sleep(3.5)
print("出发前状态:", r.detect(), flush=True)

tasks = dict(discover())
runner = TaskRunner(logdir="logs")
ok, err = runner.start(tasks["jiejie_tupo"](), target_runs=1, shot_mode="color")
print(f"启动任务: {ok} {err}（{LIMIT}s 后强制停止）\n", flush=True)

t0 = time.time()
while runner.running and time.time() - t0 < LIMIT + 90:
    for kind, payload in runner.poll():
        if kind == "log":
            print(payload, flush=True)
        elif kind == "progress":
            print("   [进度]", payload, flush=True)
        elif kind == "done":
            print("   [结束]", payload, flush=True)
    if runner.running and time.time() - t0 > LIMIT:
        runner.stop()
    time.sleep(0.3)

print("\n最终页面:", r.detect(), flush=True)
