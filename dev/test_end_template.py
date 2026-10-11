# -*- coding: utf-8 -*-
"""用「点击屏幕继续」模板对所有已保存画面打分，检查误报/漏报。"""
import os, glob
import vision

REGION = (700, 960, 1230, 1080)

groups = {
    "结束画面(正样本)": ["shots/dbg/001_t0_before.png", "shots/end_2.png",
                    "shots/cand_1.png", "shots/end_probe.png"],
    "备战页(负样本)": ["shots/now_state.png", "shots/prep_a.png", "shots/prep_b.png",
                   "shots/dbg/032_t045.5.png"],
    "战斗场景(负样本)": ["shots/after_battle.png", "shots/p1.png"],
    "活动页(负样本)": ["shots/prep_c.png"],
}

for gname, files in groups.items():
    print(f"--- {gname} ---")
    for f in files:
        if not os.path.exists(f):
            print(f"  {f:<34} (不存在)")
            continue
        from PIL import Image
        im = Image.open(f).convert("RGB")
        s, x, y = vision.match(im, "end_text.png", region=REGION, mask_path="end_text_mask.png")
        print(f"  {os.path.basename(f):<34} score={s:+.3f}  位置=({x},{y})")
