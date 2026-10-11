# 提交到 GitHub 的步骤

## ⚠️ 先说安全

**绝对不要用账号密码推送**，原因有两个：

1. GitHub 从 2021 年起**已停用密码推送**，用密码必然失败；
2. 你之前把密码发出来了 —— 建议**立刻去改密码**（GitHub → Settings → Password），
   并开启两步验证（2FA）。

正确做法是用 **Personal Access Token（PAT）**，它只授权特定范围，泄露了也能随时吊销。

---

## 方案 A：用我写好的脚本（不需要装 git）

`tools/gh_push.py` 走 GitHub REST API，纯 Python 标准库实现，**不用装 git**。

### 1. 生成 Token

1. 打开 https://github.com/settings/tokens
2. 选 **Tokens (classic)** → **Generate new token (classic)**
3. 勾选 **`repo`** 权限（要建私有仓库就再勾 `delete_repo` 不需要，`repo` 够）
4. 有效期按需选，生成后**立刻复制**（页面关了就不再显示）

### 2. 设置环境变量（当前终端有效）

```bat
set GH_TOKEN=github_pat_粘贴你的token
```

### 3. 推送

```bat
cd /d "D:\Program Files\WKSPC\yys"
python tools\gh_push.py --repo yys-auto-script --message "初始版本：活动副本 + 结界突破 + 图形界面"
```

想建**私有**仓库加 `--private`；想换分支名用 `--branch`。

之后每次改完再推：

```bat
python tools\gh_push.py --repo yys_auto_script --message "新增：xxx 功能"
```

脚本会自动跳过 `logs/`、`shots/`、`build_tmp/`、`.pydist/`、`__pycache__` 等
不需要提交的东西（同时 `.gitignore` 里也写了，用 git 命令推也一样）。

> **首次推送的说明**：仓库是空的时，GitHub 不允许用 Git Data API 建第一个 commit
> （会报 `409 Git Repository is empty`），所以脚本会退化成用 Contents API
> 逐个文件写入 —— 结果是每个文件一条 commit，历史比较碎。
> 从第二次开始仓库不再为空，脚本会走 Git Data API，**一次提交把所有改动打成一个 commit**，
> 这才是正常状态。想让首次历史也干净的话，可以在网页上把仓库删掉重建（不带 README），
> 然后用 classic token 或本地 git 推一次。

---

## 方案 B：装 git，用常规命令

### 1. 装 git

```bat
winget install Git.Git
```

### 2. 初始化并首次提交

```bat
cd /d "D:\Program Files\WKSPC\yys"
git init -b main
git add .
git commit -m "初始版本：活动副本 + 结界突破 + 图形界面"
```

### 3. 关联远程仓库并推送

先在网页上新建一个空仓库（不要勾 README），然后：

```bat
git remote add origin https://github.com/<你的用户名>/yys-auto-script.git
git push -u origin main
```

推送时会要求认证：**用户名填 GitHub 用户名，密码处粘贴 Token**（不是账号密码）。
Windows 上第一次会让你登录，凭证会被 Git 凭证管理器记住。

---

## 后续每次提交写什么

按你要求，commit 说明写清楚**这次新增了什么**，例如：

- `新增：结界突破任务（探索→结界突破→逐格挑战→自动刷新）`
- `修复：探索页底栏点错到「式神委派」，改为按图定位`
- `新增：干扰弹窗看门狗，自动关闭悬赏封印`
- `优化：随机抖动幅度收小，避免点到相邻按钮`

用 `tools/gh_push.py` 的话，就是每次 `--message "..."` 写这一句。

---

## 哪些文件会被推上去

会推：

```
gui.py start_gui.bat start_grind.bat requirements.txt README.md NOTES.md .gitignore
adbkit.py vision.py human_click.py ascii_out.py capture.py shot.py grind.py
core/                    （任务基类、运行器、导航、看门狗、路径）
tasks/*/                 （两个任务的代码 + templates/ 模板）
tools/gh_push.py tools/build_exe.py
dev/                     （开发诊断脚本，可选：不想推就自己加到 .gitignore）
```

不会推（已在 `.gitignore` 里）：

```
logs/  shots/  __pycache__/  *.pyc  build_tmp/  build/  dist/  release/  .pydist/
tasks/*/shots_out_of_ticket*.png
```

> 说明：`release/` 里的 exe 不提交是**故意的**——二进制文件放仓库会越来越大，
> 别人 clone 下来自己 `python tools/build_exe.py` 就能生成。
> 想直接分享 exe 的话，用 GitHub 的 **Releases** 功能上传附件更合适。
