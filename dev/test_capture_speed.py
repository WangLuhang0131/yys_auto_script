# -*- coding: utf-8 -*-
"""测试三种截图方式的延迟，为「结束画面快速点击」选最优方案。"""
import time
import numpy as np
from PIL import Image
from adbkit import Adb

a = Adb()

def bench(name, fn, n=5):
    ts = []
    for _ in range(n):
        t = time.time(); fn(); ts.append(time.time() - t)
    print(f"{name:<34} 平均 {sum(ts)/len(ts)*1000:6.0f} ms  最小 {min(ts)*1000:6.0f} ms")
    return sum(ts) / len(ts)

bench("exec-out screencap -p (PNG)", lambda: a.raw("exec-out", "screencap", "-p"))

def raw_all():
    return a.raw("exec-out", "screencap")

bench("exec-out screencap (raw)", raw_all)

def raw_header():
    d = a.raw("exec-out", "screencap")
    idx = d.find(b"\x89PNG")
    # Android 14 的 screencap 默认输出还是 PNG? 检查头
    return d[:16]

print("raw 前 24 字节:", raw_header()[:24])

def raw_parse():
    d = a.raw("exec-out", "screencap")
    # 假设是 w,h,format,(colorspace) + RGBA 数据
    import struct
    try:
        w, h, fmt = struct.unpack("<III", d[:12])
        off = 12
        if fmt == 2:      # 带 colorspace
            off = 16
        if 0 < w < 5000 and 0 < h < 5000 and len(d) - off >= w * h * 4:
            arr = np.frombuffer(d, dtype=np.uint8, count=w * h * 4, offset=off)
            return arr.reshape(h, w, 4)
    except Exception as e:
        return ("err", e)
    return ("unexpected", len(d), d[:16])

r = raw_parse()
print("raw 解析结果:", r if isinstance(r, tuple) else r.shape)
bench("raw + numpy 解析", raw_parse)
