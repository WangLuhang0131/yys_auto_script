# -*- coding: utf-8 -*-
"""任务：结界突破

实机验证过的完整流程：
  庭院 →[探索]→ 探索页 →[结界突破]→ 结界突破页
  → 检查阵容锁定（未锁定则点「阵容」锁定）
  → 扫描 9 个格子：亮的可打，灰色的（带「破」）已攻破直接跳过
  → 点可打格子的「名字/进度圈」区域 → 弹出进攻面板 → 点「进攻」
  → 自动战斗 → 胜利画面点「点击屏幕继续」→ 回到结界突破页
  → 9 个格子处理完 → 自动刷新 → 继续下一轮

实测要点：
  · 点灰格 / 点头像本身都没反应，必须点亮的格子的名字那一片；
  · 点掉「点击屏幕继续」后回到结界突破页，被打的格子由亮变灰（182 → 108）；
  · adb 点击有约 1.7 秒延迟，所以每个动作后都留了等待。
"""
from __future__ import annotations

import os
import sys
import time

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import vision                                                # noqa: E402
from core.tasks import TaskBase                              # noqa: E402
from . import ui                                             # noqa: E402
from . import attack as atk                                  # noqa: E402


class Task(TaskBase):
    name = "结界突破"
    slug = "jiejie_tupo"
    desc = ("自动刷「结界突破」：探索 → 结界突破 → 检查阵容锁定 →\n"
            "9 个格子逐个挑战（自动跳过已攻破的灰格）→ 自动刷新 → 循环。\n"
            "需要游戏停在庭院主界面或结界突破页。")
    supports_runs = True
    need_color = True

    MAX_ENTER_FAIL = 3        # 连续几次开不出进攻面板就认为该格打不了
    MAX_EMPTY_ROUNDS = 3      # 连续几轮一个可打格子都没有 -> 判定券已用完

    # ---------------- 执行前检查 ----------------
    def check_ready(self, ctx):
        """只报告，不拦截：真正的"先点掉结算画面 / 导航进去"都在 run() 里做，
        否则用户停在胜利画面时会被直接拒绝启动。"""
        st = self.detect(ctx)
        tips = {
            "jiejie": "已在结界突破页",
            "explore": "在探索页，会自动进入结界突破",
            "unknown": "不在已知页面，脚本会先尝试点返回/结算画面再导航",
        }
        return True, tips.get(st, st)

    def detect(self, ctx):
        return self.detect_img(ctx.a.screenshot())

    def detect_img(self, img):
        """模板判定：'jiejie' / 'explore' / 'courtyard' / 'unknown'。

        判据用**多个信号组合**，因为每个单独都会在某种情况下失手（都实测过）：
          · 左下「攻破记录」：进度条推上来时会被进度图标压住（掉到 0.29）；
          · 右下「刷新」按钮：攻击面板打开时被面板盖住（掉到 0.27）；
          · 顶部标题「结界突破」：被顶部系统横幅遮挡时掉到 0.2。
        另外攻击面板开着 = 必然在结界突破页。
        **庭院必须单独认出来**：庭院左上角是自己的头像（不是返回键），
        在那里点「返回」会弹设置页把流程卡死（踩过这个坑）。
        """
        # 1) 庭院：底部功能栏（图鉴/珍旅居/纳物库…）
        s0, _, _ = vision.match(img, ui.tpl("t_courtyard_bar.png"), region=ui.R_COURTYARD)
        if s0 >= 0.60:
            return "courtyard"
        # 2) 结界突破：左下「攻破记录」
        s1, _, _ = vision.match(img, ui.tpl("t_record_label.png"), region=ui.R_RECORD)
        if s1 >= 0.60:
            return "jiejie"
        # 3) 结界突破：右下「刷新」按钮
        s2, _, _ = vision.match(img, ui.tpl("t_refresh_btn.png"), region=ui.R_REFRESH)
        if s2 >= 0.60:
            return "jiejie"
        # 4) 结界突破：顶部标题
        s3, _, _ = vision.match(img, ui.tpl("t_title_jiejie.png"),
                                region=(700, 95, 1200, 185))
        if s3 >= 0.60:
            return "jiejie"
        # 5) 攻击面板开着 -> 结界突破页
        has_panel, _, _, _ = atk.find_attack_btn(img)
        if has_panel:
            return "jiejie"
        # 6) 探索页底栏
        s5, _, _ = vision.match(img, ui.tpl("t_explore_bar.png"),
                                region=(400, 930, 750, 1040))
        if s5 >= 0.60:
            return "explore"
        return "unknown"

    # ---------------- 主流程 ----------------
    def run(self, ctx):
        rounds = ctx.target_runs or 9999
        total_wins = 0

        if not self.ensure_jiejie_page(ctx):
            return

        empty_rounds = 0            # 连续几轮一个可打格子都没有
        for rnd in range(1, rounds + 1):
            if ctx.stopped():
                break

            # 突破券用完就收工（判据见 attack_cell：点进攻后没进战斗）
            # 这里不再读右上角的券数——实测小字在截图缩放/压缩后不可靠，已放弃。

            ctx.log(f"===== 第 {rnd}/{rounds} 轮 =====")

            self.ensure_lineup_locked(ctx)

            wins_this_round = 0
            tried_this_round = 0
            for pos, (cx, cy) in enumerate(ui.GRID_CENTERS, 1):
                if ctx.stopped():
                    break
                ctx.set_progress(pos, 9, f"第{rnd}轮结界突破")
                img = ctx.a.screenshot()
                ratio = atk.cell_ratio(img, cx, cy)
                if ratio <= atk.CELL_RATIO_TH:
                    ctx.log(f"  格子 {pos}/9 ({cx},{cy}) 已攻破（相对亮度 {ratio:.2f}），跳过")
                    continue

                tried_this_round += 1
                ctx.log(f"  格子 {pos}/9 ({cx},{cy}) 可打（相对亮度 {ratio:.2f}），开打")
                if self.attack_cell(ctx, cx, cy):
                    wins_this_round += 1
                    total_wins += 1
                    ctx.log(f"    攻破成功（本轮 {wins_this_round}，累计 {total_wins}）")
                else:
                    if getattr(self, "_tickets_out", False):
                        ctx.log(f"突破券已用完 → 任务结束"
                                f"（本次累计攻破 {total_wins} 个结界）")
                        return
                    ctx.log("    这一格没能打下来，继续下一个")

                self.dismiss_continue(ctx)

            # 兜底：一个能打的都没有（多半是券没了）
            if tried_this_round == 0:
                empty_rounds += 1
                ctx.log(f"  本轮没有任何可打格子（连续 {empty_rounds} 轮）")
                if empty_rounds >= self.MAX_EMPTY_ROUNDS:
                    ctx.log(f"连续 {empty_rounds} 轮没有可打格子 → 判定突破券已用完，"
                            f"任务完成（累计攻破 {total_wins} 个结界）")
                    return
            else:
                empty_rounds = 0

            ctx.log(f"本轮 9 格处理完（攻破 {wins_this_round} 个），检查是否已刷新...")
            if not self.wait_refresh(ctx, timeout=20):
                ctx.log("  未自动刷新，点一次「刷新」")
                self.tap_refresh(ctx)

            ctx.human.maybe_long_pause(0.15)

        ctx.log(f"达到目标轮数，任务完成：累计攻破 {total_wins} 个结界")

    # ---------------- 导航 ----------------
    def tap_courtyard_object(self, ctx, name, tpl_name, region, note, th=0.62):
        """在庭院里**按图找点**：庭院是自由布置的，物件位置会变，写死坐标很危险。

        实测模板区分度：庭院图上 1.000，其它页面 ≤0.30。
        找不到时退回内置坐标，保证不会因为匹配失败就卡住。
        """
        img = ctx.a.screenshot()
        ok, score, x, y = ctx.human.tap_image(
            img, name, ui.tpl(tpl_name), region=region, th=th, note=note)
        if ok:
            return True
        ctx.log(f"    按图没找到「{name}」（分数 {score}），退回坐标点击")
        return False

    def ensure_jiejie_page(self, ctx):
        # 先看看是不是停在结算画面（胜利/战斗结束），是的话先点掉
        self.dismiss_continue(ctx)

        st = self.detect(ctx)
        if st == "jiejie":
            ctx.log("已经在结界突破页")
            return True
        ctx.log(f"导航到结界突破页（当前 {st}）...")

        for attempt in range(3):
            if st == "courtyard":
                # 关键教训：庭院左上角是**自己的头像**，不是返回键！点它会弹设置页。
                # 而且庭院物件位置会移动，所以「探索」必须按图找点。
                ctx.log("  在庭院 → 按图找「探索」灯笼")
                if not self.tap_courtyard_object(
                        ctx, "探索", "t_courtyard_explore.png",
                        ui.R_COURTYARD_EXPLORE, "探索"):
                    ctx.human.tap("explore", *ui.TAP_EXPLORE, note="探索(坐标兜底)")
                ctx.sleep(3.5)
            elif st == "unknown":
                if self.close_profile_if_open(ctx):
                    ctx.log("  关掉弹窗后继续")
                else:
                    ctx.log("  认不出页面，按一次系统返回键")
                    ctx.a.key("KEYCODE_BACK")
                    ctx.sleep(2.0)
                self.dismiss_continue(ctx)
            elif st == "explore":
                # 关键教训：原来写死 (870,440)，结果点到了**旁边的「式神委派」**
                # （底栏「结界突破」在 x≈500~650，「式神委派」在 x≈720~850，
                #   只差 90 像素）。相邻按钮这么近，必须按图找。
                ctx.log("  在探索页 → 按图找底栏「结界突破」入口")
                img = ctx.a.screenshot()
                ok_img, score, x, y = ctx.human.tap_image(
                    img, "结界突破入口", ui.tpl("t_jj_entry_bottom.png"),
                    region=ui.R_JJ_ENTRY_BOTTOM, th=0.62, note="结界突破入口")
                if not ok_img:
                    ctx.log(f"    按图没找到入口（分数 {score}），退回坐标点击")
                    ctx.human.tap("jj_entry", *ui.TAP_JJTP_ENTRY, note="结界突破(坐标兜底)")
                ctx.sleep(3.5)
            elif st == "jiejie":
                break

            st = self.detect(ctx)
            ctx.log(f"  第{attempt+1}次导航后：{st}")
            if st == "jiejie":
                break

        ok = st == "jiejie"
        ctx.log("已进入结界突破页" if ok else f"!! 没能进入结界突破页（当前 {st}）")
        return ok

    # ---------------- 阵容锁定 ----------------
    def ensure_lineup_locked(self, ctx):
        """未锁定就点一下「阵容」左侧的金框图标锁上。

        实机标定：未锁定 = 亮色菱形（亮像素占比 0.53 / 金色 0.069），
                  已锁定 = 深色边框（0.47 / 0.048）；点图标本身即可切换。
        检测模糊（unknown）时不动作，只提示，避免误点把队伍改乱。
        """
        img = ctx.a.screenshot()
        st, m = atk.lock_state(img)
        if st == "locked":
            ctx.log(f"  阵容已锁定 {m}")
            return True
        if st == "unknown":
            ctx.log(f"  阵容锁定状态识别不清 {m}，为稳妥不做动作")
            return False

        ctx.log(f"  阵容未锁定 {m} -> 点图标锁定")
        ctx.human.tap("lock_icon", *ui.TAP_LOCK_ICON, note="锁定阵容")
        ctx.sleep(2.0)
        st2, m2 = atk.lock_state(ctx.a.screenshot())
        ctx.log(f"  锁定操作后：{st2} {m2}")
        return st2 == "locked"

    # ---------------- 打一个格子 ----------------
    def attack_cell(self, ctx, cx, cy):
        dx, dy = ui.CELL_TAP_DX_DY
        hw, hh = ui.CELL_TAP_BOX_HALF
        tx, ty = cx + dx, cy + dy
        box = (tx - hw, ty - hh, tx + hw, ty + hh)

        # 1) 点格子开面板（安全落点已避开玩家头像和「破」标记）
        btn = None
        for attempt in range(1, self.MAX_ENTER_FAIL + 1):
            if ctx.stopped():
                return False
            ctx.human.tap("cell", tx, ty, box=box, note=f"点格子({cx},{cy})")
            t0 = time.time()
            while time.time() - t0 < 8:
                if ctx.stopped():
                    return False
                img = ctx.a.screenshot()
                ok, s1, bx, by = atk.find_attack_btn(img)
                if ok:
                    btn = (bx, by)
                    ctx.log(f"    进攻面板已打开（进攻 {s1}，按钮在 ({bx},{by})）")
                    break
                time.sleep(0.5)
            if btn:
                break
            # 面板没打开：很可能是误触头像/名字弹出了「玩家资料页」（实测会有），
            # 必须先关掉它，否则后面的点击全被这层挡住。
            if self.close_profile_if_open(ctx):
                ctx.log("    已关掉玩家资料页，重试点格子")
            else:
                ctx.log(f"    第 {attempt} 次没打开面板，换点重试")
            ctx.sleep(0.8)
        if not btn:
            return False

        # 2) 点「进攻」（面板会跟着格子移动，用刚实测到的位置）
        ctx.human.tap("attack", btn[0], btn[1], note="进攻")

        # 3) 等结果：出现「准备」= 进战斗；到结算 = 已打完；
        #    两者都没有 = 点进攻没生效，实测就是券不足
        seen_ready, ended = self.confirm_ready_while_waiting(ctx, timeout=20)
        if ended:
            self.dismiss_continue(ctx)
            return True

        if not seen_ready:
            img = ctx.a.screenshot()
            has_panel, sp, _, _ = atk.find_attack_btn(img)
            page = self.detect_img(img)
            # 页面对 + 20 秒没进战斗 => 点进攻没生效，实测就是券不足
            if page == "jiejie":
                ctx.log(f"    点进攻后 20 秒内既没进战斗也没到结算"
                        f"（页面={page} 面板={has_panel} 进攻分 {sp}）→ 判定结界挑战券不足")
                self._tickets_out = True
                try:
                    img.save(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                          "shots_out_of_ticket.png"))
                    ctx.log("    （现场截图已存 tasks/jiejie_tupo/shots_out_of_ticket.png）")
                except Exception:
                    pass
                return False
            ctx.log(f"    点进攻后没进战斗，页面状态不明确（{page}），继续下一格")
            return False

        if not self.wait_battle_end(ctx, timeout=180):
            ctx.log("    !! 没等到战斗结束画面")
            return False
        self.dismiss_continue(ctx)
        return True

    # ---------------- 误触弹窗（资料页 / 设置页）的恢复 ----------------
    def close_profile_if_open(self, ctx):
        """误触头像/名字会弹出「玩家资料页」或「设置页」，整层挡住后面的操作。

        识别：中央提示带暗像素偏高（实测资料页 15959，正常页面 1000~6200）。
        关闭：优先点右上 X（设置页那个红 X），失败就用系统返回键。
        """
        img = ctx.a.screenshot()
        n = atk.warning_pixels(img)
        if n < atk.PROFILE_MIN_PIXELS:
            return False
        ctx.log(f"    检测到弹窗（中央暗像素 {n}），尝试关闭")
        ctx.human.tap("dialog_close", *ui.TAP_DIALOG_CLOSE, note="关弹窗")
        ctx.sleep(1.5)
        n2 = atk.warning_pixels(ctx.a.screenshot())
        if n2 < atk.PROFILE_MIN_PIXELS:
            ctx.log(f"    弹窗已关闭（{n} -> {n2}）")
            return True
        # X 没点中，退回系统返回键
        ctx.log("    X 没关掉，改用系统返回键")
        ctx.a.key("KEYCODE_BACK")
        ctx.sleep(2.0)
        n3 = atk.warning_pixels(ctx.a.screenshot())
        ctx.log(f"    返回键后中央暗像素 {n3}")
        return n3 < atk.PROFILE_MIN_PIXELS

    def confirm_ready_while_waiting(self, ctx, timeout=20):
        """等「准备」按钮出现并点掉。

        返回 (是否见过准备画面, 是否已到结算画面)。
        两种情况都不出现 -> 说明点进攻没生效（券不足），由调用方判定。
        实测战斗启动很快（点准备后 4~6 秒就进战斗），20 秒足够。
        """
        from tasks.event_dungeon.game import Game
        g = Game(adb=ctx.a, human=ctx.human, debug=False, verbose=False)
        g.log = lambda m: None
        seen = False
        t0 = time.time()
        while time.time() - t0 < timeout:
            if ctx.stopped():
                return seen, False
            img = ctx.a.screenshot()
            if g.is_end_screen(img) >= 0.72:
                ctx.log("    已到结算画面")
                return seen, True
            ok, s, x, y = atk.find_ready_btn(img)
            if ok:
                seen = True
                ctx.log(f"    队伍确认画面（准备按钮分 {s}），点「准备」")
                ctx.human.tap("ready", x, y, note="准备")
            time.sleep(0.6)
        if not seen:
            ctx.log(f"    {timeout}s 内没出现准备画面，也没进结算")
        return seen, False

    def wait_battle_end(self, ctx, timeout=120):
        """等「点击屏幕继续」出现（复用活动任务的文字模板）。"""
        from tasks.event_dungeon.game import Game
        g = Game(adb=ctx.a, human=ctx.human, debug=False, verbose=False)
        g.log = lambda m: None
        t0 = time.time()
        while time.time() - t0 < timeout:
            if ctx.stopped():
                return False
            img = ctx.a.screenshot()
            s = g.is_end_screen(img)
            if s >= 0.72:
                ctx.log(f"    战斗结束（文字分 {s:.3f}，用时 {time.time()-t0:.1f}s）")
                return True
            time.sleep(0.6)
        return False

    def dismiss_continue(self, ctx, tries=4):
        """点掉「点击屏幕继续」，可点多次。"""
        from tasks.event_dungeon.game import Game
        g = Game(adb=ctx.a, human=ctx.human, debug=False, verbose=False)
        g.log = lambda m: None
        for _ in range(tries):
            if ctx.stopped():
                return False
            img = ctx.a.screenshot()
            if g.is_end_screen(img) < 0.72:
                return True
            ctx.human.tap("dismiss", 300, 950, note="点掉继续")
            ctx.sleep(1.4)
        return False

    # ---------------- 刷新 ----------------
    def wait_refresh(self, ctx, timeout=20):
        """等自动刷新：出现较多亮格子即为刷新完成。"""
        t0 = time.time()
        while time.time() - t0 < timeout:
            if ctx.stopped():
                return False
            cells = atk.scan_cells(ctx.a.screenshot())
            bright = sum(1 for c in cells if c[3])
            if bright >= 5:
                ctx.log(f"  已自动刷新（可打 {bright} 个）")
                return True
            time.sleep(1.0)
        return False

    def tap_refresh(self, ctx):
        ctx.human.tap("refresh", *ui.TAP_REFRESH, note="刷新")
        ctx.sleep(2.0)
        # 有二次确认弹窗就点「确定」（判据：浅色面板出现且没有进攻按钮）
        img = ctx.a.screenshot()
        has_attack, s1, _, _ = atk.find_attack_btn(img)
        cover = float(np.asarray(img.crop((700, 300, 1250, 800)).convert("L"),
                                 dtype=np.float32).mean())
        if (not has_attack) and cover > 120:
            ctx.log(f"  出现刷新确认弹窗（面板亮度 {cover:.0f}），点「确定」")
            ctx.human.tap("refresh_ok", *ui.TAP_REFRESH_OK, note="确定")
            ctx.sleep(3.0)
