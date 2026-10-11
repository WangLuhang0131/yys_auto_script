# -*- coding: utf-8 -*-
"""用 adb 抓当前真实画面（应为 0/30 券不足状态），量券数判据。

对照基准：
  · 券数够时的截图（7/30）：shots/ticket_now.png 等
  · 现在 adb 抓到的 0/30：本脚本抓
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adbkit import Adb                                   # noqa: E402
from PIL import Image                                    # noqa: E402
from tasks.jiejie_tupo import attack as atk              # noqa: E402

a = Adb()
im = a.screenshot()
im.save("shots/ticket_real_now.png")
print("adb 抓图:", im.size)

info = atk.ticket_info(im)
print("\n券数判据结果:")
print("  字形段:", info["glyphs"])
print("  斜杠宽:", info["slash_w"], " 左数宽:", info["left_w"],
      " 左数位置:", info["left_x"], " 判定用完:", info["almost_out"])

# 同时看「结界挑战券不足」提示区（画面中部，实测 y≈470）
g = np.asarray(im.convert("L"), dtype=np.float32)
band = g[455:500, 800:1150]
print(f"\n中部提示区 亮度均值 {band.mean():.1f} 最大 {band.max():.0f}")

im.crop((1600, 15, 1840, 85)).resize((240 * 3, 70 * 3), Image.NEAREST).save(
    "shots/ticket_real_zoom.png")
print("已保存 shots/ticket_real_zoom.png")
