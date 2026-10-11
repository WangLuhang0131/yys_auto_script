# -*- coding: utf-8 -*-
"""采样点右移避开深色头像，重新找格子判据的干净分界。"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402
from tasks.jiejie_tupo import ui                         # noqa: E402

# 已知真值：
#   state_now2.png（0/30）：只有格9 可打（文木亮格），其余全部已攻破
#   step2_jiejie.png（旧图）：格5,6,7,8,9 可打
TRUTH = {
    "shots/state_now2.png": [9],
    "shots/step2_jiejie.png": [5, 6, 7, 8, 9],
    "shots/jj_clean_state.png": [4, 7, 9],
}

for dx, hw in ((95, 55), (120, 50), (140, 45)):
    print(f"\n=== 采样 格心+({dx},0) 半宽 {hw} 半高 18 ===")
    for f, ok_cells in TRUTH.items():
        im = Image.open(f).convert("L")
        m = float(np.asarray(im, dtype=np.float32).mean())
        vals = []
        for i, (cx, cy) in enumerate(ui.GRID_CENTERS, 1):
            a = np.asarray(im.crop((cx + dx - hw, cy - 18, cx + dx + hw, cy + 18)),
                           dtype=np.float32)
            vals.append(a.mean() / max(m, 1.0))
        got = [i for i, v in enumerate(vals, 1) if v > 1.15]
        print(f"  {os.path.basename(f):24s} 真值={ok_cells} 判出={got} "
              f"{'OK' if got == ok_cells else '!!'}")
        print("     比值: " + " ".join(f"{v:.2f}" for v in vals))
