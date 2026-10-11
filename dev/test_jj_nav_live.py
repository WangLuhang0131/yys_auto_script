# -*- coding: utf-8 -*-
"""实机验证：从庭院启动结界突破导航，确认能正确点到底栏「结界突破」入口。

重点看：是否还点到「式神委派」。导航成功后立即停止任务。
"""
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

LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 70
a = Adb()
r = Returner(a, Human(a, log=lambda m: None), lambda m: None)
print("起点:", r.detect(), flush=True)

runner = TaskRunner(logdir="logs")
tasks = dict(discover())
runner.start(tasks["jiejie_tupo"](), target_runs=1, shot_mode="color")

t0 = time.time()
while runner.running and time.time() - t0 < LIMIT:
    for kind, payload in runner.poll():
        if kind == "log":
            print(payload, flush=True)
        elif kind == "progress":
            print("   [进度]", payload, flush=True)
        elif kind == "done":
            print("   [结束]", payload, flush=True)
    time.sleep(0.3)

runner.stop()
time.sleep(3)
print("\n当前页面:", r.detect(), flush=True)
a.screenshot().save("shots/after_nav_test.png")
print("已存 shots/after_nav_test.png")
