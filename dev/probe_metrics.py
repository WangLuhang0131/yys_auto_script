# -*- coding: utf-8 -*-
"""结束画面判据测量：打一场，战斗中和结束后分别采样指标。"""
import io, time
import numpy as np
from PIL import Image
from adbkit import Adb

a = Adb()

def grab(region=None, retries=5):
    for i in range(retries):
        data = a.raw("exec-out", "screencap", "-p")
        try:
            img = Image.open(io.BytesIO(data)).convert("RGB")
            break
        except Exception:
            time.sleep(1.0)
    else:
        raise RuntimeError("screencap fail")
    if img.height > img.width:
        img = img.rotate(-90, expand=True)
    return img

def metrics(img, tag):
    x = np.asarray(img, dtype=np.float32)
    g = np.asarray(img.convert("L"), dtype=np.float32)
    # 底部中央「点击屏幕继续」金色文字区
    box = x[1000:1065, 780:1140]
    gold = ((box[:, :, 0] > 170) & (box[:, :, 1] > 140) & (box[:, :, 2] < 170) & (box[:, :, 0] - box[:, :, 2] > 40))
    gold_cnt = int(gold.sum())
    # 战斗 UI 特征
    top_red = float(((x[0:55, :, 0] > 130) & (x[0:55, :, 1] < 95)).mean())
    auto_btn = float(g[900:1010, 20:120].mean())   # 左下「自动」按钮区
    back_btn = float(g[20:70, 30:120].mean())      # 左上返回箭头
    print(f"{tag:16s} gold_px={gold_cnt:6d} top_red={top_red:.3f} auto_lum={auto_btn:6.1f} "
          f"back_lum={back_btn:6.1f} mean={g.mean():6.1f} dark={float((g<60).mean()):.3f}", flush=True)
    return gold_cnt, top_red

print("== 第二场：点挑战 ==")
a.tap(1727, 857)
t0 = time.time()
# 战斗中期采样
time.sleep(12)
metrics(grab(), "battle12s")
time.sleep(20)
im = grab(); metrics(im, "battle32s")

# 轮询结束画面
while time.time() - t0 < 180:
    im = grab()
    gold, top_red = metrics(im, "poll")
    if gold > 120 and top_red < 0.10:
        im.save("shots/end_probe.png")
        print(">>> 判定为结束画面，已保存 shots/end_probe.png", flush=True)
        break
    time.sleep(0.4)
else:
    print("超时未检测到结束画面")

# 结束画面停留：点一下看是否快速结束（验证结束画面会自动消失）
time.sleep(2.0)
metrics(grab(), "end+2s")
