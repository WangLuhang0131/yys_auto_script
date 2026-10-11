# -*- coding: utf-8 -*-
"""真机跑一次「结界突破」任务：限时自动停止，打印实时日志。"""
import os
import sys
import threading
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

from core.runner import TaskRunner          # noqa: E402
from core.tasks import discover             # noqa: E402

LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 150

tasks = dict(discover())
r = TaskRunner(logdir="logs")
ok, err = r.start(tasks["jiejie_tupo"](), target_runs=1, shot_mode="color")
print(f"启动: {ok} {err}  限时 {LIMIT}s\n", flush=True)


def stopper():
    time.sleep(LIMIT)
    if r.running:
        print(f"\n>>> 到 {LIMIT}s，发送停止请求", flush=True)
        r.stop()


threading.Thread(target=stopper, daemon=True).start()

t0 = time.time()
while r.running and time.time() - t0 < LIMIT + 30:
    for kind, payload in r.poll():
        if kind == "log":
            print(payload, flush=True)
        elif kind == "progress":
            s, t, note = payload
            print(f"   [进度] {note} ({s}/{t})", flush=True)
        elif kind == "done":
            print(f"   [结束] {payload}", flush=True)
    time.sleep(0.3)

for kind, payload in r.poll():
    print(kind, payload, flush=True)
print("日志文件:", r.logpath)
