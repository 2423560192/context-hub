# Context Hub

统一管理 AI Agent 的 Skill、Prompt、Workflow 和上下文资产，通过 MCP 实现多 Agent 共享、检索与按需加载。

## 目标

Context Hub 用来解决多个 AI Agent 之间上下文资产分散、重复维护和版本不同步的问题。

统一数据源：

```text
Git Repository
      ↓
Context Hub
      ↓
MCP Server
      ↓
Claude Code / Codex / Trae / Cursor / 其他 Agent
```

## 核心原则

- Git 仓库作为唯一真实数据源（Single Source of Truth）
- Skill、Prompt、Workflow、Template 等统一使用 Markdown 管理
- MCP 不一次性注入所有内容，而是先搜索、再按需加载
- 修改一份内容后，所有连接同一 MCP 的 Agent 都能获取最新版本
- 不支持 MCP 的 Agent 通过 Adapter 同步生成本地配置

## 计划支持的内容

- `skill`：能力包、操作规范、领域方法
- `prompt`：可复用提示词
- `workflow`：任务流程
- `template`：代码或文档模板
- `rule`：Agent 行为规则
- `doc`：知识文档
- `example`：示例与最佳实践

## 目录结构

```text
context-hub/
├─ skills/
├─ prompts/
├─ workflows/
├─ templates/
├─ rules/
├─ docs/
└─ README.md
```

## MCP 设计

第一阶段计划提供：

- `search_knowledge`：搜索相关知识，只返回简短元数据
- `get_knowledge`：按 ID 获取完整内容
- `list_knowledge`：按类型、标签等浏览
- `recommend_knowledge`：根据当前任务推荐相关内容

典型调用流程：

```text
用户任务
  ↓
search_knowledge
  ↓
返回 3~5 个候选
  ↓
get_knowledge
  ↓
只加载真正需要的内容
```

这样可以避免 Skill 数量变多以后大量消耗上下文 Token。

## Knowledge Item 格式

所有知识项推荐使用 Markdown + YAML Front Matter：

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
---

这里写真正需要提供给 Agent 的正文。
```

详细规范见 [`docs/knowledge-spec.md`](docs/knowledge-spec.md)。

## Roadmap

### Phase 1 - MVP

- [ ] Markdown + Front Matter 解析
- [ ] 本地知识索引
- [ ] 关键词 / 标签搜索
- [ ] MCP Server
- [ ] 文件修改自动刷新
- [ ] CLI 校验与搜索

### Phase 2

- [ ] Agent Adapter
- [ ] Claude / Codex / Trae / Cursor 配置生成
- [ ] Web 管理后台
- [ ] Git diff / commit 管理

### Phase 3

- [ ] Embedding 检索
- [ ] Reranker
- [ ] Knowledge 推荐
- [ ] 多设备同步

## 项目定位

Context Hub 不只是一个 Skill 文件读取器，而是一套 **Agent Context Infrastructure**：统一管理、检索、选择、加载和同步 AI Agent 所需要的上下文资产。
