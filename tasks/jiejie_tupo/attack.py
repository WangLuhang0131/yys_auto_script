# -*- coding: utf-8 -*-
"""结界突破的页面操作与判据（坐标和阈值全部来自实机实测）。

实测结论（很重要，别再踩坑）：
1. 只有**亮的格子**能打；灰色带「破」的是已攻破，点了没反应。
2. 可点的位置是格子的**名字/进度圈那一片**（头像右侧），
   点头像本身、点灰格都没反应 —— 实测点在 (cx+120, cy+30) 一次成功。
3. 面板会**跟着被点的格子换位置**：点右下角的格子，面板就出现在右下，
   所以「进攻」按钮必须实时找，不能写死坐标。
4. 点「进攻」→ 自动战斗（约 10 秒）→ 胜利画面「点击屏幕继续」。
5. 点掉「点击屏幕继续」后回到结界突破页，被打的格子由亮变灰。
6. 顶部系统横幅（聊天/公告）会给**整屏加一层变暗遮罩**，
   变暗后所有绝对亮度判据都会失准（整屏均值可从 114 掉到 56），
   所以凡是用亮度的判据一律改成「相对整屏均值」的比值。
"""
from __future__ import annotations

import numpy as np

import vision

from . import ui

# 可打判据：采样区（格心+95, ±55×±18）的亮度 / 整屏均值 > 该值。
# 实测（真实画面）：已攻破 0.64~1.14，可打 1.30~1.88 —— 取 1.22 分界，两边余量都够。
# 注意采样必须避开深色头像，否则灰格会被算成亮的（踩过这个坑）。
CELL_RATIO_TH = 1.22


# ---------------- 亮度采样 ----------------
def page_mean(img):
    """整屏灰度均值（用来做相对判据，抵消横幅遮罩造成的整体变暗）。"""
    return float(np.asarray(img.convert("L"), dtype=np.float32).mean())


def cell_lum(img, cx, cy):
    """格子采样区的灰度均值（采样点已避开深色头像）。"""
    dx = ui.CELL_SAMPLE_DX
    hw, hh = ui.CELL_SAMPLE_HALF
    a = np.asarray(img.crop((cx + dx - hw, cy - hh, cx + dx + hw, cy + hh)).convert("L"),
                   dtype=np.float32)
    return float(a.mean())


def cell_ratio(img, cx, cy, mean=None):
    """格子相对整屏的亮度比值 —— 抗横幅变暗。"""
    m = mean if mean is not None else page_mean(img)
    return cell_lum(img, cx, cy) / max(m, 1.0)


def scan_cells(img):
    """返回 [(cx, cy, 绝对亮度, 比值, 是否可打)]，按行优先顺序。"""
    m = page_mean(img)
    out = []
    for cy in ui.GRID_Y:
        for cx in ui.GRID_X:
            lum = cell_lum(img, cx, cy)
            ratio = lum / max(m, 1.0)
            out.append((cx, cy, round(lum, 1), round(ratio, 3),
                        ratio > CELL_RATIO_TH))
    return out


# ---------------- 「进攻」面板 ----------------
def find_attack_btn(img):
    """全屏找「进攻」按钮。
    紧裁剪的「进攻」文字模板，实测真面板 ≈0.96~1.0，
    结界突破页的「刷新」按钮只有 0.45，分界干净。
    返回 (是否找到, 匹配分, 按钮中心 x, y)"""
    s, x, y = vision.match(img, ui.tpl("t_attack_btn.png"), region=ui.R_ATTACK_SEARCH)
    return s >= 0.75, round(float(s), 3), int(x), int(y)


def panel_open(img):
    """兼容旧接口：返回 (是否打开, 匹配分, 面板亮度)。"""
    ok, s, x, y = find_attack_btn(img)
    cover = float(np.asarray(img.crop(ui.R_PANEL).convert("L"),
                             dtype=np.float32).mean())
    return ok, s, round(cover, 1)


