# -*- coding: utf-8 -*-
"""重做「门票次数为 0」的判据：先定位门票图标，再看它右边的数字区。

原来的做法错在哪：
  · 模板区域是死坐标 (1180,15,1330,85)，而且阈值卡得离命中分很近；
  · 截图里备战页顶栏有两组「图标 + 数字」：
      左：卷轴图标 + 门票次数（这里 300）
      右：「五倍」图标 + 五倍券（这里 0）
    幸好模板搜索区没覆盖到右边那组，但容错太小，稍有偏移就会误判。
新做法：
  · 用「门票图标」模板定位（图标特征强，比数字稳），
  · 图标右边固定偏移处就是门票数字区，
  · 那个区域当前只有一个数字「0」时才判为用尽。
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402
import vision                                            # noqa: E402

BASE = Image.open("shots/prep_300_live.png").convert("RGB").resize((1920, 1080), Image.LANCZOS)
ZERO = Image.open("shots/prep_zero_live.png").convert("RGB").resize((1920, 1080), Image.LANCZOS)

TPL_DIR = os.path.join("tasks", "event_dungeon", "templates")

# 1) 门票图标模板（截图里在 x 1060~1102，往上取整一带）
ICON_BOX = (1050, 20, 1115, 85)
BASE.crop(ICON_BOX).save(os.path.join(TPL_DIR, "t_ticket_icon.png"))
BASE.crop(ICON_BOX).resize((65 * 3, 65 * 3), Image.NEAREST).save("shots/ticket_icon_zoom.png")
print("门票图标模板:", (ICON_BOX[2] - ICON_BOX[0], ICON_BOX[3] - ICON_BOX[1]), "取自", ICON_BOX)

# 2) 图标右边多远是数字：图标右边缘 1102，数字区 1197~1253
#    以图标左上角为基准，(1197-1050, 20-20) = (147, 0)
OFFSET_X, OFFSET_Y = 147, 0
NUM_W, NUM_H = 70, 55          # 1102+... 覆盖「0」以及「300」的前两位范围

REGION = (1020, 10, 1340, 95)
print("\n=== 门票图标模板定位验证 ===")
for f, label in [("shots/prep_300_live.png", "备战页(门票300)"),
                 ("shots/prep_zero_live.png", "备战页(门票0)"),
                 ("shots/toast_live.png", "备战页(点挑战后)"),
                 ("shots/courtyard_clean.png", "庭院"),
                 ("shots/state_now2.png", "结界突破页")]:
    if not os.path.exists(f):
        continue
    im = Image.open(f).convert("RGB")
    if im.size != (1920, 1080):
        im = im.resize((1920, 1080), Image.LANCZOS)
    s, x, y = vision.match(im, os.path.join(TPL_DIR, "t_ticket_icon.png"), region=REGION)
    print(f"  {label:20s} 图标分 {s:6.3f} 位置 ({x},{y})  -> 数字区 x {x+OFFSET_X}~{x+OFFSET_X+NUM_W}")

# 3) 数字为 0 的模板：从「门票 0」那张裁
z_box = (1197, 20, 1262, 80)
ZERO.crop(z_box).save(os.path.join(TPL_DIR, "t_ticket_zero.png"))
ZERO.crop(z_box).resize(((z_box[2]-z_box[0])*3, (z_box[3]-z_box[1])*3), Image.NEAREST).save(
    "shots/ticket_zero_zoom.png")
BASE.crop(z_box).resize(((z_box[2]-z_box[0])*3, (z_box[3]-z_box[1])*3), Image.NEAREST).save(
    "shots/ticket_300_zoom.png")
print("\n门票数字区对比图已存: shots/ticket_zero_zoom.png（0） / shots/ticket_300_zoom.png（300）")

# 4) 验证：数字模板在两种画面上分别多少分
print("\n=== 直接比数字区（用固定坐标，先看区分度）===")
for f, label in [("shots/prep_zero_live.png", "门票0"),
                 ("shots/toast_live.png", "门票0(另一张)"),
                 ("shots/prep_300_live.png", "门票300"),
                 ("shots/ref_prep.png", "门票296")]:
    if not os.path.exists(f):
        continue
    im = Image.open(f).convert("RGB")
    if im.size != (1920, 1080):
        im = im.resize((1920, 1080), Image.LANCZOS)
    s, x, y = vision.match(im, os.path.join(TPL_DIR, "t_ticket_zero.png"),
                           region=(1150, 10, 1340, 95))
    print(f"  {label:16s} 0模板分 {s:6.3f} 位置 ({x},{y})")
