# Advanced Usage & Maintenance Reference

> [中文](advanced.md)

> The README keeps only the quick start. This document collects everything else: deployment modes, full per-client setup, Windows autostart, Trae proactive search, FAQ, and maintainer commands. The skill/document format spec lives in [content-format.en.md](content-format.en.md), and the architecture in [architecture.md](architecture.md).

## Deployment Modes at a Glance

| Scenario | Approach |
| --- | --- |
| Personal use on one machine | Long-running HTTP on localhost + Windows autostart (below); clients use `http://127.0.0.1:8765/mcp` |
| LAN / team sharing | Run the server with `--host 0.0.0.0` and open the port; clients use `http://<LAN-IP>:8765/mcp` |
| Public internet | Long-running server behind an **authenticated reverse proxy** (Nginx/Caddy). ⚠️ The MVP has no built-in auth |
| Client-launched | Use the stdio configs below and let each client start the engine on demand |

## Client Setup (full)

Shared convention: `command` launches the **engine** (context-hub) and `--repo` points to **your knowledge base**. On Windows use forward slashes, e.g. `D:/my-skills`.

### Claude Code (project `.mcp.json` or `claude mcp add`)

```json
{
  "mcpServers": {
    "skillhub": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory", "/path/to/context-hub",
        "run", "skillhub-mcp",
        "--repo", "/path/to/your-knowledge"
      ]
    }
  }
}
```

> `--directory` is the engine directory (context-hub); `--repo` is your knowledge base directory. JSON has no comments — remove the explanatory text when copying.

### Codex (`~/.codex/config.toml` or project `.codex/config.toml`)

```toml
[mcp_servers.skillhub]
command = "uv"
args = ["--directory", "/path/to/context-hub", "run", "skillhub-mcp", "--repo", "/path/to/your-knowledge"]
startup_timeout_sec = 20
tool_timeout_sec = 60
```

### Cursor

`.cursor/mcp.json` (project) or `~/.cursor/mcp.json` (global) — same JSON as Claude Code.

### Trae

- HTTP mode: **Settings → MCP → Add HTTP server**, then paste `http://127.0.0.1:8765/mcp` (simplest)
- stdio / project level: project root `.trae/mcp.json` — same JSON as Claude Code (remember to point `--repo` at your knowledge base)

Ready-made templates for every client: see [../examples/mcp](../examples/mcp).

## Windows Autostart (recommended for personal machines)

Silently starts the shared HTTP service at login, so clients do not need stdio configs.

```powershell
# 1. Create scripts\start-skillhub.vbs (adjust the paths)
#    Set shell = CreateObject("WScript.Shell")
#    shell.Run """D:\context-hub\scripts\start-skillhub-mcp.bat"" D:\my-skills 8765", 0, False
# 2. Copy it into the Startup folder
$startup = [Environment]::GetFolderPath('Startup')
Copy-Item D:\context-hub\scripts\start-skillhub.vbs "$startup\SkillHub-MCP.vbs"
```

Verify / manage:

```powershell
Start-Process wscript.exe -ArgumentList '"D:\context-hub\scripts\start-skillhub.vbs"'
Get-NetTCPConnection -LocalPort 8765 -State Listen     # LISTENING means success
taskkill /PID <PID> /F                                  # stop the service (restarts at next login)
```

Alternatives: Task Scheduler (on logon) or NSSM as a Windows service (no logon needed, auto-restart on crash).

## Trae: Making the Agent Search Proactively (router skill)

SkillHub content lives in MCP, so a Trae agent only discovers your skills after it **searches** first. The bundled `.trae/skills/skillhub-router/SKILL.md` is a "mandatory router" skill that requires: **any task starts with recommend/search against the knowledge base; run the matched skill; built-in skills are only a fallback**.

```text
Using it with Trae (pick one):
A. Project level: copy the whole .trae/skills/skillhub-router/ directory into the target project root
B. Global level: copy it into Trae's global skills directory (Windows CN: %USERPROFILE%\.trae-cn\skills\...)
Configure the MCP server, then restart Trae so it rescans skills.
```

> If the agent still does not search proactively, turn the SKILL.md content into a Trae "rule" (fully injected, read every session) — the behavior is equivalent.

## Knowledge Base and Skill Format

- A skill is a directory `{skill-name}/SKILL.md` with optional `references/`, `scripts/`, and `templates/` sub-resources; category directories can be Chinese and multi-level, and their names automatically become searchable tags
- Required frontmatter: `description`, `description_zh`, `description_en`, `version`, `author`; `name` is optional but when present must equal the leaf directory name and be unique across the library (ASCII)
- ⚠️ If a frontmatter value contains an English colon `: `, quote the value — otherwise YAML fails and the skill is skipped
- Full spec: [content-format.en.md](content-format.en.md)

## FAQ

**Q: The agent says there is no relevant skill / it only sees built-in skills and cannot find my library?**
A: First check that `skillhub` is connected in the MCP panel with all 4 tools visible (if not, re-paste the config and restart). Then confirm the server was started with `--repo` pointing at your knowledge base and that `validate` passes. Built-in skills ≠ SkillHub — SkillHub content only appears after an active search (the Trae router skill solves the "proactive" part).

**Q: `validate` reports errors / some skills are not indexed?**
A: Three common causes: required fields (`description`/`description_zh`/`description_en`/`version`/`author`) missing, or a value containing an English colon without quotes; `name` not matching the leaf directory name or duplicated; or the body referencing a nonexistent file via `@references|scripts|templates/...`. Fix them one by one and validate again.

**Q: I changed the knowledge base — do I need to restart the service?**
A: No. The file watcher rebuilds the index automatically; `git pull` updates are picked up as well.

**Q: The port is taken / the server will not start?**
A: Run `Get-NetTCPConnection -LocalPort 8765 -State Listen` to find the blocker; change the port with the bat script's second argument or with `--port`.

**Q: I want to switch to or add another knowledge base?**
A: Change `--repo` (or the environment variables `SKILLHUB_REPO` / `SKILLHUB_KNOWLEDGE_DIR` / `SKILLHUB_TRANSPORT` / `SKILLHUB_HOST` / `SKILLHUB_PORT`) and restart the service.

## Development & Verification (maintainers)

```bash
uv run pytest
uv run skillhub validate
uv run python scripts/smoke_http.py --url http://127.0.0.1:8765/mcp --query "release"
```

Test coverage: WorkBuddy skill packages, sub-resource reference validation, duplicate IDs, Chinese/English search, sub-resource loading, pagination, refresh-on-read, filesystem watching, and real MCP protocol calls.

## MVP Boundaries

Not included in the current version: editing API, authentication, persistent index, embedding/vector search, and a web UI. Sensible next steps: authenticated HTTP deployment → web editing UI → hybrid lexical/vector index. Architecture: [architecture.md](architecture.md).
