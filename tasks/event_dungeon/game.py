# -*- coding: utf-8 -*-
"""游戏状态识别 + 活动刷取主流程。

状态判据（1920x1080 横屏坐标）：
  PREP     备战页：右下「挑战」键模板匹配分数高
  OVERVIEW 活动总览：顶部「活动总览」标题模板匹配分数高
  DETAIL   活动详情：顶部「拾此一瞬」标题模板匹配分数高
  BATTLE   战斗中：无上述模板，且挑战键区域偏亮/画面非静止
  END      战斗结束（点击屏幕继续）：无上述模板，挑战键区域偏暗且画面静止

坐标依据实测：
  前往活动按钮 (1727,925)   古迹演武入口 (420,435)   挑战键 (1727,857)
"""
from __future__ import annotations

import os
import sys
import time

import numpy as np
from PIL import Image

# 任务自包含：只依赖项目根目录的公共工具（adbkit / vision / humanize）
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import vision
from adbkit import Adb, GAME_W, GAME_H
from human_click import Human

# 本任务自带模板目录（删掉本任务目录即可，不影响其它任务）
try:
    from core.paths import res_root
    TPL = os.path.join(res_root(), "tasks", "event_dungeon", "templates")
except Exception:
    TPL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


def tpl(name: str) -> str:
    return os.path.join(TPL, name)

# ---------------- 可调参数 ----------------
TH_PREP = 0.70           # 挑战键匹配阈值
TH_OVERVIEW = 0.70       # 活动总览标题
TH_DETAIL = 0.70         # 活动详情标题

R_CHALLENGE = (1640, 790, 1815, 920)     # 挑战键搜索区
R_OVERVIEW_TITLE = (200, 10, 520, 100)   # 活动总览标题搜索区
R_DETAIL_TITLE = (200, 5, 620, 110)      # 活动详情标题搜索区
R_CHALLENGE_LUM = (1650, 800, 1810, 915) # 挑战键亮度区（区分战斗/结束画面）
R_BOTTOM = (0, 890, 1920, 1080)          # 底部区域（含挑战键）
R_END_TEXT = (700, 960, 1230, 1080)      # 「点击屏幕继续」搜索区
R_END_STRIP = (0, 860, 1920, 1080)       # 快速检测条带（含挑战键 + 结束文字）
R_NO_ITEM_TOAST = (650, 270, 1300, 390)  # 「琥珀卷轴不足」等道具提示搜索区
R_COUNT_ZERO = (1180, 15, 1330, 85)      # 备战页「剩余挑战次数」数字区

TH_END_TEXT = 0.72                       # 结束画面文字匹配阈值
TH_END_STRIP = 0.80                      # 条带快速判据阈值（略低，后面会用整屏复核）
TH_NO_ITEM = 0.80                        # 道具不足提示阈值（实测有 1.0 / 无 ≤0.55）
TH_COUNT_ZERO = 0.75                     # 「次数为 0」阈值（实测 1.0 / 非0 ≤0.42）

# 点击目标名（实际随机落点由 humanize.JITTER_BOX 决定）
T_GO_ACTIVITY = "go"            # 活动总览页 前往活动
T_GUJI = "guji"                 # 活动详情页 古迹演武
T_CHALLENGE = "challenge"       # 备战页 挑战
T_CENTER = "center"             # 画面中央（兜底）
T_END_DISMISS = "dismiss"       # 结束画面点背景

try:
    from core.paths import app_path
    SHOTDIR = app_path("shots")
except Exception:
    SHOTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")
DEBUG = True


