# -*- coding: utf-8 -*-
"""用户整屏图是 2729x1536（非 1920x1080），按坐标映射定位券数区域再量。

目的：量出「0/30」里那个 0 的宽度，看是否 ≥ 现有阈值 17px（换算到 1920 基准）。
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402

im = Image.open("shots/ticket_0of30_screen.png").convert("RGB")
W, H = im.size
sx, sy = W / 1920.0, H / 1080.0
print(f"图尺寸 {im.size}，相对 1920x1080 的缩放 {sx:.3f} x {sy:.3f}")

g = np.asarray(im.convert("L"), dtype=np.float32)

# 在「右上角」适当放大的范围里找字形，避免依赖精确映射
y1, y2 = int(10 * sy), int(90 * sy)
x1, x2 = int(1550 * sx), int(1900 * sx)
sub = g[y1:y2, x1:x2]
mask = sub > 150
cols = mask.sum(axis=0)
segs, start = [], None
for i, v in enumerate(cols):
    if v > 0 and start is None:
        start = i
    elif v == 0 and start is not None:
        segs.append((x1 + start, x1 + i - 1))
        start = None
if start is not None:
    segs.append((x1 + start, x1 + len(cols) - 1))

print(f"\n搜索区 x{x1}~{x2} y{y1}~{y2} 的字形段（原始像素）：")
raw = []
for a1, a2 in segs:
    m = mask[:, a1 - x1:a2 - x1 + 1]
    rr = np.nonzero(m.sum(axis=1) > 0)[0]
    h = int(rr.max() - rr.min() + 1) if len(rr) else 0
    raw.append((a1, a2, a2 - a1 + 1, h))
    print(f"  x {a1}~{a2} 宽 {a2-a1+1:4d} 高 {h:4d}"
          f"   换算到1920基准: x{a1/sx:.0f}~{a2/sx:.0f} 宽{(a2-a1+1)/sx:.1f} 高{h/sy:.1f}")

im.crop((max(0, x1 - 20), y1, min(W, x2 + 20), y2)).resize(
    (int((x2 - x1 + 40) * 1.5), int((y2 - y1) * 1.5))).save("shots/ticket_0of30_zoom.png")
print("\n已保存 shots/ticket_0of30_zoom.png")
