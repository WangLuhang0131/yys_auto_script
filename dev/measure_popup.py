# -*- coding: utf-8 -*-
"""量「悬赏封印」干扰弹窗的特征，为独立看门狗线程定判据。

用户截图（2729x1536，缩放 1.421）：
  · 弹窗右上角有个亮粉色 X，中心约 (1490, 226) -> 1920 基准约 (1048, 159)
  · 弹窗主体是浅米色面板，中央约 (850, 520) -> 基准约 (598, 366)
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402

S = 2729 / 1920.0


def load(p):
    return Image.open(p).convert("L"), Image.open(p).convert("RGB")


print("=== 用户截图（有弹窗）===")
g, rgb = load("shots/popup_user.png")
a = np.asarray(rgb, dtype=np.float32)
gl = np.asarray(g, dtype=np.float32)

# X 号区域（基准 1020~1085, 130~190）
box = tuple(int(v * S) for v in (1015, 128, 1090, 195))
sub = a[box[1]:box[3], box[0]:box[2]]
pink = ((sub[:, :, 0] > 180) & (sub[:, :, 2] > 120) & (sub[:, :, 1] < 150))
print(f"X 号区 {box}: 均值 {sub.mean():.1f} 亮>180 {(sub.mean(axis=2)>180).mean():.3f} "
      f"粉色占比 {pink.mean():.3f}")

# 弹窗面板区域（基准 440~1100, 200~750）
box2 = tuple(int(v * S) for v in (440, 200, 1100, 750))
sub2 = gl[box2[1]:box2[3], box2[0]:box2[2]]
print(f"弹窗主体 {box2}: 均值 {sub2.mean():.1f} 亮>170 占比 {(sub2>170).mean():.3f}")

print("\n=== 对照：没有弹窗的战斗画面 ===")
for f, label in (("shots/jj_battle_end2.png", "胜利画面"),
                 ("shots/now_after_tap2.png", "结界突破页")):
    if not os.path.exists(f):
        continue
    g2, rgb2 = load(f)
    a2 = np.asarray(rgb2, dtype=np.float32)
    gl2 = np.asarray(g2, dtype=np.float32)
    box = (1015, 128, 1090, 195)
    sub = a2[box[1]:box[3], box[0]:box[2]]
    pink = ((sub[:, :, 0] > 180) & (sub[:, :, 2] > 120) & (sub[:, :, 1] < 150))
    box2 = (440, 200, 1100, 750)
    sub2 = gl2[box2[1]:box2[3], box2[0]:box2[2]]
    print(f"{label:12s} X区亮>180 {(sub.mean(axis=2)>180).mean():.3f} 粉占比 {pink.mean():.3f} "
          f"| 中央区均值 {sub2.mean():6.1f} 亮>170 占比 {(sub2>170).mean():.3f}")
