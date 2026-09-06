# Architecture

## Components

`KnowledgeRepository` is the source adapter. It treats `knowledge/skills/{skill-name}/SKILL.md` as a packaged skill entrypoint, records optional `references/`, `scripts/`, and `templates/`, and keeps the original single-file parser for other knowledge types. It validates YAML, WorkBuddy skill fields, package names, referenced resources, and duplicate IDs.

`KnowledgeIndex` is a thread-safe, replace-on-rebuild index. A rebuild constructs all maps off-lock and swaps them atomically, so MCP readers never observe a partial index.

`KnowledgeService` owns freshness and application behavior. It is the only layer used by CLI and MCP adapters. It compares a cheap file fingerprint before every query and rebuilds when paths, sizes, or modification timestamps change.

`KnowledgeWatcher` observes all filesystem events under `knowledge/`, including scripts and templates, and debounces bursts from editors. It gives proactive refresh; the service fingerprint is the correctness fallback.

`mcp_server` exposes four stable tools through the official MCP Python SDK. `cli` exposes local operator commands. Neither contains parsing or ranking logic.

## Data and request flow

1. A contributor edits and commits `SKILL.md` or one of its packaged resources.
2. Each running SkillHub process receives a watcher event and atomically rebuilds its index.
3. An Agent calls `search_knowledge` or `recommend_knowledge` and receives a handful of summaries.
4. The Agent calls `get_knowledge(id)` and receives the current `SKILL.md` plus a compact resource manifest.
5. If the skill requires a subresource, the Agent calls `get_knowledge(id, resource)` for only that file.
6. If the watcher event was delayed or lost, a read detects the changed fingerprint and rebuilds synchronously before returning.

## Concurrency and failure model

- Index replacement and reads are guarded by a reentrant lock.
- Validation errors exclude only the invalid document. Valid documents remain queryable and errors appear in `validate` and `status`.
- Duplicate IDs keep the first path in deterministic sort order and report the later path as invalid.
- The server writes diagnostics to stderr; stdout remains reserved for MCP stdio framing.
- HTTP mode binds to loopback by default and does not claim production authentication.

## Extension points

- Replace or compose `KnowledgeIndex` for vector/hybrid retrieval.
- Add a Git write service and Web API without giving write capability to MCP tools.
- Add repository revision metadata or remote synchronization without changing document IDs.
- Add a persistent derived cache only when startup profiling justifies it.
