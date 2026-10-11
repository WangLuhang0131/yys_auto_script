# 阴阳师脚本控制台

MuMu 模拟器 + adb 实现的阴阳师自动化脚本，带图形界面。

**核心特点**：全部基于 adb 截图 + 模板匹配，不读内存、不注入、不改游戏文件，
只模拟点击。**模拟器窗口放后台甚至最小化都能正常跑**（实测）。

---

## 1. 环境要求

| 项目 | 要求 |
|---|---|
| 模拟器 | MuMu Player 12（默认端口 `emulator-5554`） |
| 分辨率 | 游戏 1920×1080 横屏（MuMu 默认竖屏 1080×1920，截图会自动旋转） |
| Python | 3.10+（用打包好的 exe 则不需要装） |
| 依赖 | `Pillow`、`numpy`（`pip install -r requirements.txt`） |

`adb.exe` 会在这些位置自动查找：MuMu 自带目录 `E:\MuMuPlayer\nx_main\adb.exe`、
`PATH` 里的 `adb`。要改的话编辑 `adbkit.py` 顶部的 `ADB` / `SERIAL`。

## 2. 怎么用

### 方式 A：用打包好的 exe（推荐给不装 Python 的人）

`release/` 里有两个版本，任选：

| 文件 | 说明 |
|---|---|
| `阴阳师脚本控制台.exe` | **单文件**，31.9 MB，拷给别人直接双击就行 |
| `阴阳师脚本控制台_文件夹版\` | 整个文件夹，启动更快、兼容性更好（某些限制 Temp 写入的环境只有这个能跑） |

### 方式 B：源码运行

```bat
pip install -r requirements.txt
start_gui.bat          :: 或 python gui.py
```

### 出问题时自检

```bat
阴阳师脚本控制台.exe --selftest
```

会在旁边生成 `selftest.log`，里面列清楚：模块能不能导入、任务有没有发现、
模板有没有打进去、tkinter 是否可用。**windowed 程序出错没提示，遇到问题先跑这个。**

界面长这样：

```
┌────────────────────────┬──────────────────────────────────────────────┐
│ 任务列表               │  活动战斗 (3/300)              [清空日志]     │
│  ▸ 活动副本（古迹演武）│  [10:31:07] --- 第 3/300 次 ---              │
│  ▸ 结界突破            │  [10:31:08]   点击 challenge -> (1722,858)   │
│                        │  [10:31:18]   检测到结束画面（0.992）        │
│ 目标次数 [ 300 ]       │  [10:31:19]   本轮完成，用时 16.3s           │
│ 截图模式 [ color ▾]    │  ...                                          │
│ [▶ 执行任务]           │                                              │
│ [■ 结束任务]           │                                              │
└────────────────────────┴──────────────────────────────────────────────┘
```

左边选任务、设次数、执行/结束；右边实时日志和 `战斗(x/y)` 进度。
**在庭院主界面启动最省事**（脚本会自己走到对应页面）。

## 3. 任务说明

### 任务①：活动副本（拾此一瞬 → 古迹演武）

从庭院自动点右侧「活动」进活动总览 → 前往活动 → 古迹演武 → 循环刷。

**自动停止条件**（三层判据，按可靠性排序）：
1. 备战页「剩余挑战次数 = 0」（最可靠）；
2. 点挑战后弹出「琥珀卷轴不足」提示；
3. 连续 3 次点挑战进不了战斗。

### 任务②：结界突破

从庭院 → 探索 → 结界突破 → 检查阵容锁定 → 逐个打 9 个格子 → 自动刷新 → 循环。
灰格（已攻破）自动跳过。

**自动停止条件**：突破券用完（点进攻后 20 秒没进战斗），或连续 3 轮无可打格子。

### 两个任务共同的收尾行为

- 任务结束（或你点「结束任务」）后**自动把游戏送回庭院**，保证下次从已知状态启动；
- 跑的过程中有**独立线程**盯着干扰弹窗（如「悬赏封印」），一出现就自动点掉它——
  这类弹窗会把战斗卡死。

## 4. 目录结构

```
yys/
├─ start_gui.bat         双击启动界面
├─ gui.py                 界面（自动扫描 tasks/，不写死任何任务）
├─ core/                  公共：任务基类、任务发现、运行器、导航、弹窗看门狗、路径
├─ adbkit.py              adb 封装（截图 / 点击 / 坐标）
├─ vision.py              模板匹配（numpy FFT，无需 opencv）
├─ human_click.py         拟人化点击（随机落点 + 按图找点）
├─ ascii_out.py           控制台英文输出（cmd 不乱码）
├─ tasks/
│  ├─ event_dungeon/     任务①（task.py 入口 + game.py + templates/）
│  └─ jiejie_tupo/       任务②（task.py + attack.py + ui.py + templates/）
├─ tools/                 打包 / 推送脚本
├─ dev/                   开发期诊断脚本（平时不用）
└─ logs/                  运行日志（UTF-8）
```

**任务互相隔离**：任务之间互不 import、互不继承，只依赖 `core/` 和根目录公共工具。
删掉任意一个 `tasks/xxx/`，其它任务和界面照常工作。

## 5. 加一个自己的任务

1. 建目录 `tasks/我的任务/`，放 `__init__.py` 和 `task.py`；
2. 写一个 `Task` 类，实现 `run(self, ctx)`；
3. 界面点「刷新任务列表」。

```python
from core.tasks import TaskBase

class Task(TaskBase):
    name = "我的任务"
    desc = "说明文字"
    supports_runs = True

    def run(self, ctx):
        ctx.log("开始干活")
        for i in range(1, ctx.target_runs + 1):
            if ctx.stopped():
                break
            ctx.set_progress(i, ctx.target_runs, "战斗")   # 界面显示 战斗(3/300)
            ctx.human.tap("challenge")                     # 随机落点点击
            ctx.sleep(1.0)
```

## 6. 打 exe（给别人用）

```bat
python tools\build_exe.py                  :: 单文件 exe（默认），产物在 release\
python tools\build_exe.py --onedir         :: 文件夹版
python tools\build_exe.py --console        :: 带控制台窗口，用来排查启动问题
```

如果 `pip install pyinstaller` 装不上（受限环境 / 代理问题）：

```bat
python tools\fetch_wheels_manual.py        :: 直接从 PyPI 下 wheel 解压到 .pydist\
```

`core/paths.py` 启动时会自动把 `.pydist\` 挂到 `sys.path`。

## 7. 注意

- 只模拟点击，不改游戏数据；请自行承担使用风险。
- 换模拟器或改分辨率后，坐标与模板需要重新标定（见 `dev/` 里的标定脚本）。
- 详细的实测数据、判据来源、踩坑记录见 [NOTES.md](NOTES.md)。
