# -*- coding: utf-8 -*-
"""从已采集的整屏截图里裁剪模板，并打印各状态判据的像素特征。"""
import os
from PIL import Image, ImageStat

os.makedirs("templates", exist_ok=True)

def crop(src, box, name):
    im = Image.open(os.path.join("shots", src)).convert("RGB")
    t = im.crop(box)
    t.save(os.path.join("templates", name))
    print(f"template {name:26s} {box} -> {t.size}")

def region_stat(src, box, label):
    im = Image.open(os.path.join("shots", src)).convert("RGB")
    st = ImageStat.Stat(im.crop(box))
    return label, [round(v, 1) for v in st.mean], round(sum(st.mean) / 3, 1)

# ---- 模板 ----
crop("prep_c.png", (230, 25, 450, 90), "t_overview.png")       # 活动总览 标题
crop("prep_c.png", (1550, 880, 1900, 980), "t_go_activity.png")  # 前往活动 按钮
crop("prep_b.png", (230, 20, 460, 85), "t_detail.png")          # 拾此一瞬 标题
crop("prep_b.png", (280, 360, 480, 470), "t_guji.png")          # 古迹演武 入口
crop("prep_a.png", (1655, 810, 1800, 905), "t_challenge.png")   # 挑战 按钮

print("\n=== 前往活动按钮区（活动总览 / 活动详情）色彩对比 ===")
for src in ("prep_c.png", "prep_b.png"):
    for box, lab in [((1650, 895, 1780, 955), "按钮内部"), ((1740, 920, 1880, 960), "按钮内部2")]:
        print(src, *region_stat(src, box, lab))

print("\n=== 活动总览页 左侧红点/标题 判据 ===")
print("prep_c 标题区", *region_stat("prep_c.png", (230, 25, 450, 90), "title"))
print("prep_b 同位置", *region_stat("prep_b.png", (230, 25, 450, 90), "title"))

print("\n=== 备战页 剩余次数数字区（白色数字 299）===")
print("prep_a", *region_stat("prep_a.png", (1190, 25, 1300, 70), "count"))
print("prep_b", *region_stat("prep_b.png", (1190, 25, 1300, 70), "count"))

print("\n=== 备战页 挑战按钮 ===")
print("prep_a", *region_stat("prep_a.png", (1655, 810, 1800, 905), "challenge"))
