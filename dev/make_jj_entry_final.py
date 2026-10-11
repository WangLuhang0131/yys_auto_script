# -*- coding: utf-8 -*-
"""按刻度图标定的位置裁「结界突破」入口模板（图标 x 500~650, y 940~1045）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402
import vision                                            # noqa: E402

base = Image.open("shots/explore_user.png").convert("RGB").resize((1920, 1080), Image.LANCZOS)

BOX = (496, 940, 655, 1042)          # 图标 + 文字（按刻度图确认）
crop = base.crop(BOX)
crop.resize((crop.width * 3, crop.height * 3), Image.NEAREST).save("shots/jj_entry_final_zoom.png")
TPL = os.path.join("tasks", "jiejie_tupo", "templates", "t_jj_entry_bottom.png")
crop.save(TPL)
print("模板:", crop.size, "取自", BOX, "-> 中心约",
      (BOX[0] + crop.width // 2, BOX[1] + crop.height // 2))
# 用完删掉旧的纯文字模板，避免混淆
old = os.path.join("tasks", "jiejie_tupo", "templates", "t_jj_entry_text.png")
if os.path.exists(old):
    os.remove(old)
    print("已删除旧的 t_jj_entry_text.png")

REGION = (430, 900, 720, 1070)
print("\n=== 验证 ===")
for f, label, expect_high in [("shots/explore_user.png", "探索页(用户图)", True),
                              ("shots/step1_explore.png", "探索页2", True),
                              ("shots/courtyard_clean.png", "庭院", False),
                              ("shots/state_now2.png", "结界突破页", False),
                              ("shots/prep_zero_live.png", "备战页", False)]:
    if not os.path.exists(f):
        continue
    img = Image.open(f).convert("RGB")
    if img.size != (1920, 1080):
        img = img.resize((1920, 1080), Image.LANCZOS)
    s, x, y = vision.match(img, TPL, region=REGION)
    good = (s >= 0.6) == expect_high
    print(f"{'OK ' if good else '!! '}{label:16s} 分数 {s:5.3f} 位置 ({x},{y})")
