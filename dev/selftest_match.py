# -*- coding: utf-8 -*-
"""自检：从图里裁一块，再在原图里找它，分数必须是 1.0（或接近）。

如果这里就不对，说明是我的匹配实现有问题，而不是坐标问题。
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw                         # noqa: E402
import vision                                            # noqa: E402

im = Image.open("shots/explore_user.png").convert("RGB")

tests = [
    ("草地(低对比)", (600, 1000, 750, 1050)),
    ("印章图标(红)", (500, 930, 620, 985)),
    ("文字区(高对比)", (498, 980, 624, 1020)),
    ("大块区域", (430, 900, 700, 1050)),
]
for label, box in tests:
    b = tuple(int(v * im.size[0] / 1920) for v in box)
    tpl_path = os.path.join("shots", f"selftest_{label.split('(')[0]}.png")
    crop = im.crop(b)
    crop.save(tpl_path)
    s, x, y = vision.match(im, tpl_path, region=(b[0] - 40, b[1] - 40, b[2] + 40, b[3] + 40))
    expect_x = b[0] + crop.width // 2
    expect_y = b[1] + crop.height // 2
    ok = s > 0.95
    print(f"{'OK ' if ok else '!! '}{label:16s} 自匹配分 {s:6.3f} "
          f"找到 ({x},{y}) 期望 ({expect_x},{expect_y}) 模板 {crop.size}")
    # 也看看把模板整体贴回去时的相关值
    a = np.asarray(im, dtype=np.float32).mean(axis=2)
    t = np.asarray(crop, dtype=np.float32).mean(axis=2)
    patch = a[b[1]:b[3], b[0]:b[2]]
    print(f"      直接逐像素差: 平均 {np.abs(patch - t).mean():.2f} 最大 {np.abs(patch - t).max():.0f}")
