# -*- coding: utf-8 -*-
"""公共：把游戏送回「庭院」主界面。

为什么需要它：
  任务跑完常常停在半路（结界突破页 / 活动页 / 探索页），
  下一个任务从这些页面启动时容易认不出来（unknown），于是瞎点、卡住。
  统一在任务结束后回庭院，就能保证「每次启动都在同一个已知状态」。

怎么回：**循环判断当前页面 + 点该页面的退出键**，而不是背一条固定路线。
  庭院        -> 完成
  结界突破页  -> 右上 X
  探索页      -> 左上返回
  活动总览/活动详情/备战页 -> 左上返回
  战斗/结算   -> 先点掉「点击屏幕继续」，再回上一步
  认不出      -> 先关弹窗（资料页/设置页），再尝试系统返回键，最后才盲点

页面识别用的模板都放在各任务自己的 templates/ 里（保持任务隔离），
这里只按「任务注册表」的顺序去问各家模板，谁命中算谁。
"""
from __future__ import annotations

import os
import time

import vision

# 各任务模板目录（相对项目根）。删掉某个任务目录，这里对应项会失效但不会报错。
TASK_TPL_DIRS = [
    ("jiejie_tupo", "tasks/jiejie_tupo/templates"),
    ("event_dungeon", "tasks/event_dungeon/templates"),
]

# 页面判据：(页面名, 模板文件名, 搜索区, 阈值)
PAGE_RULES = [
    ("courtyard", "t_courtyard_bar.png", (60, 830, 1880, 1070), 0.60),
    ("jiejie", "t_courtyard_bar.png", None, None),        # 占位，下面单独处理
]

# 各页面上的退出坐标
TAP_BACK = (57, 42)              # 左上返回（探索页 / 活动页都有）
TAP_JJ_CLOSE = (1785, 190)       # 结界突破页 右上 X
TAP_DIALOG_CLOSE = (1780, 188)   # 设置页 右上 X
TAP_PROFILE_CLOSE = (1855, 205)  # 玩家资料页 右上 X
TAP_CENTER = (960, 540)

PROFILE_MIN_PIXELS = 10000       # 中央暗像素：判定弹窗（资料页/设置页）
DIALOG_DISMISS_POINT = (620, 430, 1300, 500)


def _tpl(task_dir: str, name: str):
    """task_dir 已是 tasks/<任务>/templates 这样的完整相对路径。

    用 res_root()：打包成 exe 后模板在解包目录里，不是脚本目录。
    """
    try:
        from core.paths import res_root
        root = res_root()
    except Exception:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, task_dir, name)


def _match(img, task_dir, name, region, th=0.60):
    path = _tpl(task_dir, name)
    if not os.path.exists(path):
        return -1.0
    try:
        s, _, _ = vision.match(img, path, region=region)
        return s
    except Exception:
        return -1.0


def warn_pixels(img):
    a = img.crop(DIALOG_DISMISS_POINT).convert("L")
    import numpy as np
    arr = np.asarray(a, dtype=np.float32)
    return int((arr < 60).sum())


class Returner:
    """把游戏送回庭院的循环式导航器。"""

    def __init__(self, adb, human, log, max_steps=10):
        self.a = adb
        self.human = human
        self.log = log
        self.max_steps = max_steps

    # ---------- 页面识别 ----------
    def detect(self, img=None):
        img = img or self.a.screenshot()
        # 1) 庭院
        s = _match(img, TASK_TPL_DIRS[0][1], "t_courtyard_bar.png", (60, 830, 1880, 1070))
        if s >= 0.60:
            return "courtyard"
        # 2) 结界突破页：攻破记录 / 刷新按钮 / 标题
        for name, reg in (("t_record_label.png", (200, 730, 470, 850)),
                          ("t_refresh_btn.png", (1380, 780, 1780, 950)),
                          ("t_title_jiejie.png", (700, 95, 1200, 185))):
            if _match(img, TASK_TPL_DIRS[0][1], name, reg) >= 0.60:
                return "jiejie"
        # 3) 攻击面板开着 = 结界突破页
        try:
            import sys
            try:
                from core.paths import res_root
                root = res_root()
            except Exception:
                root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if root not in sys.path:
                sys.path.insert(0, root)
            from tasks.jiejie_tupo import attack as atk
            if atk.find_attack_btn(img)[0]:
                return "jiejie"
        except Exception:
            pass
        # 4) 探索页
        if _match(img, TASK_TPL_DIRS[0][1], "t_explore_bar.png",
                  (400, 930, 750, 1040)) >= 0.60:
            return "explore"
        # 5) 活动页（总览 / 详情 / 备战）
        for name, reg in (("t_overview.png", (200, 10, 520, 100)),
                          ("t_detail.png", (200, 5, 620, 110)),
                          ("t_challenge.png", (1640, 790, 1815, 920))):
            if _match(img, TASK_TPL_DIRS[1][1], name, reg) >= 0.70:
                return "activity"
        # 6) 结算画面（胜利/点击屏幕继续）
        try:
            from tasks.event_dungeon.game import Game
            g = Game(adb=self.a, debug=False, verbose=False)
            if g.is_end_screen(img) >= 0.72:
                return "settle"
        except Exception:
            pass
        return "unknown"

    # ---------- 弹窗处理 ----------
    def dismiss_dialog(self):
        img = self.a.screenshot()
        n = warn_pixels(img)
        if n < PROFILE_MIN_PIXELS:
            return False
        self.log(f"    检测到弹窗（中央暗像素 {n}），关闭")
        self.human.tap("dialog_close", *TAP_DIALOG_CLOSE)
        time.sleep(1.5)
        if warn_pixels(self.a.screenshot()) < PROFILE_MIN_PIXELS:
            return True
        self.human.tap("profile_close", *TAP_PROFILE_CLOSE)
        time.sleep(1.5)
        if warn_pixels(self.a.screenshot()) < PROFILE_MIN_PIXELS:
            return True
        self.a.key("KEYCODE_BACK")
        time.sleep(1.8)
        return warn_pixels(self.a.screenshot()) < PROFILE_MIN_PIXELS

    # ---------- 主循环 ----------
    def go_home(self):
        """返回 (是否成功回到庭院, 步数)。"""
        for step in range(1, self.max_steps + 1):
            page = self.detect()
            self.log(f"  回庭院 第{step}步：当前={page}")
            if page == "courtyard":
                return True, step
            if page == "jiejie":
                self.human.tap("jj_close", *TAP_JJ_CLOSE, note="关结界突破页")
                time.sleep(2.5)
            elif page == "explore":
                self.human.tap("back", *TAP_BACK, note="返回")
                time.sleep(2.5)
            elif page == "activity":
                self.human.tap("back", *TAP_BACK, note="返回")
                time.sleep(2.5)
            elif page == "settle":
                self.human.tap("dismiss", 300, 950, note="点掉结算")
                time.sleep(1.5)
            else:
                if self.dismiss_dialog():
                    continue
                # 认不出：先试系统返回键（比盲点稳）
                self.log("    认不出页面，按系统返回键试试")
                self.a.key("KEYCODE_BACK")
                time.sleep(2.0)
                p2 = self.detect()
                if p2 == "unknown":
                    self.human.tap("center", *TAP_CENTER, note="兜底点击")
                    time.sleep(1.5)
        return False, self.max_steps
