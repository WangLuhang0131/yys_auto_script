# -*- coding: utf-8 -*-
"""完整跑一遍：导入检查 -> 任务发现 -> 实跑任务 -> 看是否正常。"""
import os
import sys
import time
import traceback

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

print("=== 1) 全部模块导入检查 ===", flush=True)
mods = ["adbkit", "vision", "human_click", "ascii_out",
        "core.tasks", "core.runner", "core.nav", "core.popup_watch", "core.paths",
        "tasks.event_dungeon.task", "tasks.event_dungeon.game",
        "tasks.jiejie_tupo.task", "tasks.jiejie_tupo.attack", "tasks.jiejie_tupo.ui"]
bad = []
for m in mods:
    try:
        __import__(m)
        print(f"  OK  {m}", flush=True)
    except Exception as e:
        bad.append(m)
        print(f"  !!  {m} -> {type(e).__name__}: {e}", flush=True)
        traceback.print_exc()
if bad:
    print("导入失败，先修这些:", bad)
    sys.exit(1)

print("\n=== 2) 任务发现 ===", flush=True)
import core
for name, cls in core.discover():
    print(f"  {name}: {cls().name}", flush=True)

print("\n=== 3) 实跑活动副本任务（目标 2 次）===", flush=True)
from core.runner import TaskRunner
from core.nav import Returner
from adbkit import Adb
from human_click import Human

a = Adb()
r = Returner(a, Human(a, log=lambda m: None), lambda m: None)
print("  出发前页面:", r.detect(), flush=True)

runner = TaskRunner(logdir=os.path.join(_ROOT, "logs"))
tasks = dict(core.discover())
runner.start(tasks["event_dungeon"](), target_runs=2, shot_mode="color")

t0 = time.time()
while runner.running and time.time() - t0 < 300:
    for kind, payload in runner.poll():
        if kind == "log":
            print(payload, flush=True)
        elif kind == "progress":
            print("   [进度]", payload, flush=True)
        elif kind == "done":
            print("   [结束]", payload, flush=True)
    time.sleep(0.3)

print("\n=== 4) 结束页面:", r.detect(), flush=True)