class Game:
    def __init__(self, adb_path=None, serial=None, debug=True, verbose=True,
                 jitter=True, seed=None, human=None, adb=None):
        if adb is not None:
            self.a = adb
        else:
            self.a = Adb(adb_path, serial) if adb_path else Adb()
        self.debug = debug
        self.verbose = verbose
        self.shot_seq = 0
        # 拟人化点击层：固定坐标 -> 安全矩形内随机落点 + 随机间隔
        self.human = human or Human(self.a, log=lambda m: self.log(m),
                                    enabled=jitter, seed=seed)

    # ---------- 基础 ----------
    def log(self, msg, ascii_console=False):
        """打印日志。ascii_console=True 时控制台走英文（cmd 不会乱码）。"""
        if self.verbose:
            if ascii_console:
                try:
                    from ascii_out import to_ascii
                    msg = to_ascii(msg)
                except Exception:
                    pass
            print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

    def tap(self, target: str, delay=True, note: str = ""):
        """随机落点点击（所有点击都走这里，保证不会每次点同一个像素）。"""
        return self.human.tap(target, delay=delay, note=note)

    def shot(self, name):
        if not self.debug:
            return
        os.makedirs(SHOTDIR, exist_ok=True)
        self.shot_seq += 1
        p = os.path.join(SHOTDIR, f"dbg_{self.shot_seq:04d}_{name}.png")
        self.a.screenshot().save(p)

    # ---------- 状态识别 ----------
    def is_end_screen(self, img) -> float:
        """「点击屏幕继续」文字匹配分数（实测：结束画面≈1.0，其他画面≤0.17）。"""
        s, _, _ = vision.match(img, tpl("end_text.png"), region=R_END_TEXT,
                               mask_path=tpl("end_text_mask.png"))
        return s

    def is_no_item_toast(self, img) -> float:
        """「琥珀卷轴不足」道具用完提示的匹配分数。

        实测：有提示 1.000，无提示 ≤0.553；必须带掩膜（只匹配文字笔画），
        否则备战页大片低对比背景会拿到 0.75 的假高分。
        注意：这个提示只显示一两秒，是**兜底**判据，主判据用 challenge_count_zero()。
        """
        s, _, _ = vision.match(img, tpl("t_no_item_toast.png"), region=R_NO_ITEM_TOAST,
                               mask_path=tpl("t_no_item_toast_mask.png"))
        return s

    def challenge_count_zero(self, img=None) -> float:
        """备战页「剩余挑战次数 = 0」的匹配分数。

        实测：次数为 0 时 1.000，次数 296 时 0.421，其它页面 ≤0.27。
        这个判据不用抢时间（提示会秒消失），是最可靠的道具耗尽信号。
        """
        img = img or self.a.screenshot()
        s, _, _ = vision.match(img, tpl("t_count_zero.png"), region=R_COUNT_ZERO)
        return s

    def challenge_ready(self, img=None):
        """挑战键是否为「可点」状态（金色亮字）。
        实测灰度 >170 的像素占比：可点 0.19，灰掉/无此键 ≤0.08。
        返回 (是否可点, 亮像素占比)"""
        img = img or self.a.screenshot()
        a = np.asarray(img.crop(R_CHALLENGE).convert("L"), dtype=np.float32)
        ratio = float((a > 170).mean())
        return ratio >= 0.12, round(ratio, 4)

    # ---------- 结束画面快速检测 ----------
    def end_text_in(self, img, y_offset: int = 0) -> float:
        """在（可能被裁剪过的）图像里找「点击屏幕继续」，返回匹配分数。"""
        if y_offset:
            bx1, by1, bx2, by2 = R_END_TEXT
            reg = (bx1, by1 - y_offset, bx2, by2 - y_offset)
        else:
            reg = R_END_TEXT
        s, _, _ = vision.match(img, tpl("end_text.png"), region=reg,
                               mask_path=tpl("end_text_mask.png"))
        return s

    def wait_end_screen(self, timeout=240, interval=0.25, on_poll=None):
        """
        专为结束画面优化的等待：
          1) 只截底部条带（3 倍速），条带分数够高再用整屏复核；
          2) 每 2 秒兜底做一次整屏判定，保证不误判也不会漏。
        返回 (是否检测到, 分数)
        """
        t0 = time.time()
        while time.time() - t0 < timeout:
            strip = self.a.grab_land(R_END_STRIP)
            s_strip = self.end_text_in(strip, y_offset=R_END_STRIP[1])
            if s_strip >= TH_END_STRIP:
                full = self.a.screenshot()
                s_full = self.end_text_in(full)
                if s_full >= TH_END_TEXT:
                    return True, round(s_full, 3)
            # 兜底整屏判定（防条带漏检）
            if time.time() - t0 > 2.5:
                st, info = self.detect()
                if st in ("end", "prep"):
                    return st == "end", info.get("end_text", -1)
                t0 = time.time()          # 重置兜底计时
            if on_poll:
                on_poll()
            time.sleep(interval)
        return False, -1

    def detect(self, img=None):
        """返回 (state, info)；state 为 'prep'/'overview'/'detail'/'battle'/'end'/'unknown'"""
        img = img or self.a.screenshot()

        # 1) 结束画面（点击屏幕继续）—— 必须优先，否则会被误判
        s_end = self.is_end_screen(img)
        if s_end >= TH_END_TEXT:
            return "end", {"end_text": round(s_end, 3)}

        # 2) 备战页
        s_prep, x1, y1 = vision.match(img, tpl("t_challenge.png"), region=R_CHALLENGE)
        if s_prep >= TH_PREP:
            return "prep", {"score": round(s_prep, 3), "x": x1, "y": y1}

        # 3) 活动总览 / 活动详情
        s_ov, _, _ = vision.match(img, tpl("t_overview.png"), region=R_OVERVIEW_TITLE)
        if s_ov >= TH_OVERVIEW:
            return "overview", {"score": round(s_ov, 3)}
        s_dt, _, _ = vision.match(img, tpl("t_detail.png"), region=R_DETAIL_TITLE)
        if s_dt >= TH_DETAIL:
            return "detail", {"score": round(s_dt, 3)}

        # 4) 其余按亮度区分战斗/未知（实测战斗首帧最暗约 146，备战页 ≤101）
        lum = vision.brightness(img, R_CHALLENGE_LUM)
        if lum > 155:
            return "battle", {"lum": round(lum, 1)}
        return "unknown", {"lum": round(lum, 1), "end_text": round(s_end, 3),
                           "prep": round(s_prep, 3), "ov": round(s_ov, 3),
                           "dt": round(s_dt, 3)}

    def wait_state(self, states, timeout=30, interval=0.2, img0=None):
        """等待进入指定状态集合，返回 (state, img, info)。超时返回 ('timeout', 最后一帧, {})。
        单帧判定约 0.8s（截图是瓶颈），因此这里用短 timeout 反复调用。"""
        states = (states,) if isinstance(states, str) else tuple(states)
        t0 = time.time()
        while time.time() - t0 < timeout:
            img = img0 or self.a.screenshot()
            img0 = None
            st, info = self.detect(img)
            if st in states:
                return st, img, info
            time.sleep(interval)
        return "timeout", None, {}

    def tap_and_wait(self, target: str, want, timeout=9, tries=4, note: str = ""):
        """
        点一下目标并等待画面变成 want（单个状态或元组）。
        每次没生效就等 1.5s 再换一个随机落点重试（UI 响应偶尔会吃掉第一下）。
        返回 (state, img, info)；失败返回 ('timeout', None, {})。
        """
        want = (want,) if isinstance(want, str) else tuple(want)
        for k in range(tries):
            self.pause(0.25, 0.75)
            x, y = self.tap(target, delay=False, note=note or f"第{k+1}次")
            st, img, info = self.wait_state(want, timeout=timeout / tries, interval=0.25)
            if st in want:
                self.log(f"    {target} -> ({x},{y}) 生效，状态={st} {info}")
                return st, img, info
            self.log(f"    {target} -> ({x},{y}) 未生效（当前 {st}），换点重试")
        return "timeout", None, {}

    # ---------- 动作 ----------
    def pause(self, lo=0.15, hi=0.45):
        """拟人化随机停顿。"""
        self.human.pause(lo, hi)

    def go_to_prep(self, max_back=5):
        """把画面推进到备战页（古迹演武）。返回 True 成功。"""
        for i in range(max_back + 1):
            st, img, info = self.wait_state(("prep", "overview", "detail", "end", "battle"),
                                            timeout=12)
            self.log(f"  导航第{i+1}步: 当前状态={st} {info}")
            if st == "prep":
                return True
            if st == "overview":
                self.tap_and_wait(T_GO_ACTIVITY, ("detail", "prep"),
                                  timeout=15, note="前往活动")
            elif st == "detail":
                self.tap_and_wait(T_GUJI, "prep", timeout=15, note="古迹演武")
            elif st == "end":
                self.tap_and_wait(T_END_DISMISS, ("prep",), timeout=10, note="点掉结束画面")
            elif st == "battle":
                self.log("  仍在战斗中，等待...")
                self.wait_state(("prep", "end"), timeout=120, interval=1.0)
            else:
                self.log(f"  未知状态，点屏幕中央重试 {info}")
                self.tap(T_CENTER, note="兜底点击")
                time.sleep(1.5)
        return False

    def open_activity_and_enter(self):
        """从活动总览页 -> 活动详情 -> 古迹演武备战页。"""
        st, _, info = self.wait_state(("overview", "detail", "prep", "end"), timeout=15)
        self.log(f"活动入口状态={st} {info}")
        if st == "overview":
            st2, _, info2 = self.tap_and_wait(T_GO_ACTIVITY, ("detail", "prep"),
                                              timeout=15, note="前往活动")
            self.log(f"  进入活动详情: {st2} {info2}")
            if st2 == "detail":
                self.tap_and_wait(T_GUJI, "prep", timeout=15, note="古迹演武")
        elif st == "detail":
            self.tap_and_wait(T_GUJI, "prep", timeout=15, note="古迹演武")
        return self.wait_state(("prep",), timeout=20)

    # ---------- 一轮战斗 ----------
    def one_battle(self, battle_timeout=240, verbose=True):
        """
        在备战页点「挑战」-> 等战斗结束画面 -> 点掉 -> 回到备战页。
        返回 (成功?, 用时秒, info字典)
        """
        t_start = time.time()
        info = {}
        # 进战斗前偶尔多犹豫一下（拟人）
        self.human.maybe_long_pause(0.10)
        self.tap(T_CHALLENGE, note="挑战")
        self.log("  已点挑战")

        # 1) 等离开备战页（进入战斗）。
        # 注意：道具不足的提示（「琥珀卷轴不足」）只显示两三秒，
        # 所以点完挑战要**立刻**抢着看，别等超时再截图（那样早消失了）。
        t0 = time.time()
        entered = False
        while time.time() - t0 < 25:
            st, _, i2 = self.wait_state(("battle", "end"), timeout=1.2, interval=0.3)
            if st in ("battle", "end"):
                entered = True
                self.log(f"  已进入战斗: {st} {i2}  ({time.time()-t0:.1f}s)")
                break
            # 没进战斗：抢在提示消失前检测
            img = self.a.screenshot()
            s_toast = self.is_no_item_toast(img)
            if s_toast >= TH_NO_ITEM:
                self.log(f"  检测到「道具不足」提示（分数 {s_toast:.3f}）→ 活动道具已用完")
                return False, time.time() - t_start, {"err": "no_item",
                                                      "toast": round(s_toast, 3)}
            self.log(f"  未进入战斗（道具提示分 {s_toast:.3f}），补点一次挑战")
            self.pause(0.4, 1.1)
            self.tap(T_CHALLENGE, note="补点")
        if not entered:
            self.log("  !! 25 秒内未能进入战斗")
            return False, time.time() - t_start, {"err": "enter_failed"}

        # 2) 用「条带快速检测」等结束画面，检测到立即点击
        t0 = time.time()
        found, s_end = self.wait_end_screen(timeout=battle_timeout)
        if found:
            took = time.time() - t0
            self.log(f"  检测到结束画面（分数 {s_end}，战斗耗时 {took:.1f}s），立刻点击继续")
            if self.debug:
                self.shot("end_screen")
            info["battle_sec"] = round(took, 1)
            time.sleep(0.35)          # 等提示完全稳定，避免第一下点在过渡帧上被吞
            self.tap(T_END_DISMISS, note="点掉结束画面")
            # 结束画面可能要多点几次才生效（实测 1~3 次），
            # 每次都随机落在右下空白背景，避免点到式神立绘触发别的面板。
            for k in range(1, 6):
                st_back, img, i3 = self.wait_state(("prep", "end"), timeout=5, interval=0.25)
                if st_back == "prep":
                    break
                if self.debug:
                    self.shot(f"after_click_{k}")
                self.log(f"    第 {k} 次点击后仍在 {st_back} {i3}，再点一次")
                self.pause(0.2, 0.5)
                self.tap(T_END_DISMISS, note=f"第{k+1}次")
        else:
            # 没等到结束画面：可能已经回到备战页，也可能卡住了
            st, _, i2 = self.wait_state(("prep",), timeout=5)
            if st == "prep":
                self.log("  未检测到结束画面，但已回到备战页（视为完成）")
                info["battle_sec"] = round(time.time() - t0, 1)
            else:
                self.log("  !! 战斗超时")
                return False, time.time() - t_start, {"err": "battle_timeout"}

        # 3) 最后确认回到备战页
        st, img, i2 = self.wait_state(("prep",), timeout=15)
        if st != "prep":
            self.log(f"  未回到备战页（{st} {i2}），再补点一次")
            if self.debug and img is not None:
                self.shot("not_back_to_prep")
            self.tap(T_END_DISMISS)
            st, img, i2 = self.wait_state(("prep",), timeout=12)
            if st != "prep" and self.debug and img is not None:
                self.shot("still_not_back")
        ok = st == "prep"
        info["total_sec"] = round(time.time() - t_start, 1)
        self.log(f"  本轮{'完成' if ok else '失败'}，用时 {info['total_sec']}s")
        return ok, time.time() - t_start, info
