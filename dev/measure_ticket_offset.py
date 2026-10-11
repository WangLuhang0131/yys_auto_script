# -*- coding: utf-8 -*-
"""量准：门票图标模板中心 -> 门票数字区的偏移，别再用左上角当锚点。"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402
import vision                                            # noqa: E402

TPL_DIR = os.path.join("tasks", "event_dungeon", "templates")
ICON = os.path.join(TPL_DIR, "t_ticket_icon.png")
ZERO = os.path.join(TPL_DIR, "t_ticket_zero.png")
iz = Image.open(ICON).size
zz = Image.open(ZERO).size
print("图标模板尺寸:", iz, "-> 中心偏移 (w/2, h/2) =", (iz[0] // 2, iz[1] // 2))
print("0 模板尺寸:", zz)


def load(f):
    im = Image.open(f).convert("RGB")
    if im.size != (1920, 1080):
        im = im.resize((1920, 1080), Image.LANCZOS)
    return im


print("\n=== 各画面里图标与门票0模板的实际位置 ===")
for f in ("shots/prep_zero_live.png", "shots/toast_live.png",
          "shots/prep_300_live.png", "shots/ref_prep.png"):
    if not os.path.exists(f):
        continue
    im = load(f)
    si, ix, iy = vision.match(im, ICON, region=(1020, 10, 1340, 95))
    s0, zx, zy = vision.match(im, ZERO, region=(1100, 10, 1400, 95))
    print(f"  {os.path.basename(f):24s} 图标分 {si:.3f} 中心({ix},{iy}) | "
          f"0模板分 {s0:.3f} 中心({zx},{zy})")
    if si > 0.7 and s0 > 0.7:
        print(f"      -> 数字中心相对图标中心的偏移 = ({zx-ix}, {zy-iy})")

# 用「门票0」那张反推数字区的真实范围
im0 = load("shots/prep_zero_live.png")
g = np.asarray(im0.convert("L"), dtype=np.float32)
band = g[20:90, 1100:1400]
mask = band > 170
cols = np.nonzero(mask.sum(axis=0) > 0)[0]
print("\n门票0 那张：数字亮像素横向范围 x",
      1100 + cols.min(), "~", 1100 + cols.max())
