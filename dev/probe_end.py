# -*- coding: utf-8 -*-
"""探测脚本：点挑战 -> 轮询战斗结束画面 -> 保存关键时刻截图。
用途：一次性采集「点击屏幕继续」结束画面的真实截图，用来做识别模板。
"""
import io
import time
import numpy as np
from PIL import Image
from adbkit import Adb

a = Adb()

def fast_grab(region=None):
    """快速截图（不落盘），返回 PIL Image（可裁剪区域）。"""
    data = a.raw("exec-out", "screencap", "-p")
    img = Image.open(io.BytesIO(data)).convert("RGB")
    if img.height > img.width:
        img = img.rotate(-90, expand=True)
    if region:
        img = img.crop(region)
    return img

def red_ratio(img, target=(210, 60, 45), tol=55):
    x = np.asarray(img, dtype=np.float32)
    d = np.abs(x - np.array(target, dtype=np.float32)).max(axis=2)
    return float((d <= tol).mean())

print("== 点挑战 ==")
a.tap(1727, 857)
t0 = time.time()
shots = [(1.0, "p1"), (2.5, "p2"), (4.5, "p3"), (7.0, "p4"), (10.0, "p5")]
done = set()
detected = False
step = 0
while time.time() - t0 < 90:
    el = time.time() - t0
    for ts, name in shots:
        if name not in done and el >= ts:
            done.add(name)
            im = a.screenshot()
            im.save(f"shots/{name}.png")
            print(f"[t={el:5.1f}s] saved {name}.png  顶部红标比例={red_ratio(im.crop((820,0,1100,140))):.3f}  "
                  f"左上亮度={float(np.asarray(im.crop((0,0,120,80)).convert('L')).mean()):.1f}")
    # 快速轮询结束画面：顶部中央红圈
    strip = fast_grab((820, 0, 1100, 150))
    rr = red_ratio(strip)
    if rr > 0.04:
        im = a.screenshot()
        im.save(f"shots/end_{step}.png")
        print(f"[t={el:5.1f}s] 疑似结束画面 rr={rr:.3f} -> shots/end_{step}.png 已保存")
        detected = True
        break
    step += 1
    time.sleep(0.25)

im = a.screenshot()
im.save("shots/after_battle.png")
print("loop end, detected =", detected, "rr_last=%.3f" % rr, "elapsed=%.1f" % (time.time()-t0))
