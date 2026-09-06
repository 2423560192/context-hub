from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal


KnowledgeType = Literal["skill", "prompt", "workflow", "template", "rule"]
KNOWLEDGE_TYPES: frozenset[str] = frozenset(
    {"skill", "prompt", "workflow", "template", "rule"}
)


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    path: str
    message: str
    field: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"path": self.path, "message": self.message}
        if self.field:
            result["field"] = self.field
        return result


@dataclass(frozen=True, slots=True)
class KnowledgeResource:
    path: str
    kind: str
    size: int
    media_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"path": self.path, "kind": self.kind, "size": self.size}
        if self.media_type:
            result["media_type"] = self.media_type
        return result


@dataclass(frozen=True, slots=True)
class KnowledgeDocument:
    id: str
    type: KnowledgeType
    title: str
    description: str
    tags: tuple[str, ...]
    keywords: tuple[str, ...]
    content: str
    path: Path
    relative_path: str
    metadata: dict[str, Any] = field(default_factory=dict)
    resources: tuple[KnowledgeResource, ...] = ()
    mtime_ns: int = 0

    def summary(self, *, score: float | None = None, reason: str | None = None) -> dict[str, Any]:
        result: dict[str, Any] = {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "tags": list(self.tags),
            "path": self.relative_path,
        }
        if score is not None:
            result["score"] = round(score, 3)
        if reason:
            result["reason"] = reason
        if "version" in self.metadata:
            result["version"] = self.metadata["version"]
        if self.resources:
            result["resources_count"] = len(self.resources)
        return result

    def detail(self) -> dict[str, Any]:
        return {
            **self.summary(),
            "keywords": list(self.keywords),
            "metadata": self.metadata,
            "content": self.content,
            "resources": [resource.to_dict() for resource in self.resources],
        }
