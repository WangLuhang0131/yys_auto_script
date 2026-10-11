# -*- coding: utf-8 -*-
"""带调试落盘的循环测试：每次状态判定都保存截图与判据。"""
import time, os
import numpy as np
from game import Game
import vision

os.makedirs("shots/dbg", exist_ok=True)
g = Game(debug=False, verbose=True)
SEQ = [0]

def probe(tag):
    """截一帧，打印所有判据，并保存。"""
    SEQ[0] += 1
    img = g.a.screenshot()
    p = f"shots/dbg/{SEQ[0]:03d}_{tag}.png"
    img.save(p)
    s_prep, x, y = vision.match(img, "t_challenge.png", region=g.__dict__.get("R", (1640, 790, 1815, 920)))
    from game import R_CHALLENGE, R_OVERVIEW_TITLE, R_DETAIL_TITLE, R_CHALLENGE_LUM
    s_prep, _, _ = vision.match(img, "t_challenge.png", region=R_CHALLENGE)
    s_ov, _, _ = vision.match(img, "t_overview.png", region=R_OVERVIEW_TITLE)
    s_dt, _, _ = vision.match(img, "t_detail.png", region=R_DETAIL_TITLE)
    lum = vision.brightness(img, R_CHALLENGE_LUM)
    print(f"  {tag:22s} prep={s_prep:.3f} ov={s_ov:.3f} dt={s_dt:.3f} lum={lum:6.1f}  -> {p}", flush=True)
    return img

print("=== 第 1 轮 ===")
probe("t0_before")
g.a.tap(1727, 857)
t0 = time.time()
while time.time() - t0 < 45:
    time.sleep(0.6)
    probe("t%05.1f" % (time.time() - t0))
