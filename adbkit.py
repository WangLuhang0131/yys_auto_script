# -*- coding: utf-8 -*-
"""adb 工具层：截图（PIL Image）、点击、长按、滑动。

只依赖标准库 + Pillow。所有坐标以【横屏 1920x1080】游戏画面为基准，
adb input 需要的坐标由 screen_xy() 自动换算。
"""
from __future__ import annotations

import subprocess
import threading
import time

from PIL import Image

# ---------------- 配置 ----------------
ADB = r"E:\MuMuPlayer\nx_main\adb.exe"
SERIAL = "emulator-5554"          # MuMu 12 默认；可改
GAME_W, GAME_H = 1920, 1080       # 游戏画面（横屏）逻辑分辨率

# 全局串行锁：多个线程（主任务 + 弹窗看门狗）同时跑 adb 会让 screencap 返回空包，
# 所以所有 adb 调用一律排队执行。
_ADB_LOCK = threading.Lock()


class Adb:
    def __init__(self, adb_path: str = ADB, serial: str = SERIAL, rotate: bool = True,
                 coord_mode: str = "identity", shot_mode: str = "color"):
        self.adb = adb_path
        self.serial = serial
        self.rotate = rotate          # 截图旋转成横屏
        self.coord_mode = coord_mode  # identity=直接用横屏坐标 / portrait=换算成竖屏坐标
        self.shot_mode = shot_mode    # color=PNG彩色(准) / raw=原始帧灰度(快3倍)
        self._cap_size = None         # (w, h) 旋转后的截图尺寸

    # ---------- 底层 ----------
    def raw(self, *args: str, timeout: float = 30) -> bytes:
        # 排队执行：多线程同时调 adb 会互相干扰（screencap 返回空包）
        with _ADB_LOCK:
            p = subprocess.run([self.adb, "-s", self.serial, *args],
                               capture_output=True, timeout=timeout)
        return p.stdout

    def shell(self, cmd: str, timeout: float = 30) -> str:
        return self.raw("shell", cmd, timeout=timeout).decode("utf-8", "replace").strip()

    # ---------- 截图 ----------
    def _raw_frame(self, retries: int = 4):
        """取原始帧 (w, h, memoryview)。比 PNG 快约 3 倍（实测 334ms vs 939ms）。"""
        import struct
        last = None
        for _ in range(retries):
            d = self.raw("exec-out", "screencap")
            try:
                if len(d) < 16:
                    raise ValueError(f"帧太短 {len(d)}")
                w, h, fmt = struct.unpack("<III", d[:12])
                off = 12
                if fmt == 2:
                    off = 16
                if not (0 < w < 5000 and 0 < h < 5000) or len(d) - off < w * h * 4:
                    raise ValueError(f"帧头异常 w={w} h={h} fmt={fmt} len={len(d)}")
                return w, h, memoryview(d)[off:off + w * h * 4]
            except Exception as e:
                last = e
                time.sleep(0.8)
        raise RuntimeError(f"screencap(raw) 失败: {last}")

    def grab_land(self, box=None, retries: int = 4, raw: bool = True):
        """
        截图并转成横屏（1920x1080）RGB。
        box 为【横屏坐标】(x1,y1,x2,y2)，只取该区域。
        raw=True 时走原始帧（快 3 倍）；raw=False 走 PNG（更兼容）。
        """
        if not raw:
            return self._grab_png(box, retries)

        import numpy as np
        w, h, buf = self._raw_frame(retries)      # 竖屏: w=1080, h=1920
        arr = np.frombuffer(buf, dtype=np.uint8).reshape(h, w, 4).astype(np.float32)
        # 与 PIL convert("L") 一致的灰度（保证判据阈值通用）
        gray = (arr[:, :, 0] * 0.299 + arr[:, :, 1] * 0.587 + arr[:, :, 2] * 0.114)

        if self.rotate and h > w:
            if box:
                x1, y1, x2, y2 = box
                x1 = max(0, min(w, x1)); x2 = max(0, min(w, x2))
                y1 = max(0, min(h, y1)); y2 = max(0, min(h, y2))
                # 横屏(x,y) -> 竖屏(px,py): px = x, py = w-1-y
                sub = gray[x1:x2, w - y2:w - y1]
            else:
                sub = gray
            # 竖屏转置 + 列翻转 = 横屏（横屏(x,y) = 竖屏(x, w-1-y)）
            land = np.ascontiguousarray(sub.T[:, ::-1])
            return Image.fromarray(land.astype(np.uint8), "L")

        if box:
            x1, y1, x2, y2 = box
            sub = gray[y1:y2, x1:x2]
        else:
            sub = gray
        return Image.fromarray(np.ascontiguousarray(sub).astype(np.uint8), "L")

    def _grab_png(self, box=None, retries: int = 8):
        import io
        last_err = None
        for i in range(retries):
            data = self.raw("exec-out", "screencap", "-p")
            try:
                img = Image.open(io.BytesIO(data))
                break
            except Exception as e:
                last_err = e
                # 空包是模拟器的偶发问题，退避重试；重试次数给足
                time.sleep(0.4 + 0.3 * i)
        else:
            raise RuntimeError(f"screencap(png) 失败: {last_err}")
        portrait = img.height > img.width
        if portrait and self.rotate:
            W, H = img.size
            if box:
                x1, y1, x2, y2 = box
                x1 = max(0, min(W, x1)); x2 = max(0, min(W, x2))
                y1 = max(0, min(H, y1)); y2 = max(0, min(H, y2))
                crop = img.crop((W - y2, x1, W - y1, x2))
                return crop.transpose(Image.ROTATE_270).convert("RGB")
            img = img.rotate(-90, expand=True)
        elif box:
            img = img.crop(box)
        return img.convert("RGB")

    def screenshot(self) -> Image.Image:
        """返回整屏横屏（1920x1080）图像。
        shot_mode='color' 走 PNG（彩色，判据更准）；'raw' 走原始帧（灰度，快约 3 倍）。"""
        if self.shot_mode == "raw":
            return self.grab_land(None, raw=True)
        return self.grab_land(None, raw=False)


    # ---------- 坐标换算 ----------
    def screen_xy(self, x: int, y: int):
        """游戏横屏坐标 (1920x1080) -> adb input 坐标。
        实测（MuMu 12 / Android 12）：`input tap` 直接使用横屏游戏坐标，
        无需按旋转换算。若换模拟器后点击失灵，可改用 rotate_to_portrait()。"""
        if self.coord_mode == "identity":
            return int(round(x)), int(round(y))
        # portrait 模式：竖屏物理坐标 = (1080-1-y, x)
        return int(round(GAME_H - 1 - y)), int(round(x))

    # ---------- 操作 ----------
    def tap(self, x: int, y: int, delay: float = 0.35):
        sx, sy = self.screen_xy(x, y)
        self.shell(f"input tap {sx} {sy}")
        time.sleep(delay)

    def long_press(self, x: int, y: int, ms: int = 700):
        sx, sy = self.screen_xy(x, y)
        self.shell(f"input swipe {sx} {sy} {sx} {sy} {ms}")
        time.sleep(0.4)

    def swipe(self, x1, y1, x2, y2, ms: int = 300):
        a = self.screen_xy(x1, y1)
        b = self.screen_xy(x2, y2)
        self.shell(f"input swipe {a[0]} {a[1]} {b[0]} {b[1]} {ms}")
        time.sleep(0.35)

    def key(self, code: str = "KEYCODE_BACK"):
        self.shell(f"input keyevent {code}")
        time.sleep(0.4)

    # ---------- 常用信息 ----------
    def current_app(self) -> str:
        out = self.shell("dumpsys window displays | grep mCurrentFocus")
        return out

    def test(self):
        img = self.screenshot()
        print("screencap size:", img.size)
        print("screen_xy(100,100) ->", self.screen_xy(100, 100))
        print("focus:", self.current_app())


if __name__ == "__main__":
    a = Adb()
    a.test()
