# -*- coding: utf-8 -*-
"""量「结界突破页」的结构判据：浅色面板占比 + 标题分，找能区分所有页面的组合。"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                   # noqa: E402
import vision                                            # noqa: E402
from tasks.jiejie_tupo import ui                         # noqa: E402

# 面板区域：9 宫格外框内的浅色底（避开文字/图标）
PANEL = (205, 195, 1700, 765)
TITLE_REGION = (700, 90, 1200, 180)

cases = [
    ("shots/step2_jiejie.png", "结界突破原图", True),
    ("shots/jj_after_battle.png", "结界突破战后", True),
    ("shots/jj_diag2.png", "结界突破(带横幅/变暗)", True),
    ("shots/jj_panel_open.png", "结界突破+面板", True),
    ("shots/now2.png", "结界突破(不确定)", True),
    ("shots/step1_explore.png", "探索页", False),
    ("shots/diag_explore.png", "庭院", False),
    ("shots/jj_battle_end.png", "胜利画面", False),
    ("shots/jj_refresh_dialog.png", "刷新确认弹窗", True),
]

print(f"{'文件':<26}{'浅色占比':>9}{'面板均值':>9}{'标题分':>8}  期望")
for f, label, is_jj in cases:
    if not os.path.exists(f):
        print(f"{label:<26} (缺文件)")
        continue
    im = Image.open(f).convert("L")
    a = np.asarray(im, dtype=np.float32)
    panel = a[PANEL[1]:PANEL[3], PANEL[0]:PANEL[2]]
    light = float((panel > 120).mean())
    mean = float(panel.mean())
    s, _, _ = vision.match(Image.open(f).convert("RGB"),
                           ui.tpl("t_title_jiejie.png"), region=TITLE_REGION)
    print(f"{label:<26}{light:>9.3f}{mean:>9.1f}{s:>8.3f}  {'结界突破' if is_jj else '其它'}")
