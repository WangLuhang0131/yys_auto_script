# -*- coding: utf-8 -*-
"""扫描整屏右侧，定位「0/30 / 7/30」数字的真实位置。"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402

for label, path in (("券空(0/30)", "shots/ticket_real_zero.png"),
                    ("券够(7/30)", "shots/ticket_now.png")):
    im = Image.open(path).convert("L")
    g = np.asarray(im, dtype=np.float32)
    # 只看右侧上方，且要求是「亮且细」的文字：亮度 >180
    sub = g[10:110, 1200:1920]
    mask = sub > 180
    cols = mask.sum(axis=0)
    segs, start = [], None
    for i, v in enumerate(cols):
        if v > 0 and start is None:
            start = i
        elif v == 0 and start is not None:
            segs.append((1200 + start, 1200 + i - 1))
            start = None
    if start is not None:
        segs.append((1200 + start, 1200 + len(cols) - 1))
    print(f"\n{label} ({path})  阈值>180")
    for a1, a2 in segs:
        if a2 - a1 + 1 < 3:
            continue
        m = mask[:, a1 - 1200:a2 - 1200 + 1]
        rr = np.nonzero(m.sum(axis=1) > 0)[0]
        h = int(rr.max() - rr.min() + 1) if len(rr) else 0
        ys = 10 + rr.min() if len(rr) else -1
        ye = 10 + rr.max() if len(rr) else -1
        print(f"  x {a1:5d}~{a2:5d} 宽 {a2-a1+1:3d} 高 {h:3d} y {ys}~{ye} 亮 {int(m.sum()):5d}")
