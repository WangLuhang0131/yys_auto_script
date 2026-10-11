# -*- coding: utf-8 -*-
"""一次性定位探索页底栏「结界突破」入口：
1) 用红色图标做锚点（红底印章很显眼）
2) 按「图标下方是文字」的固定关系推出文字位置
3) 把结果画在图上，人工核对一次
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw                         # noqa: E402

im = Image.open("shots/explore_user.png").convert("RGB")
S = im.size[0] / 1920.0
a = np.asarray(im, dtype=np.float32)

# 红色印章像素（红底白字很亮很红）
red = ((a[:, :, 0] > 170) & (a[:, :, 1] < 100) & (a[:, :, 2] < 100))

# 只看底栏带（基准 y 890~1020）
y1, y2 = int(890 * S), int(1020 * S)
band = red[y1:y2, :]
cols = band.sum(axis=0)
# 找红色列簇
clusters, start = [], None
for i, v in enumerate(cols):
    if v > 3 and start is None:
        start = i
    elif v <= 3 and start is not None:
        if i - start > 8:
            clusters.append((start, i - 1))
        start = None
if start is not None:
    clusters.append((start, len(cols) - 1))

print("底栏红色列簇（基准坐标）：")
for c1, c2 in clusters:
    sub = band[:, c1:c2 + 1]
    rr = np.nonzero(sub.sum(axis=1) > 0)[0]
    yy1, yy2 = y1 + rr.min(), y1 + rr.max()
    print(f"  x {c1/S:6.0f}~{c2/S:6.0f}  y {yy1/S:5.0f}~{yy2/S:5.0f}  "
          f"宽 {(c2-c1)/S:5.0f} 高 {(yy2-yy1)/S:5.0f}")

# 把前 3 个簇标出来看
vis = im.copy()
d = ImageDraw.Draw(vis)
for c1, c2 in clusters[:4]:
    sub = band[:, c1:c2 + 1]
    rr = np.nonzero(sub.sum(axis=1) > 0)[0]
    d.rectangle([c1, y1 + rr.min(), c2, y1 + rr.max()], outline=(0, 255, 0), width=4)
vis.crop((0, int(860 * S), int(1100 * S), int(1040 * S))).save("shots/entry_anchors.png")
print("\n已存 shots/entry_anchors.png（绿框=红印章锚点）")
