# -*- coding: utf-8 -*-
"""
阴阳师「拾此一瞬」版本活动 —— 古迹演武 自动刷取脚本
=====================================================
流程（实测坐标，横屏 1920x1080）：
    活动总览 →[前往活动 (1727,925)]→ 活动详情
             →[古迹演武 (420,435)]→ 备战页
             →[挑战 (1727,857)]→ 自动战斗
             →[结束画面「点击屏幕继续」]→ 点击屏幕中央 → 回到备战页
             → 重复 N 次

用法：
    python grind.py                 # 默认刷 300 次
    python grind.py --runs 10       # 刷 10 次（先这样试跑）
    python grind.py --runs 300 --yes
    python grind.py --stats         # 只做一次状态识别，不点任何东西

脚本会自动把每次战斗的耗时、成功/失败写入 logs/grind_时间戳.log，
失败时会自动重新导航回备战页继续。
"""
from __future__ import annotations

import argparse
import os
import sys
import time

from tasks.event_dungeon.game import Game, T_CENTER, T_CHALLENGE  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
LOGDIR = os.path.join(HERE, "logs")


def main():
    ap = argparse.ArgumentParser(description="阴阳师 古迹演武 自动刷取")
    ap.add_argument("--runs", type=int, default=300, help="刷取次数（默认 300）")
    ap.add_argument("--yes", action="store_true", help="跳过开始前确认")
    ap.add_argument("--stats", action="store_true", help="只识别一次当前状态，不操作")
    ap.add_argument("--debug-shots", action="store_true", help="失败时保存截图到 shots/dbg")
    ap.add_argument("--serial", default=None, help="adb 设备号，默认 emulator-5554")
    ap.add_argument("--no-jitter", action="store_true",
                    help="关闭随机落点（每次都点固定坐标，默认开启拟人随机）")
    ap.add_argument("--seed", type=int, default=None, help="随机种子（复现同一串随机落点）")
    ap.add_argument("--ascii", dest="ascii", action="store_true", default=None,
                    help="控制台用英文输出（cmd 中文乱码时用，日志文件仍是中文）")
    ap.add_argument("--cn-console", dest="ascii", action="store_false",
                    help="控制台照原样输出中文（终端本身是 UTF-8 时用）")
    args = ap.parse_args()

    # 默认策略：输出被重定向（双击 bat / 管道）时用英文，避免 cmd 代码页 936 乱码
    if args.ascii is None:
        args.ascii = not sys.stdout.isatty()

    os.makedirs(LOGDIR, exist_ok=True)
    logpath = os.path.join(LOGDIR, time.strftime("grind_%Y%m%d_%H%M%S.log"))
    logf = open(logpath, "a", encoding="utf-8")

    def log(msg, also_print=True):
        line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
        logf.write(line + "\n")          # 日志文件始终 UTF-8 中文
        logf.flush()
        if also_print:
            if args.ascii:
                from ascii_out import to_ascii
                line = to_ascii(line)    # 控制台英文，cmd 不乱码
            print(line, flush=True)

    g = Game(serial=args.serial, debug=args.debug_shots, verbose=False,
             jitter=not args.no_jitter, seed=args.seed)
    g.log = log          # 把 Game 的日志接入文件

    log("=" * 70)
    log(f"阴阳师 古迹演武 自动刷取启动  目标次数={args.runs}")
    log(f"设备={g.a.serial}  adb={g.a.adb}")
    log(f"随机落点={'开启（拟人化）' if not args.no_jitter else '关闭（固定坐标）'}"
        + (f"  seed={args.seed}" if args.seed is not None else ""))

    # ---- 状态识别 ----
    st, info = g.detect()
    log(f"当前画面状态: {st}  {info}")

    if args.stats:
        log("--stats 模式，直接退出")
        return 0

    if st == "battle":
        log("检测到正在战斗中，等待本场结束后接管...")
        st, _, info = g.wait_state(("end", "prep"), timeout=300, interval=0.5)
        log(f"战场结束，状态={st} {info}")
        if st == "end":
            g.a.tap(*TAP_CENTER)
            time.sleep(1.5)

    # ---- 导航到备战页 ----
    if not g.go_to_prep():
        log("!! 无法进入备战页，请确认游戏停在「活动总览/活动详情/古迹演武」任一页面")
        g.shot("nav_failed")
        return 2
    log("已在古迹演武备战页")

    if not args.yes:
        print(f"\n即将开始刷 {args.runs} 次古迹演武（约 {args.runs * 25 / 60:.0f} 分钟）。")
        ans = input("回车开始，输入 n 取消: ").strip().lower()
        if ans == "n":
            log("用户取消")
            return 0

    # ---- 主循环 ----
    ok_cnt = fail_cnt = 0
    total_t = time.time()
    for i in range(1, args.runs + 1):
        # 挑战次数耗尽就停下来（灰按钮亮像素极少）
        ready, ratio = g.challenge_ready()
        if not ready:
            log(f"!! 挑战键不可点（亮像素占比 {ratio}，可点时应 ≥0.12），可能次数已耗尽，停止脚本")
            break

        log(f"--- 第 {i}/{args.runs} 次 ---")
        ok, dur, bminfo = g.one_battle()
        if ok:
            ok_cnt += 1
            log(f"    成功  用时 {dur:.1f}s  累计成功 {ok_cnt} 失败 {fail_cnt}")
        else:
            fail_cnt += 1
            log(f"    !! 失败 {bminfo}")
            if args.debug_shots:
                g.shot(f"fail_{i}")
            # 失败恢复：确保回到备战页
            log("    尝试恢复到备战页...")
            if not g.go_to_prep():
                log("    !! 恢复失败，停止脚本")
                break
        # 两轮之间随机停顿，模拟人放下手机又拿起来的节奏
        g.human.maybe_long_pause(0.18)

    cost = time.time() - total_t
    log("=" * 70)
    log(f"结束：成功 {ok_cnt} 次，失败 {fail_cnt} 次，总耗时 {cost/60:.1f} 分钟，"
        f"平均 {cost/max(1, ok_cnt+fail_cnt):.1f} 秒/次")
    log(f"日志文件：{logpath}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
