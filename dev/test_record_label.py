# -*- coding: utf-8 -*-
"""用「攻破记录」标签做结界突破页判据（它位置靠下，不会被顶部横幅遮挡）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                   # noqa: E402
import vision                                            # noqa: E402

TPL = os.path.join("tasks", "jiejie_tupo", "templates", "t_record_label.png")
BOX = (245, 762, 400, 815)          # 结界突破原图里的「攻破记录」四个字
Image.open("shots/step2_jiejie.png").convert("RGB").crop(BOX).save(TPL)
print("模板:", Image.open(TPL).size, "来源", BOX)

REGION = (200, 730, 470, 850)
cases = [
    ("shots/step2_jiejie.png", "结界突破原图", True),
    ("shots/jj_after_battle.png", "结界突破战后", True),
    ("shots/jj_diag2.png", "结界突破+横幅", True),
    ("shots/jj_panel_open.png", "结界突破+面板", True),
    ("shots/now2.png", "结界突破(旧)", True),
    ("shots/jj_refresh_dialog.png", "结界突破+弹窗", True),
    ("shots/step1_explore.png", "探索页", False),
    ("shots/diag_explore.png", "庭院", False),
    ("shots/jj_battle_end.png", "胜利画面", False),
    ("shots/ref_prep.png", "活动备战页", False),
]
jj_min, no_max = 9.0, -9.0
for f, label, is_jj in cases:
    if not os.path.exists(f):
        print(f"{label}: 缺文件")
        continue
    im = Image.open(f).convert("RGB")
    s, _, _ = vision.match(im, TPL, region=REGION)
    print("%s%-22s 分数=%5.3f  期望=%s" % ("OK " if (s >= 0.5) == is_jj else "!! ",
                                           label, s, "结界突破" if is_jj else "其它"))
    if is_jj:
        jj_min = min(jj_min, s)
    else:
        no_max = max(no_max, s)
print("\n结界突破最低分=%.3f  其它最高分=%.3f  ->  %s"
      % (jj_min, no_max, "可分" if jj_min > no_max + 0.1 else "不够分"))
