from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from .service import KnowledgeService


def _print(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="skillhub", description="Manage and query a Git-backed SkillHub repository")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="repository root (default: current directory)")
    parser.add_argument("--knowledge-dir", default="knowledge", help="knowledge directory relative to repository root")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate", help="validate every knowledge Markdown file")

    search = subparsers.add_parser("search", help="search summaries without loading full content")
    search.add_argument("query")
    search.add_argument("--type", dest="kinds", action="append", choices=["skill", "prompt", "workflow", "template", "rule"])
    search.add_argument("--tag", dest="tags", action="append")
    search.add_argument("--limit", type=int, default=5)

    subparsers.add_parser("reindex", help="force a full in-memory index rebuild and report the result")
    subparsers.add_parser("status", help="show index, validation, watcher, and Git status")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    service = KnowledgeService(args.repo, args.knowledge_dir)
    try:
        if args.command == "validate":
            result = service.validate()
            _print(result)
            return 0 if result["valid"] else 1
        if args.command == "search":
            _print(service.search(args.query, kinds=args.kinds, tags=args.tags, limit=args.limit))
            return 0
        if args.command == "reindex":
            _print(service.reindex())
            return 0
        if args.command == "status":
            _print(service.status())
            return 0
    except (KeyError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

