# AI 知识中心 / SkillHub

SkillHub 是一个面向 Claude Code、Codex、Trae、Cursor 以及其他任意 MCP 客户端的轻量级、基于 Git 的知识中心。Markdown 文件是唯一的事实来源（Single Source of Truth）。服务端维护一份可随时重建的内存索引，并提供节省 Token 的两步检索流程：

```text
search_knowledge / recommend_knowledge  ->  紧凑的候选结果
get_knowledge                          ->  一篇完整文档
```

MVP 刻意不包含数据库、Embedding 服务和 Web 界面，这些能力后续可以在现有 repository 与 index 接口之上逐步增加。

## 架构

```text
Git 仓库
  └─ knowledge/
       ├─ skills/{skill-name}/SKILL.md + 可选子资源
       └─ prompts/workflows/templates/rules/*.md
       │
       ▼
KnowledgeRepository ── 解析 + 校验 + 文件指纹
       │
       ▼
KnowledgeIndex ─────── 原子更新的内存词法索引
       │                         ▲
       │                         │ 文件监听 + 读取时新鲜度检查
       ▼                         │
KnowledgeService ────────────────┘
       ├─ CLI: validate / search / reindex / status
       └─ MCP: search / get / list / recommend
```

设计决策：

- **以 Git 为准。** 索引派生自内存且可随时重建。

- **每次调用都新鲜。** 文件系统监听器会在任何技能包变更后主动重建索引；每次读取还会比对路径、修改时间和文件大小，即使漏掉监听事件也不会读到过期内容。

- **MCP 响应默认短小。** `search`、`recommend`、`list` 只返回元数据摘要。`get_knowledge(id)` 返回所选 `SKILL.md` 正文和资源清单；`get_knowledge(id, resource)` 只返回指定的某一个子资源。

- **可移植的路径与运行时。** 实现使用 `pathlib`、UTF-8、`uv` 和 `watchdog`，兼容 Windows、macOS、Linux。

- **扩展点明确。** 未来的向量索引只需实现 index 契约；Web 界面只调用 service 层。两者都不需要改动文档文件或 MCP 工具名。

更多细节见 [docs/architecture.md](docs/architecture.md) 与 [docs/content-format.md](docs/content-format.md)。

## 快速开始

