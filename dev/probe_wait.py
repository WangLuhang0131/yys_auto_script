# -*- coding: utf-8 -*-
"""轮询等待战斗结束画面（点击屏幕继续），保存若干候选帧。"""
import io, time
import numpy as np
from PIL import Image
from adbkit import Adb

a = Adb()

def grab(region=None):
    for attempt in range(5):
        data = a.raw("exec-out", "screencap", "-p")
        try:
            img = Image.open(io.BytesIO(data)).convert("RGB")
            break
        except Exception:
            print(f"  (screencap 空包，重试 {attempt+1}, bytes={len(data)})", flush=True)
            time.sleep(1.0)
    else:
        raise RuntimeError("screencap 连续失败")
    if img.height > img.width:
        img = img.rotate(-90, expand=True)
    return img.crop(region) if region else img

def stat(img):
    g = np.asarray(img.convert("L"), dtype=np.float32)
    x = np.asarray(img, dtype=np.float32)
    top = g[0:60, :]
    mid = g[300:760, :]
    return dict(dark=float((g < 60).mean()), top_red=float(((x[0:60, :, 0] > 120) & (x[0:60, :, 1] < 90)).mean()),
                mid_lum=float(mid.mean()), mean=float(g.mean()))

t0 = time.time()
cands = 0
last = None
while time.time() - t0 < 200:
    im = grab()
    s = stat(im)
    el = time.time() - t0
    sig = (round(s["mean"] / 4), round(s["mid_lum"] / 4), round(s["dark"] * 4))
    if sig != last:
        print(f"[t={el:6.1f}] mean={s['mean']:6.1f} mid={s['mid_lum']:6.1f} dark={s['dark']:.3f} top_red={s['top_red']:.3f}",
              flush=True)
        last = sig
    # 战斗场景特征：顶部血条红、暗像素极少；结束画面应是暗底+金色字
    if s["top_red"] < 0.15 and s["dark"] > 0.08:
        cands += 1
        im.save(f"shots/cand_{cands}.png")
        print(f"[t={el:6.1f}] 候选结束帧 -> shots/cand_{cands}.png  "
              f"mean={s['mean']:.1f} dark={s['dark']:.3f} top_red={s['top_red']:.3f}", flush=True)
        if cands >= 3:
            break
    time.sleep(0.2)

print("done, elapsed=%.1f" % (time.time() - t0))
