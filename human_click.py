# -*- coding: utf-8 -*-
"""拟人化操作层：把固定坐标点击变成「随机落点 + 随机间隔」。

设计要点：
1. tap(target, x, y, box=...) 在安全矩形内按高斯分布随机取点，越靠中心概率越高。
   - 不传 box 时用自适应抖动半径：小按钮自动收窄，不会点到边缘。
   - 传了 box 就在该矩形内随机（任务自带的坐标表可以这样用）。
2. 点与点之间加入随机抖动（150~450ms），并且偶尔插入一次「较长停顿」，
   模拟人手指离开屏幕、思考一下再点的节奏。
3. 随机落点全部记录在日志里，方便出问题时复核点到哪了。
"""
from __future__ import annotations

import random
import time

# ---------------- 预设目标的安全矩形（横屏 1920x1080 坐标） ----------------
# 都是「实测亮像素范围再内缩」得到，保证抖动后仍落在同一个按钮上。
JITTER_BOX = {
    "back":      (38, 28, 76, 58),        # 返回箭头
    "go":        (1695, 900, 1760, 950),  # 活动总览页 前往活动
    "guji":      (315, 412, 375, 450),    # 活动详情页 古迹演武
    "challenge": (1700, 838, 1755, 880),  # 备战页 挑战
    "dismiss":   (200, 900, 420, 1000),   # 结束画面点背景
    "center":    (900, 500, 1020, 580),   # 画面中央
}

# 这几个目标的抖动半径。
# 教训：一开始给得偏大（back 16x12、go 28x20），日志里落点能漂 10~20 像素，
# 对着小按钮或贴边按钮很危险（容易点到旁边的头像/仓库）。现在统一收小。
JITTER_RADIUS = {
    "back":      (6, 5),
    "go":        (10, 7),
    "guji":      (9, 7),
    "challenge": (12, 9),
    "dismiss":   (60, 30),
    "center":    (40, 28),
}

# 只给一个坐标、没给安全矩形时的自适应抖动上限
SELF_JITTER_MAX = (6, 5)


class Human:
    """拟人化点击器。包装 Adb，提供随机落点点击与随机停顿。"""

    def __init__(self, adb, log=None, enabled=True, seed=None, tap_lock=None):
        self.a = adb
        self.log = log or (lambda *a, **k: None)
        self.enabled = enabled
        self.rng = random.Random(seed)
        self.tap_count = 0
        self.last_point = None
        # 多线程共用时的点击互斥锁（看门狗线程 + 主任务线程）
        self.tap_lock = tap_lock

    # ---------- 随机点 ----------
    def pick_point(self, target: str = "", box=None, radius=None):
        """在安全矩形内取随机点。box=None 时查预设表。"""
        if box is None:
            box = JITTER_BOX.get(target)
        if box is None:
            raise KeyError(f"没有为 {target!r} 定义安全矩形，也没有传 box=")

        x1, y1, x2, y2 = box
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        if not self.enabled:
            return int(cx), int(cy)

        if radius is None:
            radius = JITTER_RADIUS.get(target)
        if radius is None:
            # 自适应：小按钮自动收窄
            radius = (max(4, int((x2 - x1) * 0.20)), max(3, int((y2 - y1) * 0.20)))
        rx, ry = radius
        dx = self.rng.gauss(0, rx / 2.2)
        dy = self.rng.gauss(0, ry / 2.2)
        x = int(round(min(max(cx + dx, max(x1, cx - rx)), min(x2, cx + rx))))
        y = int(round(min(max(cy + dy, max(y1, cy - ry)), min(y2, cy + ry))))
        return x, y

    # ---------- 操作 ----------
    def tap(self, target, x=None, y=None, box=None, radius=None, note="", delay=True):
        """随机落点点击。三种用法：
            human.tap("challenge")                          # 用预设表
            human.tap("cell", 865, 285)                     # 直接给坐标（自适应抖动）
            human.tap("cell", 865, 285, box=(800,240,930,330))  # 指定安全矩形
        """
        if x is None or y is None:
            x, y = self.pick_point(target, box=box, radius=radius)
        elif box is not None:
            x, y = self.pick_point(target, box=box, radius=radius)
        elif self.enabled:
            # 只给了一个点：用很小的自适应抖动（±6 × ±5），保证还在按钮内
            mx, my = SELF_JITTER_MAX
            x += int(round(self.rng.gauss(0, mx / 2.5)))
            y += int(round(self.rng.gauss(0, my / 2.5)))

        if self.tap_lock is not None:
            with self.tap_lock:
                self.a.tap(x, y, delay=0)
        else:
            self.a.tap(x, y, delay=0)
        self.tap_count += 1
        self.last_point = (target, x, y)
        if note or self.tap_count % 20 == 1:
            self.log(f"    点击 {target} -> ({x},{y}) {note}".rstrip())
        if delay:
            time.sleep(self.rng.uniform(0.15, 0.45))
        return x, y

    def tap_image(self, img, target, tpl_path, region=None, th=0.60,
                  mask_path=None, note="", delay=True):
        """**按图找点**：在画面里模板匹配到目标后再点它。

        为什么需要：有些界面的按钮位置不固定（比如庭院里的物件会随布置移动），
        写死坐标很容易点到别的东西（实测就把"探索"旁边的按钮点开过）。
        用法：
            human.tap_image(img, "explore", tpl("t_explore_lantern.png"),
                            region=(1000, 280, 1250, 420))
        返回 (是否点到, 匹配分, x, y)
        """
        import vision
        s, x, y = vision.match(img, tpl_path, region=region, mask_path=mask_path)
        if s < th:
            self.log(f"    找不到 {target}（分数 {s:.3f} < {th}），跳过")
            return False, round(float(s), 3), 0, 0
        self.tap(target, x, y, note=f"{note or target}(按图定位 {s:.2f})", delay=delay)
        return True, round(float(s), 3), x, y

    def pause(self, lo=0.15, hi=0.45):
        """短随机停顿。"""
        time.sleep(self.rng.uniform(lo, hi))

    def maybe_long_pause(self, chance=0.12, lo=0.8, hi=2.2):
        """按概率插入一次较长停顿，模拟「手指离开屏幕」的节奏。"""
        if self.enabled and self.rng.random() < chance:
            t = self.rng.uniform(lo, hi)
            self.log(f"    随机长停顿 {t:.1f}s")
            time.sleep(t)
            return t
        return 0.0

    def stats(self):
        return {"taps": self.tap_count}
