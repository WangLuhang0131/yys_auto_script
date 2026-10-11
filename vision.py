# -*- coding: utf-8 -*-
"""识别核心：不依赖 opencv，用 numpy FFT 做归一化互相关(NCC)模板匹配。
支持掩膜（只匹配模板中真正有内容的像素），适合文字/按钮模板。
"""
from __future__ import annotations

import os
import numpy as np
from PIL import Image

# 模板目录：打包成 exe 后要用解包目录（见 core/paths.py）
try:
    from core.paths import res_path
    TPLDIR = res_path("templates")
except Exception:
    TPLDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


def _ncc(image: np.ndarray, tpl: np.ndarray, mask: np.ndarray | None = None):
    """返回 (score_map, valid_map)。image/tpl 为 float32 单通道或已展平。
    这里对多通道分别算再平均，简化处理。
    """
    H, W = image.shape
    h, w = tpl.shape
    if h > H or w > W:
        return None, None

    if mask is None:
        mask = np.ones_like(tpl)
    m = mask.astype(np.float32)
    n = float(m.sum())
    if n < 1:
        return None, None

    # 归一化模板（去均值，掩膜加权）
    t = tpl.astype(np.float32)
    t_mean = float((t * m).sum() / n)
    t = (t - t_mean) * m
    t_norm = np.sqrt(float((t * t).sum()))
    if t_norm < 1e-6:
        return None, None
    t = t / t_norm

    # 用 FFT 做相关
    fsize = (H + h - 1, W + w - 1)
    FI = np.fft.rfft2(image.astype(np.float32), fsize)
    FT = np.fft.rfft2(t[::-1, ::-1], fsize)
    corr = np.fft.irfft2(FI * FT, fsize)[h - 1:H, w - 1:W]

    # 掩膜下的局部平方和 & 局部均值
    ones = np.ones_like(image, dtype=np.float32)
    Fo = np.fft.rfft2(ones, fsize)
    Fm = np.fft.rfft2(m[::-1, ::-1], fsize)
    local_n = np.fft.irfft2(Fo * Fm, fsize)[h - 1:H, w - 1:W]
    local_n = np.maximum(local_n, 1e-6)

    FI2 = np.fft.rfft2(image.astype(np.float32) ** 2, fsize)
    local_s2 = np.fft.irfft2(FI2 * Fm, fsize)[h - 1:H, w - 1:W]

    FIm = np.fft.rfft2(image.astype(np.float32), fsize)
    Fmm = np.fft.rfft2(m[::-1, ::-1], fsize)
    local_s1 = np.fft.irfft2(FIm * Fmm, fsize)[h - 1:H, w - 1:W]

    var = local_s2 - (local_s1 ** 2) / local_n
    # 掩膜很稀疏时 var 可能接近 0，NCC 会爆成大数；这里做保护
    var = np.maximum(var, 1e-3 * np.maximum(local_s2, 1.0))

    score = corr / np.sqrt(var)
    score = np.clip(score, -1.0, 1.0)          # NCC 理论范围就是 [-1, 1]
    valid = local_n > 0.5 * n
    return score, valid


def _tpl_path(name: str) -> str:
    """模板名可以是文件名（在 templates/ 找），也可以是绝对路径（任务自带模板）。"""
    if os.path.isabs(name) or os.sep in name or "/" in name:
        return name
    return os.path.join(TPLDIR, name)


def match(img: Image.Image, tpl_path: str, region=None, mask_path=None, channels="gray"):
    """
    在 img 中查找 tpl。返回 (score, cx, cy) —— 全图坐标。
    region: (x1,y1,x2,y2) 限定搜索区域，加速并提高准确率。
    tpl_path / mask_path: 文件名（找 templates/）或绝对路径（任务自带）。
    """
    if region:
        x1, y1, x2, y2 = region
        sub = img.crop((x1, y1, x2, y2))
    else:
        x1 = y1 = 0
        sub = img

    tpl = Image.open(_tpl_path(tpl_path)).convert("RGB")
    if (tpl.height > sub.height or tpl.width > sub.width):
        raise ValueError(
            f"模板比搜索区还大：模板 {tpl.size} 区域 {sub.size}（region={region}）"
            f" —— 把 region 放大或把模板裁小")
    if mask_path:
        mk = Image.open(_tpl_path(mask_path)).convert("L")
        mask_arr = (np.asarray(mk, dtype=np.float32) > 127).astype(np.float32)
    else:
        mask_arr = None

    def to_ch(img_):
        a = np.asarray(img_).astype(np.float32)
        if a.ndim == 2:                     # 灰度图（L 模式，raw 截图走这条路）
            return [a]
        if channels == "gray":
            return [a @ np.array([0.299, 0.587, 0.114], dtype=np.float32)]
        return [a[:, :, i] for i in range(a.shape[2])]

    ch_img = to_ch(sub)
    ch_tpl = to_ch(tpl)

    best = (-2.0, 0, 0)
    for ci, ct in zip(ch_img, ch_tpl):
        score, valid = _ncc(ci, ct, mask_arr)
        if score is None:
            return -1.0, 0, 0
        score = np.where(valid, score, -1.0)
        idx = int(np.argmax(score))
        s = float(score.ravel()[idx])
        if s > best[0]:
            yy, xx = np.unravel_index(idx, score.shape)
            best = (s, x1 + xx + ct.shape[1] // 2, y1 + yy + ct.shape[0] // 2)
    return best[0], best[1], best[2]


def brightness(img: Image.Image, box) -> float:
    a = np.asarray(img.crop(box).convert("L"), dtype=np.float32)
    return float(a.mean())


def mean_rgb(img: Image.Image, box):
    a = np.asarray(img.crop(box).convert("RGB"), dtype=np.float32)
    return tuple(round(float(v), 1) for v in a.reshape(-1, 3).mean(axis=0))


def color_ratio(img: Image.Image, box, target, tol=40) -> float:
    """区域内接近目标颜色的像素占比（灰度图自动退化为灰度比较）。"""
    a = np.asarray(img.crop(box).convert("RGB"), dtype=np.float32)
    d = np.abs(a - np.array(target, dtype=np.float32)).max(axis=2)
    return float((d <= tol).mean())
