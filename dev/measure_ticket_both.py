# -*- coding: utf-8 -*-
"""放宽搜索区，把「0/30」和「7/30」两种真实画面都完整量出来，定最终判据。"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adbkit import Adb                                   # noqa: E402
from PIL import Image                                    # noqa: E402

# 券够时的真实截图（此前 adb 抓的）
OLD = "shots/ticket_now.png"

a = Adb()
now = a.screenshot()
now.save("shots/ticket_real_zero.png")
print("现在（应为 0/30）已保存 shots/ticket_real_zero.png")

# 放宽：x 1600~1900, y 15~90
BOX = (1600, 15, 1900, 90)


def segments(im, th=150):
    g = np.asarray(im.convert("L"), dtype=np.float32)
    sub = g[BOX[1]:BOX[3], BOX[0]:BOX[2]]
    mask = sub > th
    cols = mask.sum(axis=0)
    segs, start = [], None
    for i, v in enumerate(cols):
        if v > 0 and start is None:
            start = i
        elif v == 0 and start is not None:
            segs.append((BOX[0] + start, BOX[0] + i - 1))
            start = None
    if start is not None:
        segs.append((BOX[0] + start, BOX[0] + len(cols) - 1))
    out = []
    for x1, x2 in segs:
        m = mask[:, x1 - BOX[0]:x2 - BOX[0] + 1]
        rr = np.nonzero(m.sum(axis=1) > 0)[0]
        h = int(rr.max() - rr.min() + 1) if len(rr) else 0
        out.append((x1, x2, x2 - x1 + 1, h, int(m.sum())))
    return out


for label, path in (("券够(7/30)", OLD), ("券空(0/30)", "shots/ticket_real_zero.png")):
    im = Image.open(path).convert("RGB")
    segs = segments(im)
    print(f"\n{label}  {path}")
    for s in segs:
        print(f"  x {s[0]:5d}~{s[1]:5d} 宽 {s[2]:3d} 高 {s[3]:3d} 亮 {s[4]:5d}")
    im.crop(BOX).resize(((BOX[2]-BOX[0])*3, (BOX[3]-BOX[1])*3), Image.NEAREST).save(
        f"shots/ticket_cmp_{'zero' if '0/30' in label else 'seven'}.png")
