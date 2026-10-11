# -*- coding: utf-8 -*-
"""正确处理带 alpha 的截图：按白底合成后再量数字。"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402

p = "shots/ticket_0of30_screen.png"
im = Image.open(p)
print("模式:", im.mode, "尺寸:", im.size)

if im.mode in ("RGBA", "LA", "P"):
    im = im.convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    im = Image.alpha_composite(bg, im)
    print("已按白底合成")

g_im = im.convert("L")
g = np.asarray(g_im, dtype=np.float32)
print(f"整屏亮度: 均值 {g.mean():.1f} 最大 {g.max():.0f}")

X1, Y1, X2, Y2 = 2260, 25, 2680, 110
sub = g[Y1:Y2, X1:X2]
print(f"\n券数区 {X1},{Y1}-{X2},{Y2}: 均值 {sub.mean():.1f} 最大 {sub.max():.0f} "
      f"p95={np.percentile(sub,95):.0f}")

th = float(np.percentile(sub, 97))
print(f"阈值 = p97 = {th:.0f}")
mask = sub > th
cols = mask.sum(axis=0)
segs, start = [], None
for i, v in enumerate(cols):
    if v > 1 and start is None:
        start = i
    elif v <= 1 and start is not None:
        segs.append((X1 + start, X1 + i - 1))
        start = None
if start is not None:
    segs.append((X1 + start, X1 + len(cols) - 1))

print("字形段:")
for a1, a2 in segs:
    if a2 - a1 + 1 < 4:
        continue
    m = mask[:, a1 - X1:a2 - X1 + 1]
    rr = np.nonzero(m.sum(axis=1) > 0)[0]
    h = int(rr.max() - rr.min() + 1) if len(rr) else 0
    print(f"  x {a1:5d}~{a2:5d} 宽 {a2-a1+1:4d} 高 {h:4d} 亮 {int(m.sum()):6d}")

g_im.crop((X1, Y1, X2, Y2)).resize(((X2 - X1) * 2, (Y2 - Y1) * 2), Image.NEAREST).save(
    "shots/user_digits_zoom.png")
print("\n已保存 shots/user_digits_zoom.png")
