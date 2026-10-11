# -*- coding: utf-8 -*-
"""给「结界挑战券不足」提示做模板。

来源：用户截图里那句提示（我有半句「结界挑战券不足」，需要完整的一句）。
这里先把可见部分裁出来，并输出它的精确位置，便于后续裁剪完整模板。
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402

# 用户整屏图里那句话：目测 x 1180~1650, y 840~900（2729x1536）
im = Image.open("shots/ticket_0of30_screen.png").convert("RGB")
W, H = im.size
s = W / 1920.0
box_user = (int(1150 * s), int(590 * s), int(1700 * s), int(660 * s))
crop = im.crop(box_user)
crop.save("shots/warn_text_from_user.png")
print("用户图里提示带小块:", crop.size, "取自", box_user)

g = np.asarray(im.convert("L"), dtype=np.float32)
sub = g[box_user[1]:box_user[3], box_user[0]:box_user[2]]
print(f"该块亮度 均值{sub.mean():.1f} 最大{sub.max():.0f}")
# 找亮像素范围（文字）
ys, xs = np.nonzero(sub > float(np.percentile(sub, 99)))
if len(xs):
    print(f"亮像素范围: x {box_user[0]+xs.min()}~{box_user[0]+xs.max()} "
          f"y {box_user[1]+ys.min()}~{box_user[1]+ys.max()}")
    print(f"换算 1920 基准: x {(box_user[0]+xs.min())/s:.0f}~{(box_user[0]+xs.max())/s:.0f} "
          f"y {(box_user[1]+ys.min())/s:.0f}~{(box_user[1]+ys.max())/s:.0f}")

# 放大保存，便于人眼确认裁到的是不是那句话
crop.resize((crop.width * 2, crop.height * 2), Image.NEAREST).save("shots/warn_text_zoom.png")
print("已保存 shots/warn_text_zoom.png（放大版）")
