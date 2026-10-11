# -*- coding: utf-8 -*-
"""做「不足」提示模板（琥珀卷轴不足 / 结界挑战券不足 都含这两个字）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402

BASE = "shots"
u = Image.open(os.path.join(BASE, "no_item_user.png")).convert("RGB")
s = u.size[0] / 1920.0
print("用户图", u.size, "缩放", round(s, 3))

# toast 在 1920 基准 y≈296~336, x≈752~972
box = tuple(int(v * s) for v in (740, 288, 990, 345))
crop = u.crop(box)
print("裁出", crop.size, "取自", box)
crop.resize((crop.width * 2, crop.height * 2), Image.NEAREST).save(
    os.path.join(BASE, "toast_zoom.png"))
crop.save(os.path.join(BASE, "toast_candidate.png"))
