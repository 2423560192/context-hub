---
id: python-async-debug
name: Python 异步问题排查
type: skill
description: 用于排查 asyncio、未 await、Task exception was never retrieved 等异步问题。
tags:
  - python
  - asyncio
  - backend
keywords:
  - async
  - await
  - task
  - coroutine
version: 1.0.0
updated_at: 2026-09-06
---

# Python 异步问题排查

处理 Python 异步报错时，优先按以下顺序检查：

1. 确认协程是否被 `await`。
2. 检查通过 `asyncio.create_task()` 创建的任务是否保存引用并正确处理异常。
3. 对 `Task exception was never retrieved`，定位任务内部真实异常，而不是只处理外层警告。
4. 检查是否混用了同步阻塞调用，必要时改为异步库或放入线程池。
5. 检查事件循环生命周期，避免重复创建、错误关闭或跨线程使用。

输出排查结果时优先说明：根因、影响范围、最小修复方案、是否存在并发副作用。
