# -*- coding: utf-8 -*-
"""标定阵容锁定判据。

用用户给的两张裁剪图（图1 未锁定 / 图2 已锁定）量出「金色边框」的差别，
再在实机整屏截图上核对位置。
"""
import glob
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402

ATT = os.path.join(os.environ.get("USERPROFILE", ""), ".dsh", "attachments", "v1", "objects")
CAND = {
    "图1_未锁定": os.path.join(ATT, "eb", "ebb086e8165c307810044aaadc3260ca9f34e1121e8eeb2ea017c5f9f9c21e41"),
    "图2_已锁定": os.path.join(ATT, "33", "33c59bdbc22d91627d7eee4079a216546d34ffbd9dc736ca757edcb705ac1395"),
}


def gold_metrics(im, box=None):
    a = np.asarray(im.crop(box) if box else im, dtype=np.float32)
    g = a.mean(axis=2)
    gold = ((a[:, :, 0] > 140) & (a[:, :, 1] > 110) & (a[:, :, 2] < 150)
            & (a[:, :, 0] - a[:, :, 2] > 45))
    return {
        "mean": round(float(g.mean()), 1),
        "bright>120": round(float((g > 120).mean()), 3),
        "bright>160": round(float((g > 160).mean()), 3),
        "gold": round(float(gold.mean()), 3),
        "mean_rgb": tuple(round(float(v)) for v in a.reshape(-1, 3).mean(axis=0)),
    }


print("=== 用户提供的两张裁剪图 ===")
for label, path in CAND.items():
    if not os.path.exists(path):
        print(f"{label}: 找不到 {path}")
        continue
    im = Image.open(path).convert("RGB")
    print(f"{label}  尺寸{im.size}  {gold_metrics(im)}")
    im.resize((im.width * 3, im.height * 3), Image.NEAREST).save(f"shots/{label}_zoom.png")

print("\n=== 实机整屏截图里的『阵容』图标区（当前应为已锁定）===")
for f in ("shots/lock_state_now.png", "shots/jj_clean_state.png", "shots/step2_jiejie.png"):
    if not os.path.exists(f):
        continue
    im = Image.open(f).convert("RGB")
    print(f"{os.path.basename(f):26s} {gold_metrics(im, (1230, 845, 1330, 920))}")
