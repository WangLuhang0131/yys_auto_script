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
# 就用 MuMu 自带的 adb，不折腾别的。
# 只做一件事：目录不在 E 盘时（换台电脑可能装在别的盘）跟着换一下盘符，
# 免得别人 clone 下去第一件事就是改路径。显式指定用环境变量 YYS_ADB。
ADB = r"E:\MuMuPlayer\nx_main\adb.exe"
SERIAL = "emulator-5554"          # MuMu 12 默认
GAME_W, GAME_H = 1920, 1080       # 游戏画面（横屏）逻辑分辨率


def _resolve_adb():
    """返回要用的 adb.exe 路径：MuMu 自带那个。"""
    import os
    env = os.environ.get("YYS_ADB")
    if env and os.path.isfile(env):
        return env
    if os.path.isfile(ADB):
        return ADB
    # 同一条相对路径，换个盘符试试（就这一种情况，不做"到处找 adb"）
    for drive in ("C:", "D:", "E:", "F:", "G:"):
        p = rf"{drive}\MuMuPlayer\nx_main\adb.exe"
        if os.path.isfile(p):
            return p
    return ADB


ADB = _resolve_adb()


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
    def __init__(self, adb_path: str | None = None, serial: str | None = None,
                 rotate: bool = True, coord_mode: str = "identity",
                 shot_mode: str = "color"):
        # 默认就用 MuMu 自带那个 adb（模块顶部已经解析好）
        self.adb = adb_path or ADB
        self.serial = serial or SERIAL
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
        """返回设备状态：device / offline / unauthorized / notfound / unknown。

        刚开机时 adb 服务没跑、或设备还在连，这里会是 offline / notfound，
        而 screencap 只会返回空包——所以报错前必须先看这个状态。

        ⚠ 实测坑：`adb devices` 和 `adb get-state` 有时给出的状态**不一致**。
        刚重启 daemon / 设备正在重新握手时，devices 显示 offline，
        但 get-state 已经能返回 device（这时截图其实是通的）。
        所以两边都要看，只要有一个说 device 就认为就绪。
        """
        listed = "unknown"
        try:
            with _ADB_LOCK:
                p = subprocess.run([self.adb, "devices"], capture_output=True,
                                   timeout=20, creationflags=_NO_WINDOW)
            text = p.stdout.decode("utf-8", "replace")
            listed = "notfound"
            for line in text.splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 2 and parts[0] == self.serial:
                    listed = parts[1]
                    break
        except Exception:
            listed = "unknown"
        if listed == "device":
            return "device"
        # devices 说不是 device，再用 get-state 复核一次（更接近"能不能真的通信"）
        try:
            with _ADB_LOCK:
                p = subprocess.run([self.adb, "-s", self.serial, "get-state"],
                                   capture_output=True, timeout=20,
                                   creationflags=_NO_WINDOW)
            got = p.stdout.decode("utf-8", "replace").strip()
            if got == "device":
                return "device"
        except Exception:
            pass
        return listed

    def devices_text(self) -> str:
        """原始 `adb devices` 输出（排查问题时用，别只看解析结果）。"""
        try:
            with _ADB_LOCK:
                p = subprocess.run([self.adb, "devices"], capture_output=True,
                                   timeout=20, creationflags=_NO_WINDOW)
            return p.stdout.decode("utf-8", "replace").strip()
        except Exception as e:
            return f"<adb devices 执行失败: {e}>"

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
                    log(f"等待设备就绪... 当前状态={st}")
                    if st == "notfound":
                        # 这种情况多半是"另一个 adb 在抢 5037 端口"：
                        # MuMu 自带的 adb 会把别人的 daemon 杀掉自己起一个，
                        # 两个 adb 版本互相打架时，设备列表会一会儿有一会儿没有。
                        log("    设备列表里没有这台设备。常见原因：")
                        log("      · MuMu 自带的 adb 和脚本用的 adb 版本不一致，"
                            "两边抢 5037 端口")
                        log("      · 模拟器刚启动，还没把 usb 调试端口接上")
                        log(f"    当前 adb devices 原始输出：{self.devices_text()!r}")
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
                "offline": "模拟器在，但 adb 还没握手完",
                "notfound": "adb 设备列表里没有这台设备",
                "unauthorized": "设备未授权，看看模拟器里有没有弹授权框",
                "unknown": "adb 命令本身执行不了（路径对不对？）",
            }.get(st, "")
            return (f"screencap({kind}) 失败：设备状态={st}（{hint}）。"
                    f"adb devices 原始输出：{self.devices_text()!r}。"
                    f"如果模拟器确实开着，通常是 MuMu 自带的 adb 和本脚本用的 adb "
                    f"版本不一致、互相抢 5037 端口；把 adbkit.py 里的 ADB 或者"
                    f"环境变量 YYS_ADB 指向 MuMu 目录下那个 adb.exe 即可")
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
