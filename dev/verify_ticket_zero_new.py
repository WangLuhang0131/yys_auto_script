# -*- coding: utf-8 -*-
"""验证「门票次数为 0」的新判据：绝不能再被右边的「五倍券 0」骗到。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402
from tasks.event_dungeon.game import Game                # noqa: E402

g = Game(debug=False, verbose=False)

cases = [
    ("shots/prep_300_live.png", False, "门票300 + 五倍券0（就是这次误判的场景）"),
    ("shots/ref_prep.png", False, "门票296"),
    ("shots/prep_zero_live.png", True, "门票0"),
    ("shots/toast_live.png", True, "门票0（点挑战后）"),
    ("shots/courtyard_clean.png", False, "庭院"),
    ("shots/state_now2.png", False, "结界突破页"),
]
bad = 0
print(f"{'画面':<36}{'门票0?':>7}{'数字分':>9}{'图标分':>9}  期望")
for f, expect, label in cases:
    if not os.path.exists(f):
        print("跳过（无此截图）:", f)
        continue
    im = Image.open(f).convert("RGB")
    if im.size != (1920, 1080):
        im = im.resize((1920, 1080), Image.LANCZOS)
    got, s0, si = g.challenge_count_zero(im)
    ok = got == expect
    bad += 0 if ok else 1
    print(f"{'OK ' if ok else '!! '}{label:<33}{str(got):>7}{s0:>9.3f}{si:>9.3f}  {expect}")

print("\n全部通过" if bad == 0 else f"\n有 {bad} 个不符合")
