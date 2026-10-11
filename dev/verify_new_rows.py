# -*- coding: utf-8 -*-
"""用新行心验证格子判据（真实 0/30 画面里只有第 9 格是可打的）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402
from tasks.jiejie_tupo import attack as atk              # noqa: E402

for f in ("shots/state_now2.png", "shots/step2_jiejie.png"):
    im = Image.open(f).convert("RGB")
    print(f"\n{f}")
    for i, c in enumerate(atk.scan_cells(im), 1):
        tag = "可打" if c[4] else "已攻破"
        print(f"  格{i}: 亮度 {c[2]:6.1f} 比值 {c[3]:.2f}  {tag}")
