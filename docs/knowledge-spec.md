# Knowledge Item 规范

Context Hub 中的 Skill、Prompt、Workflow、Template 等内容统一抽象为 `KnowledgeItem`。

## 文件格式

使用 Markdown + YAML Front Matter：

```markdown
---
id: python-async-debug
name: Python 异步问题排查
type: skill
description: 用于排查 asyncio、Task exception 等异步问题。
tags:
  - python
  - asyncio
keywords:
  - async
  - await
version: 1.0.0
updated_at: 2026-09-06
---

正文内容。
```

## 推荐字段

- `id`：全局唯一 ID，建议使用小写短横线格式
- `name`：展示名称
- `type`：内容类型
- `description`：简短描述，用于搜索结果展示
- `tags`：分类标签
- `keywords`：搜索关键词
- `version`：版本号
- `updated_at`：最后更新时间

## type 建议值

- `skill`
- `prompt`
- `workflow`
- `template`
- `rule`
- `doc`
- `example`

## 设计原则

1. metadata 要尽量短，方便搜索阶段低 Token 返回。
2. 正文只在 Agent 确认需要时通过 `get_knowledge` 加载。
3. `id` 必须稳定，不建议因为移动目录而修改。
4. 一个文件尽量只描述一个独立能力或知识点。
5. Git 仓库中的内容是唯一源数据，其他 Agent 本地文件视为生成产物。
