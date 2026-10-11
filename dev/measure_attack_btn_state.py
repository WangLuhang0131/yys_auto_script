# -*- coding: utf-8 -*-
"""量「进攻」按钮：金色（可点） vs 灰色（券不足不可点）的亮度差。

灰色按钮中心区（实测按钮大致 x 1470~1650, y 930~1010）
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402

# 用模板匹配找到按钮位置后再采样中心，避免面板移动带来的偏差
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import vision                                            # noqa: E402
from tasks.jiejie_tupo import ui                         # noqa: E402

cases = [
    ("灰色(券不足, 现在)", "shots/now_after_tap2.png"),
    ("金色(券够, 之前)", "shots/jj_panel_open.png"),
    ("金色(用户0/30那张)", "shots/ticket_0of30_screen.png"),
]

for label, path in cases:
    im = Image.open(path).convert("RGB")
    s, x, y = vision.match(im, ui.tpl("t_attack_btn.png"), region=ui.R_ATTACK_SEARCH)
    scale = im.size[0] / 1920.0
    g = np.asarray(im.convert("L"), dtype=np.float32)
    # 按钮中心 60x30
    cw, ch = int(30 * scale), int(15 * scale)
    box = (int(x - cw), int(y - ch), int(x + cw), int(y + ch))
    patch = g[box[1]:box[3], box[0]:box[2]]
    rgb = np.asarray(im.crop(box), dtype=np.float32).reshape(-1, 3).mean(axis=0)
    print(f"{label:22s} 按钮分={s:.3f} 中心位置=({x},{y}) "
          f"中心亮度 均值{patch.mean():6.1f} 最大{patch.max():5.0f} "
          f"亮>150占比 {(patch>150).mean():.3f} 平均色 {tuple(round(float(v)) for v in rgb)}")
