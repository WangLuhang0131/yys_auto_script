# -*- coding: utf-8 -*-
"""按预览图换算出的坐标裁「结界突破」底栏入口模板，并严格验证。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402
import vision                                            # noqa: E402

im = Image.open("shots/explore_user.png").convert("RGB")
S = im.size[0] / 1920.0

# 预览 910 宽 = 基准 320 宽（400~720），比例 2.844
# 预览红框 x 290~540 -> 基准 400 + 290/2.844 = 502 ; 400 + 540/2.844 = 590
# 预览 y 150~400（=基准 y 880 + 150/2.844=933 ~ 880+400/2.844=1021）
BOX = (495, 925, 620, 1005)
b = tuple(int(v * S) for v in BOX)
crop = im.crop(b)
crop.resize((crop.width * 2, crop.height * 2), Image.NEAREST).save("shots/jj_entry_zoom2.png")
TPL = os.path.join("tasks", "jiejie_tupo", "templates", "t_jj_entry_bottom.png")
crop.save(TPL)
print("模板:", crop.size, "取自", b)

REGION = (420, 880, 700, 1040)
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
