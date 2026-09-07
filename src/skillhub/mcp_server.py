from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Sequence

from mcp.server.fastmcp import FastMCP

from .service import KnowledgeService
from .watcher import KnowledgeWatcher


INSTRUCTIONS = (
    "SkillHub is a Git-backed knowledge catalog. Use search_knowledge or recommend_knowledge first; "
    "they return only compact candidates. Call get_knowledge only for the selected id. "
    "For packaged skills, inspect the returned resource manifest and request only a needed resource "
    "with get_knowledge(id, resource). Use list_knowledge for browsing, not bulk-loading."
)


def create_server(service: KnowledgeService, *, host: str = "127.0.0.1", port: int = 8765) -> FastMCP:
    mcp = FastMCP("AI Knowledge Center / SkillHub", instructions=INSTRUCTIONS, json_response=True, host=host, port=port)

    @mcp.tool()
    def search_knowledge(
        query: str,
        types: list[str] | None = None,
        tags: list[str] | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Search metadata and content, returning compact candidates only. Call get_knowledge next."""
        return service.search(query, kinds=types, tags=tags, limit=limit)

    @mcp.tool()
    def get_knowledge(id: str, resource: str | None = None) -> dict[str, Any]:
        """Get one knowledge item, or one named skill resource after inspecting its resource manifest."""
        try:
            return service.get(id, resource=resource)
        except KeyError as exc:
            raise ValueError(str(exc)) from exc

    @mcp.tool()
    def list_knowledge(
        type: str | None = None,
        tags: list[str] | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> dict[str, Any]:
        """List paginated knowledge summaries, optionally filtered by type and tags."""
        return service.list(kind=type, tags=tags, offset=offset, limit=limit)

    @mcp.tool()
    def recommend_knowledge(
        task: str,
        types: list[str] | None = None,
        tags: list[str] | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Recommend compact candidates for a described task. Fetch the chosen item separately."""
        return service.recommend(task, kinds=types, tags=tags, limit=limit)

    return mcp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="skillhub-mcp", description="Run the SkillHub MCP server")
    parser.add_argument("--repo", type=Path, default=Path(os.getenv("SKILLHUB_REPO", Path.cwd())))
    parser.add_argument("--knowledge-dir", default=os.getenv("SKILLHUB_KNOWLEDGE_DIR", "knowledge"))
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default=os.getenv("SKILLHUB_TRANSPORT", "stdio"),
    )
    parser.add_argument("--host", default=os.getenv("SKILLHUB_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("SKILLHUB_PORT", "8765")))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    service = KnowledgeService(args.repo, args.knowledge_dir)
    watcher = KnowledgeWatcher(service.repository.knowledge_root, service.reindex)
    watcher.start()
    service.set_watching(True)
    server = create_server(service, host=args.host, port=args.port)
    try:
        server.run(transport=args.transport)
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(f"SkillHub MCP server failed: {exc}", file=sys.stderr)
        return 1
    finally:
        service.set_watching(False)
        watcher.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
