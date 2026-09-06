# AI Knowledge Center / SkillHub

SkillHub is a small, Git-backed knowledge center for Claude Code, Codex, Trae, Cursor, and any other MCP client. Markdown files are the only source of truth. The server keeps a disposable in-memory index and exposes a token-efficient two-step retrieval flow:

```text
search_knowledge / recommend_knowledge  ->  compact candidates
get_knowledge                          ->  one complete document
```

The MVP intentionally has no database, embedding service, or Web UI. Those can be added later behind the existing repository and index interfaces.

## Architecture

```text
Git repository
  └─ knowledge/
       ├─ skills/{skill-name}/SKILL.md + optional subresources
       └─ prompts/workflows/templates/rules/*.md
       │
       ▼
KnowledgeRepository ── parse + validate + file fingerprint
       │
       ▼
KnowledgeIndex ─────── atomic in-memory lexical index
       │                         ▲
       │                         │ watchdog + read-time freshness check
       ▼                         │
KnowledgeService ────────────────┘
       ├─ CLI: validate / search / reindex / status
       └─ MCP: search / get / list / recommend
```

Design decisions:

- **Git is authoritative.** The index is derived in memory and can always be rebuilt.
- **Fresh on every call.** A filesystem watcher proactively rebuilds after any skill package change. Each read also compares path, modification time, and size, so a missed watcher event cannot serve stale content.
- **Small MCP responses by default.** Search, recommend, and list return metadata summaries only. `get_knowledge(id)` returns the selected `SKILL.md` and a resource manifest; `get_knowledge(id, resource)` returns only one requested subresource.
- **Portable paths and runtime.** The implementation uses `pathlib`, UTF-8, `uv`, and `watchdog` on Windows, macOS, and Linux.
- **Extension seams are explicit.** A future vector index implements the index contract; a Web UI calls the service layer. Neither requires changing document files or MCP tool names.

More detail is in [docs/architecture.md](docs/architecture.md) and [docs/content-format.md](docs/content-format.md).

## Quick start

