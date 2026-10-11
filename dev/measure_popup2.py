# -*- coding: utf-8 -*-
"""用「亮品红像素占比 + 面板浅色占比」组合识别「悬赏封印」弹窗。"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402

# 弹窗右上角 X 的搜索区（1920 基准）
R_X = (1080, 110, 1260, 250)
# 弹窗面板主体
R_PANEL = (450, 210, 1090, 740)


def metrics(path):
    im = Image.open(path).convert("RGB")
    S = im.size[0] / 1920.0
    arr = np.asarray(im, dtype=np.float32)

    bx = tuple(int(v * S) for v in R_X)
    sub = arr[bx[1]:bx[3], bx[0]:bx[2]]
    pink = ((sub[:, :, 0] > 165) & (sub[:, :, 2] > 105) & (sub[:, :, 1] < 145)
            & (sub[:, :, 0] - sub[:, :, 1] > 55))
    pink_ratio = float(pink.mean())

    bp = tuple(int(v * S) for v in R_PANEL)
    sub2 = arr[bp[1]:bp[3], bp[0]:bp[2]]
    g2 = sub2.mean(axis=2)
    light = float((g2 > 165).mean())
    return pink_ratio, light, float(g2.mean())


cases = [
    ("shots/popup_user.png", "有弹窗(用户图)", True),
    ("shots/toast_live.png", "备战页", False),
    ("shots/jj_battle_end2.png", "胜利画面", False),
    ("shots/state_now2.png", "结界突破页", False),
    ("shots/now_after_tap2.png", "结界突破页2", False),
    ("shots/courtyard_clean.png", "庭院", False),
    ("shots/step1_explore.png", "探索页", False),
    ("shots/prep_zero_live.png", "备战页2", False),
    ("shots/popup_battle_user.png", "战斗中(有弹窗)", True),
]
print(f"{'画面':<22}{'粉占比':>9}{'浅色占比':>10}{'均值':>8}  期望")
for f, label, is_popup in cases:
    if not os.path.exists(f):
        continue
    p, l, m = metrics(f)
    print(f"{label:<22}{p:>9.4f}{l:>10.3f}{m:>8.1f}  {'弹窗' if is_popup else '无'}")
