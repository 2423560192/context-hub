from __future__ import annotations

import math
import re
import threading
import unicodedata
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from .models import KnowledgeDocument


_ASCII_WORD = re.compile(r"[a-z0-9][a-z0-9._+/#-]*")
_CJK_RUN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]+")


def normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text).casefold().strip()


def tokens(text: str) -> set[str]:
    value = normalize(text)
    result = set(_ASCII_WORD.findall(value))
    for run in _CJK_RUN.findall(value):
        result.add(run)
        result.update(run)
        if len(run) > 1:
            result.update(run[index : index + 2] for index in range(len(run) - 1))
    return {item for item in result if item}


@dataclass(frozen=True, slots=True)
class SearchHit:
    document: KnowledgeDocument
    score: float
    reason: str


class KnowledgeIndex:
    """Small, deterministic in-memory index optimized for repository-sized collections."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._documents: dict[str, KnowledgeDocument] = {}
        self._field_tokens: dict[str, dict[str, set[str]]] = {}
        self._document_frequency: Counter[str] = Counter()

    def replace(self, documents: Iterable[KnowledgeDocument]) -> None:
        new_documents = {document.id: document for document in documents}
        field_tokens: dict[str, dict[str, set[str]]] = {}
        frequency: Counter[str] = Counter()
        for document in new_documents.values():
            localized_descriptions = " ".join(
                str(document.metadata.get(field, ""))
                for field in ("description_zh", "description_en")
            )
            fields = {
                "id": tokens(document.id),
                "title": tokens(document.title),
                "description": tokens(f"{document.description} {localized_descriptions}"),
                "tags": tokens(" ".join(document.tags)),
                "keywords": tokens(" ".join(document.keywords)),
                "content": tokens(document.content),
            }
            field_tokens[document.id] = fields
            all_tokens = set().union(*fields.values())
            frequency.update(all_tokens)
        with self._lock:
            self._documents = new_documents
            self._field_tokens = field_tokens
            self._document_frequency = frequency

    def get(self, document_id: str) -> KnowledgeDocument | None:
        with self._lock:
            return self._documents.get(document_id)

    def count(self) -> int:
        with self._lock:
            return len(self._documents)

    def list(
        self,
        *,
        kind: str | None = None,
        tags: Iterable[str] | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[KnowledgeDocument], int]:
        required_tags = {normalize(tag) for tag in tags or [] if tag.strip()}
        with self._lock:
            matches = [
                document
                for document in self._documents.values()
                if (kind is None or document.type == kind)
                and required_tags.issubset({normalize(tag) for tag in document.tags})
            ]
        matches.sort(key=lambda document: (document.type, document.id))
        return matches[offset : offset + limit], len(matches)

    def search(
        self,
        query: str,
        *,
        kinds: Iterable[str] | None = None,
        tags: Iterable[str] | None = None,
        limit: int = 5,
    ) -> list[SearchHit]:
        query_normalized = normalize(query)
        query_tokens = tokens(query)
        allowed_kinds = set(kinds or [])
        required_tags = {normalize(tag) for tag in tags or [] if tag.strip()}
        if not query_tokens and not required_tags and not allowed_kinds:
            return []

        weights = {"id": 8.0, "title": 7.0, "tags": 6.0, "keywords": 5.0, "description": 3.0, "content": 1.0}
        hits: list[SearchHit] = []
        with self._lock:
            total = max(len(self._documents), 1)
            for document in self._documents.values():
                if allowed_kinds and document.type not in allowed_kinds:
                    continue
                normalized_tags = {normalize(tag) for tag in document.tags}
                if not required_tags.issubset(normalized_tags):
                    continue
                fields = self._field_tokens[document.id]
                score = 0.0
                matched_fields: list[str] = []
                for field, weight in weights.items():
                    overlap = query_tokens & fields[field]
                    if overlap:
                        matched_fields.append(field)
                    for term in overlap:
                        df = self._document_frequency.get(term, 0)
                        score += weight * (math.log((total + 1) / (df + 1)) + 1.0)

                phrase_fields = {
                    "id": normalize(document.id),
                    "title": normalize(document.title),
                    "tags": normalize(" ".join(document.tags)),
                    "keywords": normalize(" ".join(document.keywords)),
                    "description": normalize(document.description),
                }
                if query_normalized:
                    for field, value in phrase_fields.items():
                        if query_normalized == value:
                            score += weights[field] * 3.0
                        elif query_normalized in value:
                            score += weights[field] * 1.5
                if score <= 0 and query_tokens:
                    continue
                reason = "matched " + ", ".join(dict.fromkeys(matched_fields)) if matched_fields else "matched filters"
                hits.append(SearchHit(document=document, score=score, reason=reason))
        hits.sort(key=lambda hit: (-hit.score, hit.document.id))
        return hits[:limit]