Install [uv](https://docs.astral.sh/uv/), then run from this repository:

```bash
uv sync --extra dev
uv run skillhub validate
uv run skillhub search "code review"
uv run skillhub status
```

Start a local MCP server over stdio:

```bash
uv run skillhub-mcp --repo /absolute/path/to/context-hub
```

Or start one shared MCP process over Streamable HTTP:

```bash
uv run skillhub-mcp --repo /absolute/path/to/context-hub --transport streamable-http --host 127.0.0.1 --port 8765
```

The shared endpoint is `http://127.0.0.1:8765/mcp`. The MVP has no authentication, so keep it bound to loopback unless you put an authenticated reverse proxy in front of it.

## Content format

Skills follow the [WorkBuddy skill package structure](https://open.workbuddy.cn/docs/skill#%E6%8A%80%E8%83%BD%E5%9F%BA%E7%A1%80%E7%BB%93%E6%9E%84):

```text
knowledge/skills/
└── {skill-name}/
    ├── SKILL.md              # required
    ├── references/           # optional reference material
    ├── scripts/              # optional executable helpers
    └── templates/            # optional reusable templates
```

Example `SKILL.md`:

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

For skills, `description`, `description_zh`, `description_en`, `version`, and `author` are required. `name` defaults to the skill directory name when omitted; when present, it must match the directory. `category`, `display_name`, `display_name_en`, `allowed-tools`, `disable-model-invocation`, and `user-invocable` are supported. Skill IDs returned by MCP are their `name`, such as `code-review`.

The other knowledge types retain the MVP single-Markdown format with `id`, `type`, `title`, and `description`. The overall catalog still supports:

- `skill`
- `prompt`
- `workflow`
- `template`
- `rule`

`tags` and `keywords` are optional string lists. Any additional front matter is preserved in `metadata`. IDs must be unique across the repository.

## CLI

All commands accept `--repo` and `--knowledge-dir` before the subcommand.

```bash
# Validate all files; exits 1 on validation errors
uv run skillhub --repo . validate

# Search title, tags, keywords, description, and body
uv run skillhub --repo . search "安全 review" --type skill --tag engineering --limit 5

# Force a complete rebuild in this CLI process
uv run skillhub --repo . reindex

# Show counts, validation errors, index time, and Git state
uv run skillhub --repo . status
```

## MCP tools

| Tool | Purpose | Returns full body? |
| --- | --- | --- |
| `search_knowledge` | Weighted keyword search with type/tag filters | No |
| `get_knowledge` | Fetch one exact ID, or one packaged-skill resource | Selected content only |
| `list_knowledge` | Paginated catalog browsing | No |
| `recommend_knowledge` | Rank candidates for a task description | No |

Search weights favor ID/title, then tags/keywords, description, and finally body. English-like tokens and Chinese characters/bigrams are indexed. This deterministic lexical search is adequate for an MVP and keeps deployment dependency-free beyond the MCP SDK.

Packaged-skill retrieval example:

```json
{"id": "ai-native-prd"}
```

The response contains the main `SKILL.md` body and paths such as `references/writing-details.md`. Load one only when its instructions require it:

```json
{"id": "ai-native-prd", "resource": "references/writing-details.md"}
```

## Agent configuration

Replace `/ABSOLUTE/PATH/context-hub` with this repository's absolute path. On Windows, JSON may use forward slashes such as `D:/projects/context-hub`.

### Claude Code

Project-scoped `.mcp.json`:

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

CLI alternative:

```bash
claude mcp add --transport stdio skillhub -- uv --directory /ABSOLUTE/PATH/context-hub run skillhub-mcp --repo /ABSOLUTE/PATH/context-hub
```

### Codex

Add this to `~/.codex/config.toml`, or to `.codex/config.toml` in a trusted project:

```toml
[mcp_servers.skillhub]
command = "uv"
args = ["--directory", "/ABSOLUTE/PATH/context-hub", "run", "skillhub-mcp", "--repo", "/ABSOLUTE/PATH/context-hub"]
startup_timeout_sec = 20
tool_timeout_sec = 60
```

Codex CLI alternative:

```bash
codex mcp add skillhub -- uv --directory /ABSOLUTE/PATH/context-hub run skillhub-mcp --repo /ABSOLUTE/PATH/context-hub
```

### Cursor

Use `.cursor/mcp.json` in a project or `~/.cursor/mcp.json` globally. Its JSON body is the same stdio configuration shown for Claude Code.

### Trae

This repository already includes both parts of the Trae integration:

- `.trae/mcp.json` starts the repository's MCP server with `${workspaceFolder}`.
- `.trae/skills/skillhub-router/SKILL.md` tells Trae when and how to discover shared skills progressively.

After cloning, open the repository root in Trae, install `uv`, and enable **Project-level MCP** under **Settings → MCP**. Restart Trae if the project skill is not discovered immediately. No absolute path editing is required.

For a global/manual setup instead, open the MCP management panel, choose the raw JSON configuration, and add the stdio object from `examples/mcp/trae.json` with the local absolute path.

Ready-to-copy templates are in [examples/mcp](examples/mcp).

### One shared HTTP process

If you want every agent to use the exact same long-running server process, start the HTTP command from Quick start once and configure this remote server:

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

For Codex, use:

```toml
[mcp_servers.skillhub]
url = "http://127.0.0.1:8765/mcp"
```

Client configuration references: [Claude Code MCP](https://code.claude.com/docs/en/mcp), [Codex MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli), [Cursor MCP](https://prod.cursor.com/docs/mcp), and [Trae MCP](https://docs.trae.cn/ide_add-mcp-servers).

## Development and verification

```bash
uv run pytest
uv run skillhub validate
uv run skillhub search "release checklist"
```

The tests cover WorkBuddy-compatible skill packages, resource reference validation, duplicate IDs, Chinese/English search, staged subresource retrieval, pagination, read-time refresh, filesystem notifications, and real MCP protocol calls.

To smoke-test a running shared HTTP server with the official MCP client:

```bash
uv run python scripts/smoke_http.py --url http://127.0.0.1:8765/mcp --query "code review"
```

## MVP boundaries and next steps

The first version deliberately omits editing APIs, authentication, persisted indexes, embeddings, and a Web UI. A sensible next sequence is:

1. Add an authenticated HTTP deployment profile and health/metrics endpoints.
2. Add a Web UI that commits reviewed changes back to Git.
3. Add a hybrid lexical/vector index behind `KnowledgeIndex`, keeping current tools and Markdown schema stable.
