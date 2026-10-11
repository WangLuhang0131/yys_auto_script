# -*- coding: utf-8 -*-
"""用「3 行浅色面板」做结界突破页判据：分别量每行的浅色占比。"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                   # noqa: E402

# 每行面板内部取样条（避开文字与图标）：y 取行中部偏下
ROW_BANDS = [(320, 355), (475, 510), (640, 675)]
X_RANGE = (215, 1690)

cases = [
    ("shots/step2_jiejie.png", "结界突破原图", True),
    ("shots/jj_after_battle.png", "结界突破战后", True),
    ("shots/jj_diag2.png", "结界突破+横幅遮挡", True),
    ("shots/jj_panel_open.png", "结界突破+面板遮挡", True),
    ("shots/now2.png", "结界突破(旧)", True),
    ("shots/jj_refresh_dialog.png", "结界突破+确认弹窗", True),
    ("shots/step1_explore.png", "探索页", False),
    ("shots/diag_explore.png", "庭院", False),
    ("shots/jj_battle_end.png", "胜利画面", False),
    ("shots/ref_prep.png", "活动备战页", False),
]

print(f"{'文件':<24}{'行1':>7}{'行2':>7}{'行3':>7}{'亮行数':>7}  期望")
for f, label, is_jj in cases:
    if not os.path.exists(f):
        print(f"{label:<24}(缺)")
        continue
    a = np.asarray(Image.open(f).convert("L"), dtype=np.float32)
    fracs = []
    for y1, y2 in ROW_BANDS:
        band = a[y1:y2, X_RANGE[0]:X_RANGE[1]]
        fracs.append(float((band > 120).mean()))
    bright_rows = sum(1 for v in fracs if v > 0.45)
    print(f"{label:<24}{fracs[0]:>7.2f}{fracs[1]:>7.2f}{fracs[2]:>7.2f}{bright_rows:>7}  "
          f"{'结界突破' if is_jj else '其它'}")
