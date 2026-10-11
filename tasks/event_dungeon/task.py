# -*- coding: utf-8 -*-
"""任务：活动副本（拾此一瞬 → 古迹演武）

流程：活动总览 →[前往活动]→ 活动详情 →[古迹演武]→ 备战页
      →[挑战]→ 自动战斗 →[点击屏幕继续]→ 回备战页 → 循环 N 次

停止条件（除了刷够次数）：
  · 挑战键变灰（活动道具用完）→ 判定任务完成，正常停止
  · 道具用完时挑战键虽然还亮但点了没反应 → 连续多次进不了战斗也判定完成

本任务自带 game.py 与 templates/，删掉 tasks/event_dungeon/ 不影响其它任务。
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.tasks import TaskBase            # noqa: E402
from tasks.event_dungeon.game import (     # noqa: E402
    Game, T_CHALLENGE, T_CENTER, T_END_DISMISS,
)

import vision                              # noqa: E402

try:
    from core.paths import res_root
    TPL_DIR = os.path.join(res_root(), "tasks", "event_dungeon", "templates")
except Exception:
    TPL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
TAP_ACTIVITY_ICON = (1835, 222)     # 庭院右侧「活动」图标（坐标兜底用）
R_COURTYARD_ACTIVITY = (1700, 130, 1920, 320)   # 按图找「活动」图标的搜索区


class Task(TaskBase):
    name = "活动副本（古迹演武）"
    slug = "event_dungeon"
    desc = ("自动刷「拾此一瞬」活动的古迹演武。\n"
            "可从庭院开始（自动点右侧「活动」），\n"
            "也可停在活动总览/活动详情/备战页。\n"
            "活动道具用完会自动停止。")
    supports_runs = True
    need_color = True

    #: 连续多少次「进不了战斗」就判定道具用完
    MAX_ENTER_FAILS = 3

    def _tpl(self, name):
        return os.path.join(TPL_DIR, name)

    def _is_courtyard(self, img):
        s, _, _ = vision.match(img, self._tpl("t_courtyard_bar.png"),
                               region=(60, 830, 1880, 1070))
        return s >= 0.60

    def tap_activity_icon(self, ctx):
        """庭院里点右侧「活动」图标：**按图找点**（庭院物件会随布置移动，写死坐标危险）。

        实测模板区分度：庭院图上 1.000，其它页面 ≤0.30。找不到时退回坐标。
        """
        img = ctx.a.screenshot()
        ok, score, x, y = ctx.human.tap_image(
            img, "活动", self._tpl("t_courtyard_activity.png"),
            region=R_COURTYARD_ACTIVITY, th=0.62, note="活动")
        if not ok:
            ctx.log(f"    按图没找到「活动」图标（分数 {score}），退回坐标点击")
            ctx.human.tap("activity_icon", *TAP_ACTIVITY_ICON, note="活动(坐标兜底)")
        return ok

    def check_ready(self, ctx):
        g = self._game(ctx)
        if self._is_courtyard(ctx.a.screenshot()):
            return True, "在庭院，会自动点右侧「活动」进入"
        st, info = g.detect()
        mapping = {
            "prep": "已就位（古迹演武备战页）",
            "overview": "已就位（活动总览页，会自动进入）",
            "detail": "已就位（活动详情页，会自动进入）",
            "battle": "正在战斗中，会等这场打完再接管",
            "end": "停在结束画面，会先点掉",
        }
        if st in mapping:
            return True, mapping[st]
        return True, f"认不出当前画面（{st}），会先尝试点返回再导航"

    def _game(self, ctx):
        if not hasattr(self, "_g"):
            self._g = Game(adb=ctx.a, human=ctx.human, debug=False, verbose=False)
            self._g.log = lambda m: ctx.log(m)
        return self._g

    def run(self, ctx):
        g = self._game(ctx)

        # ---- 进场：在庭院就按图找「活动」图标，否则处理战斗/结算画面 ----
        if self._is_courtyard(ctx.a.screenshot()):
            ctx.log("在庭院 → 按图找右侧「活动」图标")
            self.tap_activity_icon(ctx)
            ctx.sleep(3.5)
        else:
            st, info = g.detect()
            ctx.log(f"当前画面状态: {st} {info}")
            self._wait_until_idle(g, ctx, st)

        if not g.go_to_prep():
            ctx.log("!! 无法进入备战页，任务结束")
            return

        runs = ctx.target_runs or 9999
        ok_cnt = fail_cnt = 0
        enter_fail_streak = 0

        for i in range(1, runs + 1):
            if ctx.stopped():
                break

            # 道具用完的判据 1（最可靠）：备战页「剩余挑战次数 = 0」
            s_zero = g.challenge_count_zero()
            if s_zero >= 0.75:
                ctx.log(f"备战页剩余挑战次数为 0（匹配 {s_zero:.3f}）→ 活动道具已用完，任务完成")
                ctx.log(f"本次共完成 {ok_cnt} 次")
                return

            # 道具用完的判据 2：挑战键变灰
            ready, ratio = g.challenge_ready()
            if not ready:
                ctx.log(f"挑战键已变灰（亮像素占比 {ratio}），活动道具用完 → 任务完成")
                ctx.log(f"本次共完成 {ok_cnt} 次")
                return

            ctx.set_progress(i, runs, "活动战斗")
            ctx.log(f"--- 第 {i}/{runs} 次 ---")
            ok, dur, bminfo = g.one_battle()

            if ok:
                ok_cnt += 1
                enter_fail_streak = 0
                ctx.log(f"    成功  用时 {dur:.1f}s  累计成功 {ok_cnt} 失败 {fail_cnt}")
            else:
                fail_cnt += 1
                ctx.log(f"    !! 失败 {bminfo}")
                if bminfo.get("err") == "no_item":
                    ctx.log("点挑战后弹出「道具不足」提示 → 活动道具已用完，任务完成")
                    ctx.log(f"本次共完成 {ok_cnt} 次")
                    return
                if bminfo.get("err") == "enter_failed":
                    enter_fail_streak += 1
                    if enter_fail_streak >= self.MAX_ENTER_FAILS:
                        ctx.log(f"连续 {enter_fail_streak} 次点挑战都进不了战斗，"
                                f"判定活动道具已用完 → 任务完成")
                        ctx.log(f"本次共完成 {ok_cnt} 次")
                        return
                else:
                    enter_fail_streak = 0
                ctx.log("    尝试恢复到备战页...")
                if not g.go_to_prep():
                    ctx.log("    !! 恢复失败，任务结束")
                    return

            ctx.human.maybe_long_pause(0.18)

        ctx.log(f"达到目标次数，任务完成：成功 {ok_cnt} 次，失败 {fail_cnt} 次")

    # ---------- 内部 ----------
    def _wait_until_idle(self, g, ctx, st):
        """如果进来时正在战斗/停在结束画面，先处理干净。"""
        if st == "battle":
            ctx.log("检测到正在战斗中，等本场结束...")
            s2, _, i2 = g.wait_state(("end", "prep"), timeout=300, interval=0.5)
            ctx.log(f"战场结束，状态={s2} {i2}")
            st = s2
        if st == "end":
            g.tap_and_wait(T_END_DISMISS, ("prep", "detail", "overview"),
                           timeout=15, note="点掉结束画面")
