# -*- coding: utf-8 -*-
"""任务刚结束后，连续抓帧 + 打印各判据分数，把"被误判成 activity 的庭院帧"存图。"""
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
import vision                                             # noqa: E402

J = os.path.join("tasks", "jiejie_tupo", "templates")
E = os.path.join("tasks", "event_dungeon", "templates")
a = Adb()
h = Human(a, log=lambda m: None)
r = Returner(a, h, lambda m: None)

runner = TaskRunner(logdir=os.path.join(_ROOT, "logs"))
tasks = dict(discover())
runner.start(tasks["event_dungeon"](), target_runs=1, shot_mode="color")
t0 = time.time()
while runner.running and time.time() - t0 < 150:
    runner.poll()
    time.sleep(0.3)

# runner 收尾完成后，连续抓 25 帧找误判
print("=== 任务结束后连续抓帧（找被误判成 activity 的庭院帧）===", flush=True)
saved = 0
for i in range(25):
    img = a.screenshot()
    cy, _, _ = vision.match(img, os.path.join(J, "t_courtyard_bar.png"),
                            region=(60, 830, 1880, 1070))
    ov, _, _ = vision.match(img, os.path.join(E, "t_overview.png"), region=(200, 10, 520, 100))
    dt, _, _ = vision.match(img, os.path.join(E, "t_detail.png"), region=(200, 5, 620, 110))
    ch, _, _ = vision.match(img, os.path.join(E, "t_challenge.png"), region=(1640, 790, 1815, 920))
    page = r.detect(img)
    flag = ""
    if cy > 0.6 and page == "activity":
        flag = "  <<< 庭院分高却判成 activity！"
        p = f"shots/misjudge_{saved}.png"
        img.save(p)
        saved += 1
        flag += f" 已存 {p}"
    print(f"  帧{i+1:2d}: 庭院={cy:6.3f} 总览={ov:6.3f} 详情={dt:6.3f} 挑战={ch:6.3f} "
          f"判定={page}{flag}", flush=True)
    if saved:
        break
    time.sleep(0.5)
print("共存下", saved, "张误判帧", flush=True)
