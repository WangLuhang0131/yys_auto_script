# -*- coding: utf-8 -*-
"""验证「琥珀卷轴不足」提示检测。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402
from tasks.event_dungeon.game import Game                # noqa: E402

g = Game(debug=False, verbose=False)
cases = [
    ("shots/toast_live.png", True, "点挑战后(有提示)"),
    ("shots/prep_before_tap.png", False, "备战页(无提示)"),
    ("shots/ref_prep.png", False, "备战页2(无提示)"),
    ("shots/no_item_prep.png", False, "备战页3(无提示)"),
    ("shots/courtyard_clean.png", False, "庭院"),
    ("shots/state_now2.png", False, "结界突破页"),
]
bad = 0
for f, expect, label in cases:
    if not os.path.exists(f):
        continue
    s = g.is_no_item_toast(Image.open(f).convert("RGB"))
    ok = (s >= 0.80) == expect
    bad += 0 if ok else 1
    print("%s%-22s 提示分=%5.3f 期望=%s"
          % ("OK " if ok else "!! ", label, s, "有提示" if expect else "无提示"))
print("全部通过" if bad == 0 else f"{bad} 个不符合")
