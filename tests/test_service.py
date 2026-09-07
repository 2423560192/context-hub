from pathlib import Path

import pytest

from skillhub.service import KnowledgeService


def test_search_then_get(knowledge_repo: Path) -> None:
    service = KnowledgeService(knowledge_repo)
    result = service.search("安全", limit=3)
    assert result["count"] == 1
    assert "content" not in result["results"][0]
    detail = service.get(result["results"][0]["id"])
    assert "authorization" in detail["content"]
    assert detail["resources"][0]["path"] == "references/checklist.md"


def test_search_by_tag_and_description(knowledge_repo: Path) -> None:
    service = KnowledgeService(knowledge_repo)
    assert service.search("regression")["results"][0]["id"] == "review"
    assert service.search("", tags=["安全"])["count"] == 1


def test_get_missing_id(knowledge_repo: Path) -> None:
    service = KnowledgeService(knowledge_repo)
    with pytest.raises(KeyError):
        service.get("missing")


def test_automatic_freshness_check(knowledge_repo: Path) -> None:
    service = KnowledgeService(knowledge_repo)
    package = knowledge_repo / "knowledge" / "skills" / "new"
    package.mkdir()
    path = package / "SKILL.md"
    path.write_text(
        """---
name: new
display_name: Fresh content
description: Added after service startup
description_zh: 服务启动后添加
description_en: Added after service startup
version: 1.0.0
author: Test Author
---
The newest instructions.
""",
        encoding="utf-8",
    )
    assert service.get("new")["content"] == "The newest instructions."


def test_get_skill_resource_on_demand(knowledge_repo: Path) -> None:
    service = KnowledgeService(knowledge_repo)
    detail = service.get("review")
    assert "Verify access control" not in detail["content"]
    resource = service.get("review", resource="@references/checklist.md")
    assert "Verify access control" in resource["content"]


def test_skill_resource_refreshes_without_restart(knowledge_repo: Path) -> None:
    service = KnowledgeService(knowledge_repo)
    path = knowledge_repo / "knowledge" / "skills" / "review" / "references" / "checklist.md"
    path.write_text("# Checklist\n\nUpdated resource content.", encoding="utf-8")
    assert "Updated resource content" in service.get(
        "review", resource="references/checklist.md"
    )["content"]


def test_list_is_paginated(knowledge_repo: Path) -> None:
    service = KnowledgeService(knowledge_repo)
    result = service.list(limit=1)
    assert result["total"] == 1
    assert result["limit"] == 1
