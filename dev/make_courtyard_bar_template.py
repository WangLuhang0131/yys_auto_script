# -*- coding: utf-8 -*-
"""做「庭院」识别模板（底部功能栏），并验证它能区分其它页面。

之前 bug：在庭院上把「左上角」当返回键点了，结果点开自己的头像 -> 设置页 -> 卡住。
修法：先认出庭院（这类页面**没有**返回键），就不点那个位置。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402
import vision                                            # noqa: E402

TPL = os.path.join("tasks", "jiejie_tupo", "templates", "t_courtyard_bar.png")
BOX = (120, 875, 1760, 1030)          # 庭院底部功能栏（图鉴…式神录）
Image.open("shots/courtyard_clean.png").convert("RGB").crop(BOX).save(TPL)
print("庭院模板:", Image.open(TPL).size, "取自", BOX)

REGION = (60, 830, 1880, 1070)
cases = [
    ("shots/courtyard_clean.png", "庭院", True),
    ("shots/step1_explore.png", "探索页", False),
    ("shots/state_now2.png", "结界突破页", False),
    ("shots/jj_battle_end.png", "胜利画面", False),
    ("shots/ref_prep.png", "活动备战页", False),
    ("shots/settings_user.png", "设置页(盖在庭院上)", False),
]
c_min, o_max = 9, -9
for f, label, is_court in cases:
    if not os.path.exists(f):
        continue
    im = Image.open(f).convert("RGB")
    s, _, _ = vision.match(im, TPL, region=REGION)
    print("%s%-22s 庭院分=%5.3f 期望=%s"
          % ("OK " if (s >= 0.6) == is_court else "!! ", label, s,
             "庭院" if is_court else "其它"))
    if is_court:
        c_min = min(c_min, s)
    else:
        o_max = max(o_max, s)
print("\n庭院最低=%.3f 其它最高=%.3f -> %s"
      % (c_min, o_max, "可分" if c_min > o_max + 0.15 else "不够分"))
