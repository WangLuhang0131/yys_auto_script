# -*- coding: utf-8 -*-
"""确认：启动任务后，看门狗线程确实在跑；任务结束后线程被回收。

不实机等弹窗（悬赏封印协作取消后只出现一次），只验证线程生命周期。
"""
import os
import sys
import threading
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

from core.runner import TaskRunner            # noqa: E402
from core.tasks import discover               # noqa: E402


def threads():
    return [t.name for t in threading.enumerate()]


tasks = dict(discover())
runner = TaskRunner(logdir="logs")
print("启动前线程:", threads(), flush=True)

# 用「不限次数」的方式跑活动任务：进去就会被"次数为0"判据停掉，很快结束
runner.start(tasks["event_dungeon"](), target_runs=1, shot_mode="color")
print("已启动任务", flush=True)

started = False
t0 = time.time()
while runner.running and time.time() - t0 < 120:
    names = threads()
    if "popup-watcher" in names and not started:
        started = True
        print(">>> 看门狗线程已存在:", names, flush=True)
    for kind, payload in runner.poll():
        if kind == "log" and "看门狗" in payload:
            print(payload, flush=True)
        elif kind == "done":
            print("  [结束]", payload, flush=True)
    time.sleep(0.2)

time.sleep(1.5)
print("\n任务结束后线程:", threads())
print("看门狗是否成功启动过:", started)
print("看门狗是否已回收:", "popup-watcher" not in threads())
