# -*- coding: utf-8 -*-
"""给「悬赏封印」弹窗做识别模板 + X 号点击点。

特征：
  · 弹窗右上有个亮粉色 X（约 1920 基准 (1160,176)）
  · 弹窗主体是大片浅米色面板
两者组合判断，既能识别又能拿到点击点。
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402
import vision                                            # noqa: E402

u = Image.open("shots/popup_user.png").convert("RGB")
S = u.size[0] / 1920.0

# 基准坐标下的 X 号区域
BOX = (1120, 135, 1205, 220)
box_user = tuple(int(v * S) for v in BOX)
crop = u.crop(box_user)
crop.resize((crop.width * 3, crop.height * 3), Image.NEAREST).save("shots/popup_x_zoom.png")
print("X 模板候选:", crop.size, "取自用户图", box_user)

arr = np.asarray(crop, dtype=np.float32)
g = arr.mean(axis=2)
pink = ((arr[:, :, 0] > 170) & (arr[:, :, 2] > 110) & (arr[:, :, 1] < 140)
        & (arr[:, :, 0] - arr[:, :, 1] > 60))
print(f"  该区 均值 {g.mean():.1f} 亮>180 占比 {(g>180).mean():.3f} 粉色占比 {pink.mean():.3f}")

TPL = os.path.join("tasks", "event_dungeon", "templates", "t_popup_x.png")
crop.save(TPL)
print("已存为模板:", TPL)

# 在用户图上验证：模板分数
REGION = (1080, 100, 1260, 260)
s, x, y = vision.match(u, TPL, region=REGION)
print(f"\n用户图自匹配: 分数 {s:.3f} 位置 ({x},{y})")

# 对照：无弹窗画面
print("\n对照（应低分）:")
for f, label in (("shots/toast_live.png", "备战页"),
                 ("shots/jj_battle_end2.png", "胜利画面"),
                 ("shots/state_now2.png", "结界突破页"),
                 ("shots/courtyard_clean.png", "庭院")):
    if not os.path.exists(f):
        continue
    s2, _, _ = vision.match(Image.open(f).convert("RGB"), TPL, region=REGION)
    print(f"  {label:12s} 分数 {s2:.3f}")

# 顺便量「弹窗面板」区域（大块浅色）
print("\n弹窗面板区域（基准 440~1100, 200~750）亮度:")
for f, label in (("shots/popup_user.png", "有弹窗"), ("shots/jj_battle_end2.png", "胜利画面"),
                 ("shots/toast_live.png", "备战页")):
    if not os.path.exists(f):
        continue
    im2 = Image.open(f).convert("L")
    S2 = im2.size[0] / 1920.0
    b = tuple(int(v * S2) for v in (440, 200, 1100, 750))
    sub = np.asarray(im2.crop(b), dtype=np.float32)
    print(f"  {label:12s} 均值 {sub.mean():6.1f} 亮>170 占比 {(sub>170).mean():.3f}")
