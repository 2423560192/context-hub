# SkillHub · AI Skill Center Engine

> [中文](README.md)

Turn a folder of Markdown skills into a **searchable knowledge base** and serve it to AI clients — Claude Code, Trae, Codex, Cursor and others — through MCP with a **search-first, load-on-demand** flow. No matter how many skills you add, it never blows up the context window.

> This repository contains **engine code only**. Your skill content lives in your own knowledge-base repository or folder (the engine ships a ready-to-use `knowledge/` category skeleton). The engine serves whichever content `--repo` points to.

> **Note:** SkillHub content is only visible when **actively searched** — agents will not browse your skill library on their own; that is exactly why it keeps contexts small. To make a Trae agent search the knowledge base first on every task, install the bundled **skillhub-router routing skill** (`.trae/skills/skillhub-router`, see [docs/advanced.en.md](docs/advanced.en.md)).

## Quick Start (~3 minutes)

**1. Install the engine** (install [uv](https://docs.astral.sh/uv/) first — it is the only dependency)

```bash
git clone <your-engine-repo-url> context-hub
cd context-hub
uv sync
```

**2. Add a skill**

Using the bundled skeleton as an example, create `knowledge/skills/demo/SKILL.md` and copy the template below (`name` is optional — the directory name becomes the skill id):

```markdown
---
description: One sentence describing what this skill does and when to trigger it.
description_zh: 简短中文介绍。
description_en: Short English introduction.
version: 1.0.0
author: Your Name
---
Body: write the instructions that will be injected into the agent. To attach extra material, put files under this skill's references/, scripts/ or templates/ subdirectories and reference them on demand.
```

> Note: reference sub-resources in the body with the `@references/file-name` syntax; the engine validates that the file actually exists. See [docs/content-format.en.md](docs/content-format.en.md) for the full skill format spec. You can also clone an existing knowledge repository and point `--repo` to it when starting.

**3. Start the shared service (HTTP — one address shared by every client)**

```bash
uv run skillhub-mcp --repo . --transport streamable-http --port 8765
```

**4. Connect a client and verify**

Add an MCP server to any AI client and fill in the same address:

```json
{ "mcpServers": { "skillhub": { "type": "http", "url": "http://127.0.0.1:8765/mcp" } } }
```

- Claude Code / Cursor: write the JSON above into `.mcp.json` / `.cursor/mcp.json` in your project
- Trae: Settings → MCP → Add HTTP server, then paste the address
- Per-client details and ready-made templates: see [docs/advanced.en.md](docs/advanced.en.md) and [examples/mcp](examples/mcp)

Verify: tell your agent to "call `search_knowledge` for "demo" and tell me the id of the match" — success is when it returns results. Or use the CLI smoke test: `uv run python scripts/smoke_http.py --query demo` (defaults to 127.0.0.1:8765/mcp).

## MCP Tools (agent's view)

| Tool                                                   | Purpose            | Returns full content |
| ------------------------------------------------------ | ------------------ | -------------------- |
| `search_knowledge(query, types?, tags?, limit?)`       | Keyword search     | No, compact hits     |
| `recommend_knowledge(task, types?, tags?, limit?)`     | Recommend for a task description | No, compact hits |
| `list_knowledge(type?, tags?, offset?, limit?)`        | Browse paginated catalog | No                |
| `get_knowledge(id, resource?)`                         | Get one full item; skills can fetch a single sub-resource | Yes |

Recommended flow: call `search_knowledge` / `recommend_knowledge` for 3–5 candidates → pick the best id → `get_knowledge(id)`; if the skill body references sub-resources, fetch only what you need with `get_knowledge(id, resource="references/xxx.md")`.

## Common Commands

```bash
uv run skillhub validate           # validate the knowledge base (lists problems, excludes broken files)
uv run skillhub search "发布" --limit 5
uv run skillhub status             # document count / errors / index time / Git status
uv run skillhub reindex            # force a full index rebuild
```

No need to **restart the service** after editing the knowledge base — the index rebuilds automatically when files change.

## Features

- A Git repository is your knowledge base; Markdown is the single source of truth and the index can be rebuilt anytime
- Index refreshes automatically on file changes — no restart needed after `git pull`
- Skills can live in category directories at any depth (Chinese names and multiple levels supported); directory names become searchable tags
- Bilingual keyword search (English + Chinese) with type/tag filters; only compact candidates are returned, full content is fetched on demand
- One engine serves every client: a long-running shared HTTP server, or stdio processes launched by Claude Code / Codex / Cursor / Trae

## License

MIT (declared in pyproject.toml).

## Learn More

- [docs/advanced.en.md](docs/advanced.en.md) — deployment modes, full per-client configs, Windows autostart, Trae proactive search, FAQ, maintainer commands
- [docs/content-format.en.md](docs/content-format.en.md) — skill and document format spec
- [examples/mcp](examples/mcp) — ready-made MCP configuration templates
- [docs/architecture.md](docs/architecture.md) — architecture design (maintainers)
