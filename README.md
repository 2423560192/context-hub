# SkillHub · AI 技能中心引擎

> [English](README.en.md)

把 Markdown 技能整理成一个**可检索的知识库**，通过 MCP 提供给 Claude Code、Trae、Codex、Cursor 等 AI 客户端**先检索、再按需加载**——技能再多，也不会把上下文撑爆。

> 本仓库只含**引擎代码**。技能内容放在你自己的知识库仓库/文件夹里（引擎自带 `knowledge/` 分类骨架，可直接用）。引擎用 `--repo` 指向哪里，就服务哪里的内容。

> **提示：** SkillHub 的技能要**主动检索**才可见——Agent 不会自动翻你的技能库，这正是它不撑爆上下文的原因。想让 Trae 的 Agent 每次任务先搜知识库再用技能，给它装上仓库自带的 **skillhub-router 路由技能**（`.trae/skills/skillhub-router`，用法见 [docs/advanced.md](docs/advanced.md)）。

## 快速开始（约 3 分钟）

**1. 安装引擎**（需先装 [uv](https://docs.astral.sh/uv/)，它是唯一依赖）

```bash
git clone <引擎仓库地址> context-hub
cd context-hub
uv sync
```

**2. 放一个技能进去**

以引擎自带骨架为例，新建 `knowledge/skills/demo/SKILL.md`，整段复制下面模板即可（`name` 可省，目录名就是技能 id）：

```markdown
---
description: 一句话说明本技能的能力与触发场景。
description_zh: 简短中文介绍。
description_en: Short English introduction.
version: 1.0.0
author: 你的名字
---
正文写要注入给 Agent 的指令。需要附加资料时，把它们放进本技能目录下的 references/、scripts/ 或 templates/ 子目录，再在正文里按需引用。
```

> 说明：正文里按 `@references/文件名` 的格式引用子资源，引擎会校验该文件必须真实存在。技能格式完整规范见 [docs/content-format.md](docs/content-format.md)。也可以直接克隆一份现成的知识库仓库，启动时把 `--repo` 指过去即可。

**3. 启动共享服务（HTTP，一个地址所有客户端共用）**

```bash
uv run skillhub-mcp --repo . --transport streamable-http --port 8765
```

**4. 客户端接入并验证**

给任意 AI 客户端添加一个 MCP 服务器，填同一个地址：

```json
{ "mcpServers": { "skillhub": { "type": "http", "url": "http://127.0.0.1:8765/mcp" } } }
```

- Claude Code / Cursor：把上面 JSON 写入项目 `.mcp.json` / `.cursor/mcp.json`

- Trae：设置 → MCP → 添加 HTTP，填入该地址

- 各客户端详细配置与现成模板：见 [docs/advanced.md](docs/advanced.md) 和 [examples/mcp](examples/mcp)

验证：对你的 Agent 说「调用 `search_knowledge` 搜一下 "demo"，把命中的 id 告诉我」，能返回结果即成功；或用命令行冒烟 `uv run python scripts/smoke_http.py --query demo`（默认连 127.0.0.1:8765/mcp）。

## MCP 工具（Agent 视角）

| 工具                                                 | 干什么                | 返回正文   |
| -------------------------------------------------- | ------------------ | ------ |
| `search_knowledge(query, types?, tags?, limit?)`   | 关键词搜索              | 否，紧凑候选 |
| `recommend_knowledge(task, types?, tags?, limit?)` | 按任务描述推荐            | 否，紧凑候选 |
| `list_knowledge(type?, tags?, offset?, limit?)`    | 分页浏览目录             | 否      |
| `get_knowledge(id, resource?)`                     | 取单篇完整正文；技能可再取单个子资源 | 是      |

推荐流程：先 `search_knowledge` / `recommend_knowledge` 拿 3–5 条候选 → 选最匹配的 id → `get_knowledge(id)`；技能正文引用了子资源，再按需 `get_knowledge(id, resource="references/xxx.md")`。

## 常用命令

```bash
uv run skillhub validate           # 校验知识库（有问题会列出并排除坏文件）
uv run skillhub search "发布" --limit 5
uv run skillhub status             # 文档数 / 错误 / 索引时间 / Git 状态
uv run skillhub reindex            # 强制重建索引
```

改了知识库**不用重启服务**：文件一变动，索引会自动重建。

## 它能做什么

- 一个 Git 仓库就是一个知识库，Markdown 是唯一事实来源，索引可随时重建

- 文件一改动索引自动刷新，`git pull` 后无需重启服务

- 技能可放在任意层级的分类目录（支持中文、多级），目录名自动成为可检索标签

- 中英文关键词检索，支持类型/标签过滤；只返回紧凑候选，命中后再按需取正文

- 一份引擎服务所有客户端：本机共享 HTTP 常驻，或由 Claude Code / Codex / Cursor / Trae 以 stdio 各自拉起

## License

MIT（声明于 pyproject.toml）。

## 了解更多

- [docs/advanced.md](docs/advanced.md) — 部署模式、逐客户端完整配置、Windows 开机自启、Trae 主动检索、FAQ、维护者命令

- [docs/content-format.md](docs/content-format.md) — 技能与文档格式规范

- [examples/mcp](examples/mcp) — 现成的 MCP 配置模板

- [docs/architecture.md](docs/architecture.md) — 架构设计（维护者，英文）

