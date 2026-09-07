from __future__ import annotations

import subprocess
import threading
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .index import KnowledgeIndex
from .models import KNOWLEDGE_TYPES, ValidationIssue
from .repository import KnowledgeRepository


class KnowledgeService:
    """Application boundary used by both CLI and MCP adapters."""

    def __init__(self, root: Path | str, knowledge_dir: str = "knowledge") -> None:
        self.repository = KnowledgeRepository(root, knowledge_dir)
        self.index = KnowledgeIndex()
        self._refresh_lock = threading.RLock()
        self._fingerprint: tuple[tuple[str, int, int], ...] | None = None
        self._issues: list[ValidationIssue] = []
        self._indexed_at: datetime | None = None
        self._watching = False
        self.reindex()

    def reindex(self) -> dict[str, Any]:
        with self._refresh_lock:
            documents, issues = self.repository.scan()
            self.index.replace(documents)
            self._issues = issues
            self._fingerprint = self.repository.fingerprint()
            self._indexed_at = datetime.now(timezone.utc)
            return {
                "indexed": len(documents),
                "invalid": len(issues),
                "indexed_at": self._indexed_at.isoformat(),
            }

    def ensure_fresh(self) -> None:
        current = self.repository.fingerprint()
        if current != self._fingerprint:
            self.reindex()

    def validate(self) -> dict[str, Any]:
        self.reindex()
        return {
            "valid": not self._issues,
            "documents": self.index.count(),
            "issues": [issue.to_dict() for issue in self._issues],
        }

    def search(
        self,
        query: str,
        *,
        kinds: Iterable[str] | None = None,
        tags: Iterable[str] | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        self.ensure_fresh()
        checked_kinds = self._validate_kinds(kinds)
        limit = max(1, min(limit, 20))
        hits = self.index.search(query, kinds=checked_kinds, tags=tags, limit=limit)
        return {
            "query": query,
            "count": len(hits),
            "results": [hit.document.summary(score=hit.score, reason=hit.reason) for hit in hits],
            "next_step": (
                "Call get_knowledge with the best id to load its main content and resource manifest; "
                "for a skill resource, call get_knowledge again with id and resource path."
            ),
        }

    def get(self, document_id: str, resource: str | None = None) -> dict[str, Any]:
        self.ensure_fresh()
        document = self.index.get(document_id)
        if document is None:
            raise KeyError(f"knowledge id not found: {document_id}")
        if resource is not None:
            normalized = resource.strip().removeprefix("@").replace("\\", "/")
            match = next((item for item in document.resources if item.path == normalized), None)
            if match is None:
                raise KeyError(f"resource not found for '{document_id}': {resource}")
            if match.size > 1_000_000:
                raise ValueError(f"resource is too large to return through MCP: {match.size} bytes")
            resource_path = (document.path.parent / normalized).resolve()
            if document.path.parent.resolve() not in resource_path.parents:
                raise ValueError("resource path escapes the skill package")
            try:
                content = resource_path.read_text(encoding="utf-8-sig")
            except UnicodeError as exc:
                raise ValueError(f"resource is not UTF-8 text: {normalized}") from exc
            except OSError as exc:
                raise KeyError(f"cannot read resource: {normalized}") from exc
            return {
                "id": document.id,
                "type": document.type,
                "resource": match.to_dict(),
                "content": content,
            }
        return document.detail()

    def list(
        self,
        *,
        kind: str | None = None,
        tags: Iterable[str] | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> dict[str, Any]:
        self.ensure_fresh()
        if kind is not None:
            self._validate_kinds([kind])
        offset = max(0, offset)
        limit = max(1, min(limit, 100))
        documents, total = self.index.list(kind=kind, tags=tags, offset=offset, limit=limit)
        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "results": [document.summary() for document in documents],
        }

    def recommend(
        self,
        task: str,
        *,
        kinds: Iterable[str] | None = None,
        tags: Iterable[str] | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        result = self.search(task, kinds=kinds, tags=tags, limit=limit)
        result["task"] = result.pop("query")
        result["recommendation_policy"] = "lexical relevance across title, tags, keywords, description, and content"
        return result

    def status(self) -> dict[str, Any]:
        self.ensure_fresh()
        documents, _ = self.index.list(limit=100_000)
        counts = Counter(document.type for document in documents)
        return {
            "repository": str(self.repository.root),
            "knowledge_directory": str(self.repository.knowledge_root),
            "documents": len(documents),
            "by_type": {kind: counts.get(kind, 0) for kind in sorted(KNOWLEDGE_TYPES)},
            "invalid": len(self._issues),
            "issues": [issue.to_dict() for issue in self._issues],
            "watching": self._watching,
            "indexed_at": self._indexed_at.isoformat() if self._indexed_at else None,
            "git": self._git_status(),
        }

    def set_watching(self, value: bool) -> None:
        self._watching = value

    @staticmethod
    def _validate_kinds(kinds: Iterable[str] | None) -> list[str] | None:
        if kinds is None:
            return None
        values = list(kinds)
        invalid = sorted(set(values) - KNOWLEDGE_TYPES)
        if invalid:
            raise ValueError(f"unknown knowledge type(s): {', '.join(invalid)}")
        return values

    def _git_status(self) -> dict[str, Any]:
        try:
            branch = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repository.root,
                check=False,
                capture_output=True,
                text=True,
                timeout=2,
            ).stdout.strip()
            changes = subprocess.run(
                ["git", "status", "--porcelain", "--", self.repository.knowledge_root],
                cwd=self.repository.root,
                check=False,
                capture_output=True,
                text=True,
                timeout=2,
            ).stdout.splitlines()
            return {"available": True, "branch": branch or None, "knowledge_changes": len(changes)}
        except (OSError, subprocess.SubprocessError):
            return {"available": False}
