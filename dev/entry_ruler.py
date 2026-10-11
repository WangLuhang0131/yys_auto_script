# -*- coding: utf-8 -*-
"""不再靠换算：把「探索页底栏」整条底栏在 1920 基准下图解出来，标上坐标刻度。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw                         # noqa: E402

im = Image.open("shots/explore_user.png").convert("RGB")
base = im.resize((1920, 1080), Image.LANCZOS)            # 统一到 1920 基准
crop = base.crop((400, 880, 800, 1040))
big = crop.resize((crop.width * 3, crop.height * 3), Image.LANCZOS)
d = ImageDraw.Draw(big)
# 画刻度：每 50 基准像素一条竖线，标出绝对 x
for x in range(400, 801, 50):
    px = (x - 400) * 3
    d.line([(px, 0), (px, 20)], fill=(255, 0, 0), width=2)
    d.text((px + 2, 2), str(x), fill=(255, 0, 0))
for y in range(880, 1041, 40):
    py = (y - 880) * 3
    d.line([(0, py), (20, py)], fill=(0, 255, 0), width=2)
    d.text((22, py), str(y), fill=(0, 255, 0))
big.save("shots/entry_ruler.png")
print("已存 shots/entry_ruler.png（红=绝对x刻度，绿=绝对y刻度）")