先安装 [uv](https://docs.astral.sh/uv/)，然后在仓库目录下执行：

```bash
uv sync --extra dev
uv run skillhub validate
uv run skillhub search "code review"
uv run skillhub status
```

通过 stdio 启动本地 MCP 服务器：

```bash
uv run skillhub-mcp --repo /absolute/path/to/context-hub
```

或者通过 Streamable HTTP 启动一个共享的 MCP 进程：

```bash
uv run skillhub-mcp --repo /absolute/path/to/context-hub --transport streamable-http --host 127.0.0.1 --port 8765
```

共享端点为 `http://127.0.0.1:8765/mcp`。MVP 没有鉴权，因此请将其绑定到回环地址，除非你在前面架设了带鉴权的反向代理。

## 内容格式

技能遵循 [WorkBuddy 技能包结构](https://open.workbuddy.cn/docs/skill#%E6%8A%80%E8%83%BD%E5%9F%BA%E7%A1%80%E7%BB%93%E6%9E%84)：

```text
knowledge/skills/
└── {skill-name}/
    ├── SKILL.md              # 必需
    ├── references/           # 可选的参考资料
    ├── scripts/              # 可选的可执行辅助脚本
    └── templates/            # 可选的可复用模板
```

`SKILL.md` 示例：

```markdown
---
name: code-review
display_name: 代码审查
display_name_en: Code Review
description: Review changes for correctness and security. Trigger for code review requests.
description_zh: 检查代码正确性、安全问题和回归风险。
description_en: Review code for correctness, security issues, and regressions.
category: software-development
version: 1.0.0
author: Your Name
---
# Instructions

Full skill instructions go here. Load details from @references/checklist.md only when needed.
```

对技能而言，`description`、`description_zh`、`description_en`、`version` 和 `author` 为必填项。省略 `name` 时默认取技能目录名；填写时必须与目录名一致。支持 `category`、`display_name`、`display_name_en`、`allowed-tools`、`disable-model-invocation` 和 `user-invocable`。MCP 返回的技能 ID 即其 `name`，例如 `code-review`。

其余知识类型沿用 MVP 的单 Markdown 文件格式，包含 `id`、`type`、`title` 和 `description`。整体目录仍支持以下类型：

- `skill`

- `prompt`

- `workflow`

- `template`

- `rule`

`tags` 和 `keywords` 为可选字符串列表。其他任意 Front Matter 字段会保留在 `metadata` 中。整个仓库内 `id` 必须唯一。

## CLI

所有子命令前都可加 `--repo` 和 `--knowledge-dir`。

```bash
# 校验全部文件；存在校验错误时退出码为 1
uv run skillhub --repo . validate

# 搜索标题、标签、关键词、描述和正文
uv run skillhub --repo . search "安全 review" --type skill --tag engineering --limit 5

# 在当前 CLI 进程中强制全量重建索引
uv run skillhub --repo . reindex

# 显示数量统计、校验错误、索引时间与 Git 状态
uv run skillhub --repo . status
```

## MCP 工具

| 工具                    | 用途                      | 是否返回完整正文 |
| --------------------- | ----------------------- | -------- |
| `search_knowledge`    | 带类型/标签过滤的加权关键词搜索        | 否        |
| `get_knowledge`       | 按精确 ID 获取，或获取技能包中的某个子资源 | 仅所选内容    |
| `list_knowledge`      | 分页浏览目录                  | 否        |
| `recommend_knowledge` | 依据任务描述对候选内容排序推荐         | 否        |

搜索权重依次偏向 ID/标题、标签/关键词、描述，最后是正文。支持对英文类 token 以及中文单字/双字组合（bigram）建索引。这种确定性词法搜索对 MVP 已经足够，除 MCP SDK 外不引入额外部署依赖。

获取技能包示例：

```json
{"id": "ai-native-prd"}
```

响应会包含主 `SKILL.md` 正文以及诸如 `references/writing-details.md` 的资源路径。只有当技能指令确实需要时才去加载单个资源：

```json
{"id": "ai-native-prd", "resource": "references/writing-details.md"}
```

## 引擎与内容解耦：指向你自己的知识库

SkillHub 的代码（引擎）与内容（`knowledge/`）是分离的：本仓库里的 `knowledge/` 只是示例内容，你可以让服务指向**任意一个含** **`knowledge/`** **目录的仓库或文件夹**，包括你自己的私有知识库。

三种指定方式（优先级：命令行参数 > 环境变量 > 默认值）：

```bash
# 1. 命令行参数
uv run skillhub-mcp --repo /path/to/your-knowledge-repo

# 2. 环境变量（不写 --repo / --knowledge-dir 时生效）
set SKILLHUB_REPO=D:\your-knowledge-repo        # Windows PowerShell 用 $env:SKILLHUB_REPO=...
set SKILLHUB_KNOWLEDGE_DIR=knowledge
set SKILLHUB_TRANSPORT=streamable-http
```

```bash
# 先校验你的内容是否合规
uv run skillhub --repo /path/to/your-knowledge-repo validate
```

使用示例：本仓库 `scripts/start-skillhub-mcp.bat` 支持直接传入知识库路径启动共享 HTTP 服务：

```text
start-skillhub-mcp.bat                          # 默认用本仓库示例知识库
start-skillhub-mcp.bat D:\MySkills\my-knowledge 8765
```

注意：`knowledge/` 目录结构、`SKILL.md` Front Matter 字段与 ID 唯一性要求见 [docs/content-format.md](docs/content-format.md)。校验不通过的内容不会被索引。

## Agent 配置

将 `/ABSOLUTE/PATH/context-hub` 替换为本仓库的绝对路径，或替换为上文你自己的知识库路径。在 Windows 上，JSON 中可使用正斜杠，例如 `D:/projects/context-hub`。

### Claude Code

项目级 `.mcp.json`：

```json
{
  "mcpServers": {
    "skillhub": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/context-hub",
        "run",
        "skillhub-mcp",
        "--repo",
        "/ABSOLUTE/PATH/context-hub"
      ]
    }
  }
}
```

CLI 方式：

```bash
claude mcp add --transport stdio skillhub -- uv --directory /ABSOLUTE/PATH/context-hub run skillhub-mcp --repo /ABSOLUTE/PATH/context-hub
```

### Codex

将其加入 `~/.codex/config.toml`，或可信项目下的 `.codex/config.toml`：

```toml
[mcp_servers.skillhub]
command = "uv"
args = ["--directory", "/ABSOLUTE/PATH/context-hub", "run", "skillhub-mcp", "--repo", "/ABSOLUTE/PATH/context-hub"]
startup_timeout_sec = 20
tool_timeout_sec = 60
```

Codex CLI 方式：

```bash
codex mcp add skillhub -- uv --directory /ABSOLUTE/PATH/context-hub run skillhub-mcp --repo /ABSOLUTE/PATH/context-hub
```

### Cursor

使用项目内的 `.cursor/mcp.json`，或全局的 `~/.cursor/mcp.json`。其 JSON 内容与上方 Claude Code 的 stdio 配置相同。

### Trae

本仓库的 Trae 集成包含两部分：

- `.trae/mcp.json`：用 `${workspaceFolder}` 启动本仓库的 MCP 服务器。

- `.trae/skills/skillhub-router/SKILL.md`：告诉 Trae 何时以及如何渐进式地发现共享技能。

克隆后在 Trae 中打开仓库根目录，安装 `uv`，并在 **设置 → MCP** 中启用 **项目级 MCP**。如果项目技能未能立即被发现，请重启 Trae。无需手工编辑绝对路径。

若改用全局/手动配置，请打开 MCP 管理面板，选择原生 JSON 配置，填入 `examples/mcp/trae.json` 中的 stdio 配置并替换为本地绝对路径。

可直接复制的配置模板见 [examples/mcp](examples/mcp)。

### 一个共享的 HTTP 进程

如果你希望所有 Agent 使用完全相同的常驻服务进程，按"快速开始"中的 HTTP 命令启动一次，然后配置为远程服务器：

```json
{
  "mcpServers": {
    "skillhub": {
      "type": "http",
      "url": "http://127.0.0.1:8765/mcp"
    }
  }
}
```

Codex 使用：

```toml
[mcp_servers.skillhub]
url = "http://127.0.0.1:8765/mcp"
```

客户端配置参考：[Claude Code MCP](https://code.claude.com/docs/en/mcp)、[Codex MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)、[Cursor MCP](https://prod.cursor.com/docs/mcp)、[Trae MCP](https://docs.trae.cn/ide_add-mcp-servers)。

## 开发与验证

```bash
uv run pytest
uv run skillhub validate
uv run skillhub search "release checklist"
```

测试覆盖：WorkBuddy 兼容技能包、资源引用校验、重复 ID、中英文搜索、按阶段加载子资源、分页、读取时刷新、文件系统通知，以及真实的 MCP 协议调用。

用官方 MCP 客户端对运行中的共享 HTTP 服务器做冒烟测试：

```bash
uv run python scripts/smoke_http.py --url http://127.0.0.1:8765/mcp --query "code review"
```

## MVP 边界与下一步

首个版本刻意不含编辑 API、鉴权、持久化索引、Embedding 和 Web 界面。合理的下一步顺序：

1. 增加带鉴权的 HTTP 部署配置，以及健康检查/指标端点。
2. 增加 Web 界面，可将审核通过的修改提交回 Git。
3. 在 `KnowledgeIndex` 之后增加词法/向量混合索引，同时保持现有工具与 Markdown schema 稳定。

