# -*- coding: utf-8 -*-
"""给探索页的「结界突破」入口做模板（底栏那个，实测 x≈470~660）。

教训：原来写死 (870,440)，结果点到了**旁边的「式神委派」**（x≈720~850）。
相邻按钮只差 ~90 像素，坐标不可靠，必须按图找。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402
import vision                                            # noqa: E402

SRC = "shots/explore_user.png"
im = Image.open(SRC).convert("RGB")
S = im.size[0] / 1920.0
print("参考图", im.size, "缩放", round(S, 3))

# 底栏「结界突破」：基准 x 470~665, y 915~1000
BOX = (465, 910, 670, 1005)
b = tuple(int(v * S) for v in BOX)
crop = im.crop(b)
crop.resize((crop.width * 2, crop.height * 2), Image.NEAREST).save("shots/jj_entry_zoom.png")
TPL = os.path.join("tasks", "jiejie_tupo", "templates", "t_jj_entry_bottom.png")
crop.save(TPL)
print("模板:", crop.size, "取自", b)

# 验证
REGION = (380, 860, 820, 1050)
print("\n=== 模板验证 ===")
for f, label, expect_high in [(SRC, "探索页(底栏)", True),
                              ("shots/step1_explore.png", "探索页2", True),
                              ("shots/courtyard_clean.png", "庭院", False),
                              ("shots/state_now2.png", "结界突破页", False)]:
    if not os.path.exists(f):
        continue
    s, x, y = vision.match(Image.open(f).convert("RGB"), TPL, region=REGION)
    print(f"  {label:14s} 分数 {s:5.3f} 位置 ({x},{y})  "
          f"{'OK' if (s >= 0.6) == expect_high else '!!'}")

# 顺便确认「式神委派」区域与它不是同一个东西：把式神委派也裁出来对比
BOX2 = (700, 910, 870, 1005)
b2 = tuple(int(v * S) for v in BOX2)
im.crop(b2).resize(((b2[2]-b2[0]), (b2[3]-b2[1]))).save("shots/wrong_entry_zoom.png")
print("\n已存 shots/wrong_entry_zoom.png（应该被点到的那个=式神委派）")