def find_ready_btn(img):
    """队伍确认画面的「准备」按钮（点完进攻后会先到这个画面）。
    实测：准备画面 1.000，结界突破页 0.18，胜利画面 0.28。
    返回 (是否找到, 匹配分, x, y)"""
    s, x, y = vision.match(img, ui.tpl("t_ready.png"), region=ui.R_READY)
    return s >= 0.60, round(float(s), 3), int(x), int(y)


# ---------------- 阵容锁定 ----------------
# 实机标定（对同一个 25x25 小区域 (1263,883)-(1288,908)，用两状态差异图自动定位）：
#   未锁定（深色边框）：均值 46.4，很暗(<90)占比 0.925
#   已锁定（亮色边框）：均值 116.1，很暗(<90)占比 0.333
# 差异极大，用「很暗像素占比」就足够，阈值取 0.60（两边各有 0.25 以上余量）。
# 切换方式：点「阵容」左侧的金框图标本身。
LOCK_DARK_LOCKED = 0.60           # 很暗像素占比 ≤ 该值 = 已锁定


def lock_metrics(img):
    """阵容锁定图标的指标。"""
    a = np.asarray(img.crop(ui.R_LINEUP_LOCK).convert("RGB"), dtype=np.float32)
    g = a.mean(axis=2)
    return {
        "mean": round(float(g.mean()), 1),
        "dark": round(float((g < 90).mean()), 3),
    }


def lock_state(img):
    """判断阵容锁定状态。返回 ('locked' / 'unlocked' / 'unknown', 指标)"""
    m = lock_metrics(img)
    if m["dark"] <= 0.45:
        return "locked", m
    if m["dark"] >= 0.75:
        return "unlocked", m
    return "unknown", m


def is_locked(img):
    """兼容旧接口：返回 (是否已锁定, 指标)。unknown 视为已锁定（不做动作）。"""
    st, m = lock_state(img)
    return st != "unlocked", m


# ---------------- 突破券计数（右上「7/30」） ----------------
# 实测数字区：x 1640~1810, y 20~80。字形从左到右是
#   突破图标 | 左数(1~2位) | / | 上限(2位)
# 实测（7/30）：左数「7」宽 15px，上限「3」「0」各宽 13/16px，斜杠宽 6px。
# 因此可以用「左数那一位的宽度」区分数字：0/8/9 这类圆数字明显更宽，
# 7/1 这类窄数字明显更窄。只用于判断「券是不是用完了」，不追求读准确值。
TICKET_BOX = (1630, 20, 1810, 80)
TICKET_BRIGHT = 150
TICKET_NARROW_MAX_W = 9        # 宽度 ≤ 该值视为斜杠（实测斜杠 6px，数字 13~16px）
TICKET_TALL_H = 20             # 高度 ≥ 该值才算数字/斜杠（排除图标）
TICKET_WIDE_W = 17             # 左数那一位宽 ≥ 该值 = 宽数字（0/8/9）→ 券数可能为 0
TICKET_MAX_GAP = 12            # 斜杠与它左边那一位的最大字距（实测 4~6px）
TICKET_SLASH_H = (20, 34)      # 斜杠高度范围（实测 25）


def _glyph_segments(img):
    """把计数区里的亮字形切成一段段，返回 [(x1, x2, 宽, 高, 亮像素数), ...] 从左到右。"""
    a = np.asarray(img.crop(TICKET_BOX).convert("L"), dtype=np.float32)
    mask = a > TICKET_BRIGHT
    cols = mask.sum(axis=0)
    segs, start = [], None
    for i, v in enumerate(cols):
        if v > 0 and start is None:
            start = i
        elif v == 0 and start is not None:
            segs.append((TICKET_BOX[0] + start, TICKET_BOX[0] + i - 1))
            start = None
    if start is not None:
        segs.append((TICKET_BOX[0] + start, TICKET_BOX[0] + len(cols) - 1))

    out = []
    for x1, x2 in segs:
        m = mask[:, x1 - TICKET_BOX[0]:x2 - TICKET_BOX[0] + 1]
        rr = np.nonzero(m.sum(axis=1) > 0)[0]
        h = int(rr.max() - rr.min() + 1) if len(rr) else 0
        out.append((x1, x2, x2 - x1 + 1, h, int(m.sum())))
    return out


