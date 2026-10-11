# -*- coding: utf-8 -*-
"""验证 GitHub token：打印账号信息、确认权限范围。token 从环境变量 GH_TOKEN 读。"""
import json
import os
import sys
import urllib.request
import urllib.error

API = "https://api.github.com"


def get(path, token):
    r = urllib.request.Request(API + path)
    r.add_header("Authorization", f"Bearer {token}")
    r.add_header("Accept", "application/vnd.github+json")
    r.add_header("User-Agent", "yys-push")
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


token = os.environ.get("GH_TOKEN")
if not token:
    print("!! 没有 GH_TOKEN")
    sys.exit(1)

st, me = get("/user", token)
print("GET /user ->", st)
if st == 200:
    print("  用户名:", me.get("login"))
    print("  显示名:", me.get("name"))
    print("  邮箱:", me.get("email"))
else:
    print(" ", me)
    sys.exit(1)

# 看已有仓库
st2, repos = get(f"/users/{me['login']}/repos?per_page=100", token)
if st2 == 200:
    print(f"\n现有仓库 {len(repos)} 个:")
    for r in repos:
        print(f"  {r['name']:30s} private={r['private']}")
else:
    print("查仓库失败:", st2, repos)

# 检查目标仓库名有没有被占
st3, chk = get(f"/repos/{me['login']}/yys-auto-script", token)
print(f"\n检查 yys-auto-script -> {st3} ({'已存在' if st3 == 200 else '不存在，可创建' if st3 == 404 else chk})")
