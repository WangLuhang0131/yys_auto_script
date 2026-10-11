# -*- coding: utf-8 -*-
"""实机检查：当前备战页的门票判定是否正确（别再被五倍券 0 骗到）。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adbkit import Adb                                   # noqa: E402
from human_click import Human                            # noqa: E402
from core.nav import Returner                            # noqa: E402
from tasks.event_dungeon.game import Game                # noqa: E402

a = Adb()
r = Returner(a, Human(a, log=lambda m: None), lambda m: None)
print("当前页面:", r.detect())

g = Game(adb=a, debug=False, verbose=False)
st, info = g.detect()
print("活动任务识别:", st, {k: v for k, v in info.items() if k in ("score",)})

im = a.screenshot()
im.save("shots/live_ticket_check.png")
ex, s0, si = g.challenge_count_zero(im)
print(f"门票用尽? {ex}   数字分={s0}   图标分={si}")
print("（门票还有剩余时必须是 False）")
