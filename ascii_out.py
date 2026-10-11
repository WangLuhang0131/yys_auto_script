# -*- coding: utf-8 -*-
"""控制台 ASCII 化：让 cmd（代码页 936 或 65001）都能显示正常，不出现乱码。

日志文件仍然写 UTF-8 中文（记事本 / VS Code 打开正常），
只有打印到控制台时把中文换成等义英文。
"""
from __future__ import annotations

import re
import sys

# ---------- 第一层：整行模板（正则），最具体 ----------
LINE_PATTERNS = [
    # 主循环标题：--- 第 3/300 次 ---
    (re.compile(r"^--- 第 (\d+)/(\d+) 次 ---$"), r"--- run \1/\2 ---"),
    # 结束汇总
    (re.compile(r"^结束：成功 (\d+) 次，失败 (\d+) 次，总耗时 ([\d.]+) 分钟，平均 ([\d.]+) 秒/次$"),
     r"DONE: ok \1, failed \2, total \3 min, avg \4 s/run"),
    (re.compile(r"^日志文件：(.+)$"), r"log file: \1"),
    (re.compile(r"^阴阳师 (.+) 自动刷取启动  目标次数=(\d+)$"), r"Onmyoji \1 auto grind started  runs=\2"),
    (re.compile(r"^设备=(.+)  adb=(.+)$"), r"device=\1  adb=\2"),
    (re.compile(r"^随机落点=开启（拟人化）(.*)$"), r"random taps=ON (humanized)\1"),
    (re.compile(r"^随机落点=关闭（固定坐标）(.*)$"), r"random taps=OFF (fixed)\1"),
    (re.compile(r"^当前画面状态: (.*)$"), r"screen state: \1"),
    (re.compile(r"^检测到正在战斗中，等待本场结束后接管\.\.\.$"),
     r"battle in progress, taking over after it ends..."),
    (re.compile(r"^战场结束，状态=(.*)$"), r"battle ended, state=\1"),
    (re.compile(r"^导航第(\d+)步: 当前状态=(.*)$"), r"nav step \1: state=\2"),
    (re.compile(r"^已在古迹演武备战页$"), r"at Guji Yanwu prep page"),
    (re.compile(r"^已点挑战$"), r"challenge tapped"),
    (re.compile(r"^已进入战斗: (\S+) (.*)  \(([\d.]+)s\)$"), r"entered battle: \1 \2  (\3s)"),
    (re.compile(r"^未进入战斗，补点一次挑战$"), r"not in battle, retapping challenge"),
    (re.compile(r"^检测到结束画面（分数 ([\d.]+)，战斗耗时 ([\d.]+)s），立刻点击继续$"),
     r"end screen detected (score \1, battle took \2s), clicking continue now"),
    (re.compile(r"^第 (\d+) 次点击后仍在 (\S+) (.*)，再点一次$"),
     r"\1th click, still \2 \3, one more tap"),
    (re.compile(r"^未检测到结束画面，但已回到备战页（视为完成）$"),
     r"end screen missed but back at prep (counted as done)"),
    (re.compile(r"^本轮完成，用时 ([\d.]+)s$"), r"round done, took \1s"),
    (re.compile(r"^本轮失败，用时 ([\d.]+)s$"), r"round FAILED, took \1s"),
    (re.compile(r"^随机长停顿 ([\d.]+)s$"), r"random long pause \1s"),
    (re.compile(r"^成功  用时 ([\d.]+)s  累计成功 (\d+) 失败 (\d+)$"),
     r"OK   took \1s  ok=\2 fail=\3"),
    (re.compile(r"^!! 失败 (.*)$"), r"!! FAILED \1"),
    (re.compile(r"^尝试恢复到备战页\.\.\.$"), r"trying to recover to prep..."),
    (re.compile(r"^!! 恢复失败，停止脚本$"), r"!! recovery failed, stopping"),
    (re.compile(r"^!! 挑战键不可点（亮像素占比 ([\d.]+)，可点时应 ≥0\.12），可能次数已耗尽，停止脚本$"),
     r"!! challenge button not clickable (bright ratio \1, expected >=0.12), attempts used up, stopping"),
    (re.compile(r"^!! 无法进入备战页，请确认游戏停在「活动总览/活动详情/古迹演武」任一页面$"),
     r"!! cannot reach prep page; park the game on the event screen"),
    (re.compile(r"^--stats 模式，直接退出$"), r"--stats mode, exiting"),
    (re.compile(r"^用户取消$"), r"cancelled by user"),
    (re.compile(r"^!! 25 秒内未能进入战斗$"), r"!! could not enter battle within 25s"),
    (re.compile(r"^!! 战斗超时$"), r"!! battle timeout"),
    (re.compile(r"^未回到备战页（(\S+) (.*)），再补点一次$"), r"not back at prep (\1 \2), one more tap"),
    (re.compile(r"^仍在战斗中，等待\.\.\.$"), r"still in battle, waiting..."),
    (re.compile(r"^未知状态，点屏幕中央重试 (.*)$"), r"unknown state, tap center to retry \1"),
    (re.compile(r"^检测到结束画面 \((.*)\)$"), r"end screen detected (\1)"),
    (re.compile(r"^点击 (\w+) -> \((\d+),(\d+)\)$"), r"tap \1 -> (\2,\3)"),
    (re.compile(r"^!! 战利品?.*$"), r"!! loot issue"),
    (re.compile(r"^载入配置.*$"), r"loading config"),
]

