# -*- coding: utf-8 -*-
"""对比「备战页 / 战斗场景 / 结束画面」在不同区域的灰度差异，找出可靠判据。"""
import numpy as np
from PIL import Image

REGIONS = {
    "左上返回箭头": (20, 15, 130, 80),
    "顶部中央横幅": (500, 0, 1500, 60),
    "左下自动按钮": (20, 890, 140, 1030),
    "右下挑战键": (1655, 800, 1800, 910),
    "底部中央金句": (780, 1000, 1140, 1065),
    "右侧头像列": (1700, 150, 1800, 620),
    "左侧说明区": (30, 160, 460, 300),
    "底部中央整体": (600, 950, 1300, 1080),
}

FILES = {
    "备战页(now)": "shots/now_state.png",
    "备战页(prep_a)": "shots/prep_a.png",
    "战斗12s": "shots/end_2.png",
    "战斗32s": "shots/after_battle.png",
    "结束画面(cand_1)": "shots/cand_1.png",
    "活动总览": "shots/prep_c.png",
}

imgs = {k: Image.open(v).convert("RGB") for k, v in FILES.items()}

print(f"{'区域':<14}" + "".join(f"{k:>17}" for k in imgs))
for rname, box in REGIONS.items():
    row = f"{rname:<14}"
    for k, im in imgs.items():
        a = np.asarray(im.crop(box).convert("L"), dtype=np.float32)
        row += f"{a.mean():>17.1f}"
    print(row)

print()
print("=== 金色文字像素数（底部中央 780-1140 x 1000-1065）===")
for k, im in imgs.items():
    x = np.asarray(im.crop((780, 1000, 1140, 1065)), dtype=np.float32)
    gold = ((x[:, :, 0] > 165) & (x[:, :, 1] > 130) & (x[:, :, 2] < 175) & (x[:, :, 0] - x[:, :, 2] > 40))
    print(f"{k:<20} gold_px={int(gold.sum()):6d}  面积占比={gold.mean():.4f}")
