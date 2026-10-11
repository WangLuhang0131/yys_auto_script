# -*- coding: utf-8 -*-
"""在多张结界突破截图上验证突破券解析。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402
from tasks.jiejie_tupo import attack as atk              # noqa: E402

FILES = ["shots/ticket_now.png", "shots/jj_clean_state.png", "shots/step2_jiejie.png",
         "shots/jj_after_battle.png", "shots/jj_state4.png"]

for f in FILES:
    if not os.path.exists(f):
        continue
    im = Image.open(f).convert("RGB")
    info = atk.ticket_info(im)
    print("%-26s 斜杠宽=%s 左数宽=%s 左数位置=%s 判定券用完=%s"
          % (os.path.basename(f), info["slash_w"], info["left_w"],
             info["left_x"], info["almost_out"]))