# ---------- 第二层：零散片段 ----------
FRAGMENTS = [
    ("点击 ", "tap "),
    (" 生效，状态=", " worked, state="),
    (" 未生效（当前 ", " no effect (now "),
    ("），换点重试", "), retry with another point"),
    ("挑战", "challenge"),
    ("补点", "retap"),
    ("前往活动", "go-to-event"),
    ("古迹演武", "Guji Yanwu"),
    ("点掉结束画面", "dismiss end screen"),
    ("兜底点击", "fallback tap"),
    ("第", "#"),
    ("次", ""),
    ("，", ", "),
    ("（", " ("),
    ("）", ") "),
    ("：", ": "),
    ("状态=", "state="),
    ("用时 ", "took "),
    ("秒", "s"),
    ("分钟", "min"),
]


def to_ascii(s: str) -> str:
    """把一行日志里的中文换成英文（保留前缀、数字、时间、坐标）。"""
    nl = "\n" if s.endswith("\n") else ""
    line = s.rstrip("\n")

    # 拆出 [HH:MM:SS] 前缀，正文单独匹配，避免前缀干扰
    m = re.match(r"^(\[[^\]]*\]\s*)(.*)$", line)
    prefix, body = (m.group(1), m.group(2)) if m else ("", line)
    lead = body[:len(body) - len(body.lstrip())]
    body = body.strip()

    for pat, rep in LINE_PATTERNS:
        if pat.match(body):
            return prefix + lead + pat.sub(rep, body) + nl

    out = body
    for f, t in FRAGMENTS:
        out = out.replace(f, t)
    # 兜底：剩下的中文一律变 ?
    out = re.sub(r"[\u3000-\u9fff\uff00-\uffef]+", "?", out)
    return prefix + lead + out + nl


def enable_ascii_console():
    """把 stdout/stderr 包一层，输出前做 ASCII 化。"""
    if getattr(sys.stdout, "_ascii_wrapped", False):
        return

    class _W:
        def __init__(self, stream):
            self._s = stream
            self._ascii_wrapped = True

        def write(self, data):
            try:
                self._s.write(to_ascii(data))
            except Exception:
                try:
                    self._s.write(str(data).encode("ascii", "replace").decode("ascii"))
                except Exception:
                    pass

        def flush(self):
            try:
                self._s.flush()
            except Exception:
                pass

        def __getattr__(self, name):
            return getattr(self._s, name)

    sys.stdout = _W(sys.stdout)
    sys.stderr = _W(sys.stderr)


if __name__ == "__main__":
    samples = [
        "[10:26:14]     点击 dismiss -> (270,953) 点掉结束画面",
        "[10:26:18] 结束：成功 2 次，失败 0 次，总耗时 0.6 分钟，平均 17.1 秒/次",
        "[10:25:57]  检测到结束画面（分数 0.992，战斗耗时 9.1s），立刻点击继续",
        "--- 第 3/300 次 ---",
        "[10:26:11]    第 2 次点击后仍在 end {'end_text': 0.99}，再点一次",
        "[10:26:18]     成功  用时 16.1s  累计成功 2 失败 0",
        "[10:25:40] 阴阳师 古迹演武 自动刷取启动  目标次数=2",
        "[10:25:40] 随机落点=开启（拟人化）",
        "[10:17:45] 当前画面状态: prep  {'score': 1.0, 'x': 1728, 'y': 857}",
        "[10:14:55]    点击 go -> (1734,930) 前往活动",
        "[10:14:56]    go -> (1734,930) 生效，状态=prep {'score': 0.72}",
    ]
    for s in samples:
        print(to_ascii(s))
