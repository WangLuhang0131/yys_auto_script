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

# 关键：打包成 --windowed 的 exe 后，程序自己没有控制台，
# 此时用 subprocess 启动 adb.exe 会**每调用一次就弹出一个黑窗口**（实测）。
# CREATE_NO_WINDOW 让子进程不建控制台窗口。
# （源码用 python.exe 运行时不会暴露这个问题，因为父进程有控制台可共用。）
_NO_WINDOW = 0x08000000 if hasattr(subprocess, "CREATE_NO_WINDOW") else 0

# 自愈过程的记录器：由 GUI 启动时替换成日志函数（见 core/runner.py），
# 这样"正在等设备就绪/正在重启 adb"能显示在界面上。
# 打包成 windowed exe 后没有 stdout，print 会消失，所以必须走这个回调。
def _diag_log(msg: str):
    try:
        print(f"[adb] {msg}", flush=True)
    except Exception:
        pass


_DIAG_LOG = _diag_log


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
                               capture_output=True, timeout=timeout,
                               creationflags=_NO_WINDOW)
        return p.stdout

    def shell(self, cmd: str, timeout: float = 30) -> str:
        return self.raw("shell", cmd, timeout=timeout).decode("utf-8", "replace").strip()

    # ---------- 设备就绪 / 自愈 ----------
    def device_state(self) -> str:
        """返回设备状态字符串：device / offline / unauthorized / notfound / unknown。

        刚开机时 adb 服务没跑、或者设备还在连，这里会是 offline / notfound，
        而 screencap 只会返回空包——所以报错前必须先看这个状态。
        """
        try:
            with _ADB_LOCK:
                p = subprocess.run([self.adb, "devices"], capture_output=True,
                                   timeout=20, creationflags=_NO_WINDOW)
            text = p.stdout.decode("utf-8", "replace")
        except Exception:
            return "unknown"
        for line in text.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[0] == self.serial:
                return parts[1]
        return "notfound"

    def wait_ready(self, timeout: float = 90, log=None) -> bool:
        """等设备变成 device 状态。刚重启电脑后 MuMu 自己和 adb 都要时间起来。

        中途会主动拉一把：start-server -> 重连 -> 再等。
        返回是否就绪。
        """
        t0 = time.time()
        tried_recover = False
        last = None
        while time.time() - t0 < timeout:
            st = self.device_state()
            if st == "device":
                if last is not None and log:
                    log(f"设备已就绪（{time.time()-t0:.1f}s）")
                return True
            if st != last:
                if log:
                    log(f"等待设备就绪... 当前状态={st}"
                        f"（刚重启电脑时 MuMu 和 adb 都需要一点时间）")
                last = st
            # 等了一会儿还不行，就主动恢复一次
            if not tried_recover and time.time() - t0 > 5:
                tried_recover = True
                self.recover(log=log)
            time.sleep(1.5)
        if log:
            log(f"!! 等了 {timeout:.0f}s 设备仍未就绪（最后状态={last}）")
        return False

    def recover(self, log=None):
        """重启 adb 服务并重连设备。用于截图连续失败时自愈。"""
        def _run(args):
            try:
                with _ADB_LOCK:
                    return subprocess.run([self.adb] + args, capture_output=True,
                                          timeout=60, creationflags=_NO_WINDOW)
            except Exception as e:
                if log:
                    log(f"  adb {' '.join(args)} 异常：{e}")
                return None

        if log:
            log("  adb 异常自愈：重启 adb 服务并重连设备")
        _run(["kill-server"])
        time.sleep(1.0)
        _run(["start-server"])
        time.sleep(1.0)
        _run(["connect", "127.0.0.1:5555"])       # MuMu 常见的无线调试端口
        time.sleep(0.5)
        _run(["reconnect", "offline"])
        time.sleep(0.5)

    def wait_online_after_fail(self, log=None) -> bool:
        """截图失败后的补救：重启服务 + 等设备回来。"""
        self.recover(log=log)
        return self.wait_ready(timeout=60, log=log)

    def _explain_shot_failure(self, kind: str, last_err) -> str:
        """截图连续失败时，给出人能看懂的诊断信息，并尝试自愈一次。

        最常见的原因不是"截图偶发失败"，而是设备掉线：
        刚重启电脑时 adb 服务没跑、MuMu 还没连上，此时
        `adb devices` 会显示 offline / notfound，screencap 只会返回空包。
        """
        st = self.device_state()
        if st != "device":
            recovered = self.wait_online_after_fail(log=_DIAG_LOG)
            if recovered:
                return (f"screencap({kind}) 失败：设备一开始是 {st}（未就绪），"
                        f"已自动重启 adb 并恢复连接，请重试任务")
            hint = {
                "offline": "模拟器在，但 adb 还没连上",
                "notfound": "没找到这个设备（模拟器没开？或设备号变了）",
                "unauthorized": "设备未授权，看看模拟器里有没有弹授权框",
                "unknown": "adb 命令本身执行不了（路径对不对？）",
            }.get(st, "")
            return (f"screencap({kind}) 失败：设备状态={st}（{hint}）。"
                    f"请确认 MuMu 已启动并加载完，再重试")
        return f"screencap({kind}) 失败: {last_err}（设备在线，属于模拟器偶发问题，可直接重试）"

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
        raise RuntimeError(self._explain_shot_failure("raw", last))

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
                img.load()                     # 必须真正解码，否则坏数据到后面才炸
                break
            except Exception as e:
                last_err = e
                # 空包是模拟器的偶发问题，退避重试；重试次数给足
                time.sleep(0.4 + 0.3 * i)
        else:
            # 重试用完：多半不是"偶发"，而是设备掉线（例如刚重启电脑）。
            # 先看设备状态并试着自愈，再给出**能看懂**的报错。
            raise RuntimeError(self._explain_shot_failure("png", last_err))
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
