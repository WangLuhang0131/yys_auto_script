# -*- coding: utf-8 -*-
"""制作「点击屏幕继续」金色文字的掩膜模板。"""
import numpy as np
from PIL import Image

SRC = "shots/dbg/001_t0_before.png"
BOX = (780, 995, 1140, 1070)      # 文字区域
im = Image.open(SRC).convert("RGB")
tpl = im.crop(BOX)
tpl.save("templates/end_text.png")

a = np.asarray(tpl, dtype=np.float32)
# 金色/米白文字掩膜：亮且低饱和偏暖
lum = a.mean(axis=2)
mask = ((lum > 150) & (a[:, :, 0] - a[:, :, 2] > 10)).astype(np.uint8) * 255
Image.fromarray(mask).save("templates/end_text_mask.png")
print("模板尺寸", tpl.size, "掩膜像素数", int((mask > 0).sum()),
      "占比", round(float((mask > 0).mean()), 3))

# 放大一点以便人眼确认
Image.fromarray(np.asarray(tpl.resize((tpl.width * 2, tpl.height * 2)))).save("shots/end_text_zoom.png")
