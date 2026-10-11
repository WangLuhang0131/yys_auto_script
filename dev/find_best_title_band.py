# -*- coding: utf-8 -*-
"""给「结界突破」标题模板找最稳的裁剪带。"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                   # noqa: E402
import vision                                            # noqa: E402

JJ = ["shots/step2_jiejie.png", "shots/jj_after_battle.png", "shots/jj_diag2.png",
      "shots/jj_panel_open.png", "shots/now2.png"]
NO = ["shots/step1_explore.png", "shots/diag_explore.png", "shots/jj_battle_end.png"]

src = Image.open("shots/step2_jiejie.png").convert("RGB")
tmp = os.path.join(tempfile.gettempdir(), "cand_title.png")

for y1, y2 in [(110, 145), (112, 140), (115, 145), (108, 148), (100, 140), (120, 150)]:
    src.crop((840, y1, 1085, y2)).save(tmp)
    reg = (700, max(0, y1 - 5), 1200, y2 + 25)
    jj_scores = [vision.match(Image.open(f).convert("RGB"), tmp, region=reg)[0] for f in JJ]
    no_scores = [vision.match(Image.open(f).convert("RGB"), tmp, region=reg)[0] for f in NO]
    smin, smax = min(jj_scores), max(no_scores)
    verdict = "可分" if smin > smax + 0.15 else "不可分"
    print("裁剪 y%d-%d: 结界突破最低=%.3f 其它最高=%.3f  %s"
          % (y1, y2, smin, smax, verdict))
    print("     结界突破各图:", [round(v, 3) for v in jj_scores])
    print("     其它各图    :", [round(v, 3) for v in no_scores])
