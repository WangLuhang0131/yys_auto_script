# -*- coding: utf-8 -*-
"""从实机截图裁「琥珀卷轴不足」toast 模板，并验证它在无提示的截图上不误报。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402
import vision                                            # noqa: E402

SRC = "shots/toast_live.png"
im = Image.open(SRC).convert("RGB")

# toast 文字：中心约 (925, 325)，宽度约 230
BOX = (790, 300, 1075, 350)
crop = im.crop(BOX)
crop.resize((crop.width * 3, crop.height * 3), Image.NEAREST).save("shots/toast_tpl_zoom.png")
TPL = os.path.join("tasks", "event_dungeon", "templates", "t_no_item_toast.png")
crop.save(TPL)

# 关键：做「只匹配亮笔画」的掩膜，否则大片低对比背景会让它在无 toast 时也拿高分
import numpy as np                                       # noqa: E402
arr = np.asarray(crop, dtype=np.float32)
lum = arr.mean(axis=2)
mask = (lum > 165).astype(np.uint8) * 255
Image.fromarray(mask).save(os.path.join("tasks", "event_dungeon", "templates",
                                        "t_no_item_toast_mask.png"))
print("掩膜亮像素占比 %.3f" % (mask > 0).mean())
print("toast 模板:", crop.size, "取自", BOX)

REGION = (650, 270, 1300, 390)
MASK = os.path.join("tasks", "event_dungeon", "templates", "t_no_item_toast_mask.png")
cases = [
    ("shots/toast_live.png", "有点挑战后(有toast)", True),
    ("shots/prep_before_tap.png", "备战页(无toast)", False),
    ("shots/no_item_prep.png", "备战页2(无toast)", False),
    ("shots/ref_prep.png", "备战页3(无toast)", False),
    ("shots/state_now2.png", "结界突破页", False),
    ("shots/courtyard_clean.png", "庭院", False),
]
t_min, n_max = 9, -9
for f, label, is_toast in cases:
    if not os.path.exists(f):
        continue
    s, _, _ = vision.match(Image.open(f).convert("RGB"), TPL, region=REGION, mask_path=MASK)
    print("%s%-24s toast分=%5.3f 期望=%s"
          % ("OK " if (s >= 0.6) == is_toast else "!! ", label, s,
             "有" if is_toast else "无"))
    if is_toast:
        t_min = min(t_min, s)
    else:
        n_max = max(n_max, s)
print("\n有toast最低=%.3f 无toast最高=%.3f -> %s"
      % (t_min, n_max, "可分" if t_min > n_max + 0.15 else "不够分"))
