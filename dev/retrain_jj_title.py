# -*- coding: utf-8 -*-
"""重做「结界突破」标题模板（避开顶部横幅遮挡区），并验证判定。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                   # noqa: E402
import vision                                            # noqa: E402
from tasks.jiejie_tupo import ui                         # noqa: E402

BOX = (840, 118, 1085, 152)          # 只取标题上缘，避免被顶部横幅遮住
src = Image.open("shots/step2_jiejie.png").convert("RGB")
tpl_path = os.path.join("tasks", "jiejie_tupo", "templates", "t_title_jiejie.png")
src.crop(BOX).save(tpl_path)
print("新标题模板:", Image.open(tpl_path).size, "来源区域", BOX)

REGION = (700, 90, 1200, 180)
cases = [
    ("shots/step2_jiejie.png", "结界突破原图", True),
    ("shots/jj_after_battle.png", "结界突破战后", True),
    ("shots/jj_diag2.png", "结界突破(带横幅)", True),
    ("shots/jj_panel_open.png", "结界突破+面板", True),
    ("shots/step1_explore.png", "探索页", False),
    ("shots/diag_explore.png", "庭院", False),
    ("shots/jj_battle_end.png", "胜利画面", False),
]
ok_all = True
for f, label, expect in cases:
    im = Image.open(f).convert("RGB")
    s, _, _ = vision.match(im, ui.tpl("t_title_jiejie.png"), region=REGION)
    good = (s >= 0.55) == expect
    ok_all &= good
    print("%s%-20s 标题分=%5.3f 期望=%s" % ("OK " if good else "!! ", label, s,
                                            "高" if expect else "低"))
print("全部通过" if ok_all else "有不符合的")
