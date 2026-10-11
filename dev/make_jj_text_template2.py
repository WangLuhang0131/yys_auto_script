# -*- coding: utf-8 -*-
"""按锚点图确认的位置裁「结界突破」文字模板（基准 x 500~620, y 982~1016）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402
import vision                                            # noqa: E402

im = Image.open("shots/explore_user.png").convert("RGB")
S = im.size[0] / 1920.0

BOX = (498, 980, 624, 1020)
b = tuple(int(v * S) for v in BOX)
crop = im.crop(b)
crop.resize((crop.width * 3, crop.height * 3), Image.NEAREST).save("shots/jj_text_zoom2.png")
TPL = os.path.join("tasks", "jiejie_tupo", "templates", "t_jj_entry_text.png")
crop.save(TPL)
print("文字模板:", crop.size, "取自", b)

REGION = (440, 930, 700, 1050)
print("\n=== 验证 ===")
for f, label, expect_high in [("shots/explore_user.png", "探索页(用户图)", True),
                              ("shots/step1_explore.png", "探索页2", True),
                              ("shots/courtyard_clean.png", "庭院", False),
                              ("shots/state_now2.png", "结界突破页", False),
                              ("shots/prep_zero_live.png", "备战页", False)]:
    if not os.path.exists(f):
        continue
    s, x, y = vision.match(Image.open(f).convert("RGB"), TPL, region=REGION)
    good = (s >= 0.6) == expect_high
    print(f"{'OK ' if good else '!! '}{label:16s} 分数 {s:5.3f} 位置 ({x},{y})")