def ticket_info(img):
    """返回突破券计数信息（尽力而为，只判断"券是不是用完了"）。

    实测数字区结构：突破图标 | 左数 | / | 上限(2位)
    做法（不识别汉字，只用几何）：
      1. 只保留"高 ≥20px"的字形段（数字和斜杠），丢掉左侧大图标；
      2. 其中最窄的一段就是斜杠；
      3. 斜杠左边那一位 = 左数（券数）的最后一位；
         它的宽度 ≥17px 说明是 0/8/9 这类宽数字 → 券数很可能是 0（用完）。
    """
    segs = _glyph_segments(img)
    tall = [s for s in segs if s[3] >= TICKET_TALL_H]
    info = {"glyphs": segs, "tall": tall, "slash_w": None,
            "left_w": None, "left_x": None, "almost_out": None}
    if len(tall) < 3:
        return info

    # 候选斜杠：窄且高度在斜杠范围内（实测 6px 宽 / 25px 高）
    cands = [s for s in tall
             if s[2] <= TICKET_NARROW_MAX_W and TICKET_SLASH_H[0] <= s[3] <= TICKET_SLASH_H[1]]
    if not cands:
        return info
    slash = max(cands, key=lambda s: s[0])          # 取最右边那个
    info["slash_w"] = slash[2]

    # 紧挨在斜杠左边、字距正常的那一位 = 券数最后一位
    lefts = [s for s in tall if s[1] < slash[0] and (slash[0] - s[1]) <= TICKET_MAX_GAP]
    if not lefts:
        return info
    left = max(lefts, key=lambda s: s[0])
    info["left_x"] = (left[0], left[1])
    info["left_w"] = left[2]
    info["almost_out"] = left[2] >= TICKET_WIDE_W
    return info


# ---------------- 券不足时的收工判据 ----------------
# 实测教训：**不要用「中部暗像素变多」这种糙判据**。
# 我一度用它判定券不足，结果存下来的现场图其实是个「玩家资料弹窗」
# （点格子时误触到玩家头像），属于误判。
# 现在只用两条**行为/几何**判据：
#   1) 点进攻后 20 秒内既没出现「准备」（进战斗）也没到结算 -> 券不足；
#   2) 连续 MAX_EMPTY_ROUNDS 轮 9 个格子全部已攻破 -> 券不足。
# 若将来拿到「结界挑战券不足」提示的清晰截图，可以在这里补一个模板匹配，
# 作为更直接的判据（比暗像素稳得多）。
WARN_DARK_TH = 60
WARN_MIN_PIXELS = 30000
# 资料页识别：实测资料页时中央提示带暗像素 15959，正常页面 1000~6000。
# 所以 10000 可以干净区分（只用于「是否要关掉资料页」，不用来判定券不足）。
PROFILE_MIN_PIXELS = 10000
# 只认"画面正中那一条带"里的提示，避免资料弹窗之类的误触发
WARN_STRIP = (620, 430, 1300, 500)


def warning_pixels(img):
    """统计画面正中提示条带里"很暗的笔画像素"数量。
    ⚠ 这只是个粗判据（弹窗也可能命中），只用来在日志里给点线索，
    不作为「券不足」的判定依据。"""
    a = np.asarray(img.crop(WARN_STRIP).convert("L"), dtype=np.float32)
    return int((a < WARN_DARK_TH).sum())


def warning_visible(img, min_pixels=WARN_MIN_PIXELS):
    n = warning_pixels(img)
    return n >= min_pixels, n
