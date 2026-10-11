# -*- coding: utf-8 -*-
"""通过 GitHub REST API 把本项目推上去（不依赖 git 命令，纯 Python + 标准库）。

为什么用 API：这台机器上没装 git，而且 PowerShell 的 HTTPS 有问题，
但 Python 的网络是通的（实测 github API 200）。
本脚本只做两件事：
  1) 首次：创建仓库（如果不存在）
  2) 之后：把工作区的文件按「新增/更新」提交上去（每次 commit 写清楚加了什么）

用法（在项目目录下）：
    set GH_TOKEN=github_pat_xxx
    python tools/gh_push.py --repo yys-auto-script --message "新增：xxx"

需要 token 具备 repo 权限（classic PAT 勾 repo，或 fine-grained 给 Contents: Read and write）。
token 只从环境变量读，绝不要写进代码或提交。
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
# 不提交的东西（与 .gitignore 保持一致，这里再过滤一遍更保险）
SKIP_DIRS = {"logs", "shots", "build", "dist", "release", "__pycache__", ".git",
             ".idea", ".vscode", ".pydist", "build_tmp", "node_modules"}
SKIP_EXT = {".pyc", ".pyo", ".log", ".spec"}
SKIP_NAME_PREFIX = ("shots_out_of_ticket",)


def req(method: str, path: str, token: str, data=None):
    url = path if path.startswith("http") else API + path
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(url, data=body, method=method)
    r.add_header("Authorization", f"Bearer {token}")
    r.add_header("Accept", "application/vnd.github+json")
    r.add_header("User-Agent", "yys-push-script")
    if body:
        r.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            raw = resp.read().decode("utf-8", "replace")
            return resp.status, (json.loads(raw) if raw.strip() else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw}


def should_skip(rel: str) -> bool:
    parts = rel.replace("\\", "/").split("/")
    if any(p in SKIP_DIRS for p in parts):
        return True
    name = parts[-1]
    if os.path.splitext(name)[1].lower() in SKIP_EXT:
        return True
    if name.startswith(SKIP_NAME_PREFIX):
        return True
    # 隐藏文件里只允许 .gitignore
    if name.startswith(".") and name != ".gitignore":
        return True
    return False


def collect(root: str):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace("\\", "/")
            if should_skip(rel):
                continue
            out.append((rel, full))
    return sorted(out)


def _push_via_contents(login, args, token, files):
    """空仓库首次推送：用 Contents API 逐个 PUT。

    第一个文件写下去之后，仓库就不再是空的，后面的文件也照这个方式写，
    全部写在同一分支上（Contents API 会自动为每个文件生成提交）。
    为避免 153 个文件产生 153 条提交，这里第一个文件用 --message，
    其余用 "添加文件"（GitHub 的 Contents API 无法一次提交多文件）。
    """
    ok = 0
    fail = []
    for rel, full in files:
        with open(full, "rb") as f:
            content = f.read()
        body = {
            "message": args.message if ok == 0 else f"添加 {rel}",
            "content": base64.b64encode(content).decode(),
            "branch": args.branch,
        }
        # 路径里可能有中文文件名（比如 dev/GITHUB提交说明.md），必须 URL 编码，
        # 否则 http.client 会报 UnicodeEncodeError: 'ascii' codec can't encode...
        safe_path = "/".join(urllib.parse.quote(seg) for seg in rel.split("/"))
        st, res = req("PUT", f"/repos/{login}/{args.repo}/contents/{safe_path}",
                      token, body)
        if st in (200, 201):
            ok += 1
            if ok <= 5 or ok % 25 == 0:
                print(f"  + [{ok}/{len(files)}] {rel}", flush=True)
        else:
            fail.append((rel, st, res.get("message")))
            print(f"  !! {rel} 失败：{st} {res.get('message')}", flush=True)

    print(f"\nContents API 写入完成：成功 {ok} 个，失败 {len(fail)} 个")
    if fail:
        for rel, st, msg in fail[:10]:
            print(f"   失败 {rel}: {st} {msg}")
        return 2
    print(f"仓库地址：https://github.com/{login}/{args.repo}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="仓库名，例如 yys-auto-script")
    ap.add_argument("--message", required=True, help="本次 commit 说明（写清新加了什么）")
    ap.add_argument("--branch", default="main")
    ap.add_argument("--private", action="store_true", help="建私有仓库")
    ap.add_argument("--desc", default="阴阳师自动化脚本（MuMu + adb + tkinter 控制台）")
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    args = ap.parse_args()

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("!! 请先设置环境变量 GH_TOKEN（GitHub Personal Access Token）")
        print("   例：set GH_TOKEN=github_pat_xxx")
        return 2

    # 1) 当前用户
    st, me = req("GET", "/user", token)
    if st != 200:
        print(f"!! token 无效或权限不足：{st} {me}")
        return 2
    login = me["login"]
    print(f"已登录：{login}")

    # 2) 仓库是否存在，不存在就创建
    st, info = req("GET", f"/repos/{login}/{args.repo}", token)
    if st == 404:
        print(f"仓库 {args.repo} 不存在，正在创建...")
        st2, created = req("POST", "/user/repos", token, {
            "name": args.repo, "description": args.desc,
            "private": bool(args.private), "auto_init": False,
        })
        if st2 not in (200, 201):
            print(f"!! 创建失败：{st2} {created}")
            return 2
        print(f"已创建：{created.get('html_url')}")
    elif st != 200:
        print(f"!! 查询仓库失败：{st} {info}")
        return 2

    # 3) 取分支当前 HEAD（可能还没有）
    st, ref = req("GET", f"/repos/{login}/{args.repo}/git/ref/heads/{args.branch}", token)
    parent_sha = ref.get("object", {}).get("sha") if st == 200 else None
    base_tree = None
    if parent_sha:
        st, commit = req("GET", f"/repos/{login}/{args.repo}/git/commits/{parent_sha}", token)
        base_tree = commit.get("tree", {}).get("sha") if st == 200 else None
        print(f"已有分支 {args.branch}，HEAD={parent_sha[:8]}")

    # 4) 上传文件
    files = collect(args.root)
    print(f"准备提交 {len(files)} 个文件...")

    # 空仓库不能用 Git Data API 建首个 commit（会返回 409 Git Repository is empty），
    # 必须改用 Contents API 写第一批文件，等仓库里有了内容再走 Git Data API。
    if not parent_sha:
        print("空仓库：改用 Contents API 建立第一个提交...")
        return _push_via_contents(login, args, token, files)

    tree_items = []
    for rel, full in files:
        with open(full, "rb") as f:
            content = f.read()
        st, blob = req("POST", f"/repos/{login}/{args.repo}/git/blobs", token, {
            "content": base64.b64encode(content).decode(),
            "encoding": "base64",
        })
        if st not in (200, 201):
            print(f"!! 上传 {rel} 失败：{st} {blob}")
            return 2
        tree_items.append({"path": rel, "mode": "100644", "type": "blob",
                           "sha": blob["sha"]})
        print(f"  + {rel}")

    tree_payload = {"tree": tree_items}
    if base_tree:
        tree_payload["base_tree"] = base_tree
    st, tree = req("POST", f"/repos/{login}/{args.repo}/git/trees", token, tree_payload)
    if st not in (200, 201):
        print(f"!! 建 tree 失败：{st} {tree}")
        return 2

    commit_payload = {"message": args.message, "tree": tree["sha"]}
    if parent_sha:
        commit_payload["parents"] = [parent_sha]
    st, newc = req("POST", f"/repos/{login}/{args.repo}/git/commits", token, commit_payload)
    if st not in (200, 201):
        print(f"!! 建 commit 失败：{st} {newc}")
        return 2

    if parent_sha:
        st, _ = req("PATCH", f"/repos/{login}/{args.repo}/git/refs/heads/{args.branch}",
                    token, {"sha": newc["sha"], "force": False})
    else:
        st, _ = req("POST", f"/repos/{login}/{args.repo}/git/refs", token,
                    {"ref": f"refs/heads/{args.branch}", "sha": newc["sha"]})
    if st not in (200, 201):
        print(f"!! 更新分支失败：{st}")
        return 2

    print(f"\n完成！commit {newc['sha'][:8]}：{args.message}")
    print(f"仓库地址：https://github.com/{login}/{args.repo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
