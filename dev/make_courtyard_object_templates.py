# -*- coding: utf-8 -*-
"""给庭院里会移动的物件做模板：探索灯笼、右侧活动图标。

教训：庭院是自由布置的，这些物件位置不固定，写死坐标很容易点到别的东西。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image                                    # noqa: E402
import vision                                            # noqa: E402

SRC = "shots/courtyard_clean.png"
im = Image.open(SRC).convert("RGB")

# 探索灯笼（实测中心约 (1123,350)，灯笼本体约 100x140）
CAND = {
    "t_courtyard_explore.png": (1065, 275, 1190, 425),
    "t_courtyard_activity.png": (1755, 175, 1920, 275),      # 右侧「活动」图标
}
for name, box in CAND.items():
    p = os.path.join("tasks", "jiejie_tupo", "templates", name)
    im.crop(box).save(p)
    print(f"{name}: {Image.open(p).size} 取自 {box}")

# 立即验证：在庭院图上找得到吗？在其它页面上会不会误报？
print("\n=== 探索灯笼模板验证 ===")
for f, label, is_court in [("shots/courtyard_clean.png", "庭院", True),
                           ("shots/step1_explore.png", "探索页", False),
                           ("shots/state_now2.png", "结界突破页", False)]:
    s, x, y = vision.match(Image.open(f).convert("RGB"),
                           os.path.join("tasks", "jiejie_tupo", "templates",
                                        "t_courtyard_explore.png"),
                           region=(900, 200, 1400, 500))
    print(f"  {label:12s} 分数 {s:.3f} 位置 ({x},{y})")

print("\n=== 活动图标模板验证 ===")
for f, label in [("shots/courtyard_clean.png", "庭院")]:
    s, x, y = vision.match(Image.open(f).convert("RGB"),
                           os.path.join("tasks", "jiejie_tupo", "templates",
                                        "t_courtyard_activity.png"),
                           region=(1700, 130, 1920, 320))
    print(f"  {label:12s} 分数 {s:.3f} 位置 ({x},{y})")
