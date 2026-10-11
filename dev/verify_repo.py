# -*- coding: utf-8 -*-
"""确认推上去的仓库内容可读、关键文件在位。"""
import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request

TOKEN = os.environ.get("GH_TOKEN")
R = "WangLuhang0131/yys_auto_script"


def get(path):
    r = urllib.request.Request("https://api.github.com" + path)
    r.add_header("Authorization", "Bearer " + TOKEN)
    r.add_header("Accept", "application/vnd.github+json")
    r.add_header("User-Agent", "yys-push")
    try:
        with urllib.request.urlopen(r, timeout=40) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


checks = ["README.md", "NOTES.md", "requirements.txt", ".gitignore",
          "tasks/jiejie_tupo/templates/t_jj_entry_bottom.png",
          "tasks/event_dungeon/templates/t_count_zero.png",
          "dev/GITHUB提交说明.md", "tools/gh_push.py"]
for p in checks:
    st, res = get("/repos/%s/contents/%s" % (R, urllib.parse.quote(p)))
    if st != 200:
        print("!!  %-52s %s %s" % (p, st, res.get("message")))
        continue
    data = base64.b64decode(res["content"])
    info = "%d 字节" % len(data)
    if p.endswith(".md") or p.endswith(".txt"):
        first = data.decode("utf-8", "replace").splitlines()[0][:36]
        info += " | " + first
    print("OK  %-52s %s" % (p, info))
