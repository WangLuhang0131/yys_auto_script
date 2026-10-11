# -*- coding: utf-8 -*-
"""确定各点击目标的安全抖动范围（从真实截图中量出按钮边界）。"""
import numpy as np
from PIL import Image

def save(f, out):
    Image.open(f).convert("RGB").save(out)
    print("saved", out)

# 用当前画面重新采集参考图
from adbkit import Adb
a = Adb()
a.screenshot().save("shots/ref_prep.png")
print("已采集备战页 shots/ref_prep.png")

im = np.asarray(Image.open("shots/ref_prep.png").convert("L"), dtype=np.float32)

def bright_box(box, tag, th=150):
    x1, y1, x2, y2 = box
    sub = im[y1:y2, x1:x2]
    mask = sub > th
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        print(f"{tag}: 无亮像素")
        return
    print(f"{tag}: 亮像素范围 x {x1+xs.min()}~{x1+xs.max()}  y {y1+ys.min()}~{y1+ys.max()}  "
          f"数量 {mask.sum()}  占比 {mask.mean():.3f}")

print("\n=== 备战页「挑战」键区域 (1620,760)-(1850,960) 亮像素(金边+文字) ===")
bright_box((1620, 760, 1860, 970), "挑战键")
print("\n=== 备战页「自动」/下方按钮 ===")
bright_box((20, 880, 200, 1040), "自动按钮区", th=120)
print("\n=== 备战页右下小按钮行 (秘宝/协战/队伍预设/式神录) ===")
bright_box((1100, 740, 1650, 860), "小按钮行", th=140)
