# -*- coding: utf-8 -*-
"""裁「庭院左上角头像」模板，用于识别当前是否停在庭院主界面。

用户整屏图 2729x1536（缩放 1.421）。头像大致在 1920 基准 x 10~115, y 15~120。
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402

BASE = r"D:\Program Files\WKSPC\yys\shots"
user = Image.open(os.path.join(BASE, "courtyard_user.png"))
s = user.size[0] / 1920.0
print("用户图尺寸:", user.size, "缩放", round(s, 3))

box_user = (int(8 * s), int(12 * s), int(120 * s), int(125 * s))
crop = user.crop(box_user)
crop.save(os.path.join(BASE, "courtyard_avatar_from_user.png"))
print("裁出:", crop.size, "取自", box_user)
crop.resize((crop.width * 2, crop.height * 2), Image.NEAREST).save(
    os.path.join(BASE, "courtyard_avatar_zoom.png"))
