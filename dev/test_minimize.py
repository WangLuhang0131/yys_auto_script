# -*- coding: utf-8 -*-
"""实测：MuMu 窗口「最小化」后，渲染是否停止（截图是否变黑/冻结）。

步骤：
  1) 抓当前帧 baseline
  2) 最小化 MuMu 窗口（ShowWindow SW_MINIMIZE）
  3) 等 N 秒后抓帧 minimized
  4) 还原窗口（SW_RESTORE），等 2 秒再抓帧 restored
  5) 对比像素差 / 平均亮度
"""
import ctypes
import io
import sys
import time

import numpy as np
from PIL import Image

from adbkit import Adb

user32 = ctypes.windll.user32

SW_MINIMIZE = 6
SW_RESTORE = 9

TITLES = ["MuMu", "阴阳师", "MuMuPlayer", "MuMu模拟器"]


def find_windows():
    """枚举可见顶层窗口，返回 [(hwnd, title)]，按标题过滤。"""
    found = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def cb(hwnd, lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        n = user32.GetWindowTextLengthW(hwnd)
        if n == 0:
            return True
        buf = ctypes.create_unicode_buffer(n + 1)
        user32.GetWindowTextW(hwnd, buf, n + 1)
        title = buf.value
        # 取进程名
        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        found.append((hwnd, title, pid.value))
        return True

    user32.EnumWindows(cb, None)
    return found


def proc_name(pid):
    try:
        import subprocess
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                             capture_output=True, text=True, timeout=10).stdout.strip()
        return out.split(",")[0].strip('"') if out else "?"
    except Exception:
        return "?"


def main():
    wins = find_windows()
    print("=== 可见顶层窗口（含 MuMu 关键字）===")
    target = None
    for hwnd, title, pid in wins:
        name = proc_name(pid)
        if any(k.lower() in title.lower() for k in TITLES) or "mumu" in name.lower():
            print(f"  hwnd={hwnd} pid={pid} proc={name} title={title!r}")
            if target is None:
                target = (hwnd, title, name)

    if target is None:
        print("\n未找到 MuMu 窗口，打印全部窗口供参考：")
        for hwnd, title, pid in wins[:25]:
            print(f"  hwnd={hwnd} pid={pid} proc={proc_name(pid)} title={title!r}")
        return 1

    hwnd, title, name = target
    print(f"\n>>> 操作窗口: {name} / {title!r} (hwnd={hwnd})")

    a = Adb()

    def grab(tag):
        im = a.screenshot()
        arr = np.asarray(im, dtype=np.float32)
        p = f"shots/min_{tag}.png"
        im.save(p)
        print(f"  {tag:10s} 亮度均值={arr.mean():7.2f}  黑像素占比={(arr < 12).mean():.3f}  -> {p}")
        return arr

    print("\n[1] 抓基线（窗口正常显示）")
    base = grab("baseline")

    time.sleep(1.5)
    print("\n[1b] 再抓一张（确认画面在动）")
    base2 = grab("baseline2")
    d = np.abs(base - base2)
    print(f"  两次差异: 平均={d.mean():.2f} 最大={d.max():.0f}"
          f"  （画面在动的话平均差通常 >1）")

    print("\n[2] 最小化窗口")
    user32.ShowWindow(hwnd, SW_MINIMIZE)
    time.sleep(3.0)
    mini1 = grab("minimized_3s")

    time.sleep(5.0)
    print("\n[3] 最小化保持 8 秒后再抓")
    mini2 = grab("minimized_8s")
    dm = np.abs(mini1 - mini2)
    print(f"  最小化期间两次差异: 平均={dm.mean():.2f} 最大={dm.max():.0f}")

    print("\n[4] 还原窗口")
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetForegroundWindow(hwnd)
    time.sleep(2.5)
    rest = grab("restored")
    dr = np.abs(mini2 - rest)
    print(f"  最小化 -> 还原 差异: 平均={dr.mean():.2f} 最大={dr.max():.0f}")

    print("\n=== 结论参考 ===")
    print(f"  基线两帧差 {d.mean():.2f}；最小化期间两帧差 {dm.mean():.2f}；还原前后差 {dr.mean():.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
