# -*- coding: utf-8 -*-
"""公共库：任务基类、任务发现、运行器。

任务只依赖这一层 + 根目录的 adbkit / vision / humanize，
任务之间**互不 import**，所以删掉任意 tasks/<名字>/ 都不影响别人。
"""
from core.tasks import TaskBase, TaskContext, discover, load_task   # noqa: F401
from core.runner import TaskRunner                                  # noqa: F401
