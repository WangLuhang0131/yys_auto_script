# -*- coding: utf-8 -*-
"""做「挑战次数 = 0」模板：只在次数为 0 时匹配得上。

备战页第一个「卷轴 + 数字」= 剩余挑战次数；实测数字区 x 1238~1253, y 35~60。
次数 >0 时数字会变宽/变多，模板就匹配不上了。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402
import vision                                            # noqa: E402

SRC = "shots/ref_prep.png"           # 这张是次数 296 的备战页
ZERO = "shots/prep_zero_live.png"    # 这张是次数 0

# 先看次数>0 时数字区长什么样
im = Image.open(SRC).convert("RGB")
im.crop((1180, 20, 1400, 80)).resize((220 * 3, 60 * 3), Image.NEAREST).save(
    "shots/count_296_zoom.png")
print("次数 296 的数字区已存 shots/count_296_zoom.png")

# 以 0 次那张为模板
z = Image.open(ZERO).convert("RGB")
BOX = (1225, 25, 1270, 72)
TPL = os.path.join("tasks", "event_dungeon", "templates", "t_count_zero.png")
z.crop(BOX).save(TPL)
print("0 次模板:", Image.open(TPL).size, "取自", BOX)

REGION = (1180, 15, 1330, 85)
cases = [
    (ZERO, "次数0（实机）", True),
    ("shots/no_item_prep.png", "次数0（另一次）", True),
    ("shots/toast_live.png", "次数0（点挑战后）", True),
    (SRC, "次数296", False),
    ("shots/step2_jiejie.png", "结界突破页", False),
    ("shots/courtyard_clean.png", "庭院", False),
]
z_min, n_max = 9, -9
for f, label, is_zero in cases:
    if not os.path.exists(f):
        continue
    s, _, _ = vision.match(Image.open(f).convert("RGB"), TPL, region=REGION)
    print("%s%-22s 0次分=%5.3f 期望=%s"
          % ("OK " if (s >= 0.6) == is_zero else "!! ", label, s,
             "是0" if is_zero else "不是"))
    if is_zero:
        z_min = min(z_min, s)
    else:
        n_max = max(n_max, s)
print("\n0次最低=%.3f 非0最高=%.3f -> %s"
      % (z_min, n_max, "可分" if z_min > n_max + 0.15 else "不够分"))
