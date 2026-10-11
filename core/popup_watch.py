# -*- coding: utf-8 -*-
"""公共：干扰弹窗看门狗（独立线程）。

为什么需要独立线程：
  「悬赏封印」这类弹窗会在战斗中弹出来，**把整个战斗卡住**（游戏等玩家点确定），
  而主任务的循环此时正卡在"等战斗结束"上，根本不知道有弹窗。
  所以必须有个独立线程一直在旁边盯着，一出现就点掉。

识别判据（实测）：弹窗右上角有个亮品红色的 X，
  该区域"品红像素占比"有弹窗 0.055，其它任何画面都是 0.000 —— 非常干净。
点击点：品红像素的重心（比写死坐标稳）。

用法：
    w = PopupWatcher(adb, human, log)
    w.start()
    ... 跑任务 ...
    w.stop()
"""
from __future__ import annotations

import threading
import time

import numpy as np

# X 号搜索区（1920 基准）
R_X = (1080, 110, 1260, 250)
PINK_MIN_RATIO = 0.015      # 品红像素占比阈值（有 0.055 / 无 0.000）
PINK_MIN_PIXELS = 150       # 绝对像素数下限，防小图误判
POLL_INTERVAL = 1.2         # 轮询间隔（秒）


class PopupWatcher:
    """盯着屏幕，发现干扰弹窗就点掉。"""

    def __init__(self, adb, human, log, poll=POLL_INTERVAL, tap_lock=None):
        self.a = adb
        self.human = human
        self.log = log
        self.poll = poll
        self.tap_lock = tap_lock        # 可选：和主线程共用的"点击互斥锁"
        self._stop = threading.Event()
        self._thread = None
        self.closed_count = 0
        self._seen = 0                  # 连续检测到弹窗的次数（避免瞬时误判）

    # ---------- 识别 ----------
    def find_popup(self, img):
        """返回 (是否检测到, 品红像素重心 x, y, 占比)。

        坐标按图片实际尺寸换算（兼容 1920x1080 的实机截图和更大的参考图）。
        """
        s = img.size[0] / 1920.0
        box = (int(R_X[0] * s), int(R_X[1] * s), int(R_X[2] * s), int(R_X[3] * s))
        a = np.asarray(img.crop(box).convert("RGB"), dtype=np.float32)
        pink = ((a[:, :, 0] > 165) & (a[:, :, 2] > 105) & (a[:, :, 1] < 145)
                & (a[:, :, 0] - a[:, :, 1] > 55))
        n = int(pink.sum())
        if n < PINK_MIN_PIXELS:
            return False, 0, 0, 0.0
        ys, xs = np.nonzero(pink)
        # 换算回 1920 基准（点击用的是基准坐标）
        cx = R_X[0] + int(xs.mean() / s)
        cy = R_X[1] + int(ys.mean() / s)
        return True, cx, cy, n / pink.size

    # ---------- 线程 ----------
    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True,
                                        name="popup-watcher")
        self._thread.start()

    def stop(self, timeout=3.0):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=timeout)

    @property
    def running(self):
        return bool(self._thread and self._thread.is_alive())

    def _loop(self):
        while not self._stop.is_set():
            try:
                img = self.a.screenshot()
                ok, cx, cy, ratio = self.find_popup(img)
                if ok:
                    self._seen += 1
                    # 连续两次确认后再点，避免把偶发画面误当弹窗
                    if self._seen >= 2:
                        self.log(f"  [看门狗] 发现干扰弹窗（品红占比 {ratio:.3f}），"
                                 f"点 X ({cx},{cy})")
                        if self.tap_lock:
                            with self.tap_lock:
                                self.a.tap(cx, cy, delay=0.2)
                        else:
                            self.a.tap(cx, cy, delay=0.2)
                        self.closed_count += 1
                        self._seen = 0
                        time.sleep(1.0)
                        # 点完复查一次，确认真的关掉了
                        img2 = self.a.screenshot()
                        ok2, _, _, r2 = self.find_popup(img2)
                        self.log(f"  [看门狗] 复查：{'仍然存在' if ok2 else '已关闭'}"
                                 f"（占比 {r2:.3f}）")
                else:
                    self._seen = 0
            except Exception as e:
                self.log(f"  [看门狗] 异常：{e}")
            self._stop.wait(self.poll)
