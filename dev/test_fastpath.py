# -*- coding: utf-8 -*-
"""验证快速判据（只看底部区域）与整屏判定是否一致。

关键假设：备战页的「挑战」和结束画面的「点击屏幕继续」都在底部区域，
因此轮询时只需截取底部 190px，可显著提速。
"""
import time
import numpy as np
from adbkit import Adb
from game import R_CHALLENGE, R_END_TEXT
import vision

a = Adb()
BOX = (0, 890, 1920, 1080)

full = a.screenshot()
part = a.grab_land(BOX)
ref = full.crop(BOX)
d = np.abs(np.asarray(part, dtype=np.int16) - np.asarray(ref, dtype=np.int16))
print(f"底部区域一致性: 最大差={d.max()} 平均差={d.mean():.3f}")

for name, box in (("挑战键(整屏区)", R_CHALLENGE), ("结束文字(整屏区)", R_END_TEXT)):
    b = (box[0], box[1] - BOX[1], box[2], box[3] - BOX[1])
    s_full, _, _ = vision.match(full, "t_challenge.png" if "挑战" in name else "end_text.png",
                                region=box,
                                mask_path=None if "挑战" in name else "end_text_mask.png")
    s_part, _, _ = vision.match(part, "t_challenge.png" if "挑战" in name else "end_text.png",
                                region=b,
                                mask_path=None if "挑战" in name else "end_text_mask.png")
    print(f"{name}: 整屏={s_full:.3f}  底部区域={s_part:.3f}")

ts = []
for _ in range(5):
    t = time.time(); p = a.grab_land(BOX)
    s1, _, _ = vision.match(p, "t_challenge.png", region=(1640, 790 - 890, 1815, 920 - 890))
    s2, _, _ = vision.match(p, "end_text.png", region=(700, 960 - 890, 1230, 1080 - 890),
                            mask_path="end_text_mask.png")
    ts.append(time.time() - t)
print("底部区域「双判据」单次耗时:", [f"{x*1000:.0f}ms" for x in ts])
print("当前画面判据: prep=%.3f end=%.3f" % (s1, s2))
