# -*- coding: utf-8 -*-
"""给「结界突破页」找一个更稳的判据：用「刷新」按钮模板（位置固定、不会被遮挡）。"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402
import vision                                            # noqa: E402

TPL = os.path.join("tasks", "jiejie_tupo", "templates", "t_refresh_btn.png")
Image.open("shots/where_now.png").convert("RGB").crop((1440, 820, 1700, 910)).save(TPL)
print("刷新按钮模板:", Image.open(TPL).size)

REGION = (1380, 780, 1780, 950)
cases = [
    ("shots/where_now.png", "结界突破 0/30", True),
    ("shots/ticket_now.png", "结界突破 7/30", True),
    ("shots/step2_jiejie.png", "结界突破 初始", True),
    ("shots/jj_after_battle.png", "结界突破 战后", True),
    ("shots/now_after_tap2.png", "结界突破+面板", True),
    ("shots/step1_explore.png", "探索页", False),
    ("shots/diag_explore.png", "庭院", False),
    ("shots/jj_battle_end.png", "胜利画面", False),
    ("shots/ref_prep.png", "活动备战页", False),
    ("shots/jj_state4.png", "队伍准备画面", False),
]
jj_min, no_max = 9, -9
for f, label, is_jj in cases:
    if not os.path.exists(f):
        continue
    s, _, _ = vision.match(Image.open(f).convert("RGB"), TPL, region=REGION)
    print("%s%-20s 刷新按钮分=%5.3f  期望=%s"
          % ("OK " if (s >= 0.6) == is_jj else "!! ", label, s,
             "结界突破" if is_jj else "其它"))
    if is_jj:
        jj_min = min(jj_min, s)
    else:
        no_max = max(no_max, s)
print("\n结界突破最低=%.3f 其它最高=%.3f -> %s"
      % (jj_min, no_max, "可分" if jj_min > no_max + 0.15 else "不够分"))
