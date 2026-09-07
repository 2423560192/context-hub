from pathlib import Path

from skillhub.repository import KnowledgeRepository


def test_scan_valid_document(knowledge_repo: Path) -> None:
    documents, issues = KnowledgeRepository(knowledge_repo).scan()
    assert not issues
    assert [document.id for document in documents] == ["review"]
    assert documents[0].metadata["version"] == "1.0.0"
    assert [resource.path for resource in documents[0].resources] == [
        "references/checklist.md",
        "templates/report.md",
    ]


def test_validation_reports_bad_front_matter(knowledge_repo: Path) -> None:
    bad = knowledge_repo / "knowledge" / "bad.md"
    bad.write_text("# no front matter", encoding="utf-8")
    documents, issues = KnowledgeRepository(knowledge_repo).scan()
    assert len(documents) == 1
    assert any("front matter" in issue.message for issue in issues)


def test_duplicate_ids_are_rejected(knowledge_repo: Path) -> None:
    duplicate = knowledge_repo / "knowledge" / "duplicate.md"
    duplicate.write_text(
        """---
id: review
type: prompt
title: Duplicate
description: Duplicate id example
---
Body
""",
        encoding="utf-8",
    )
    documents, issues = KnowledgeRepository(knowledge_repo).scan()
    assert len(documents) == 1
    assert any("duplicate id" in issue.message for issue in issues)


def test_skill_name_must_match_directory(knowledge_repo: Path) -> None:
    path = knowledge_repo / "knowledge" / "skills" / "review" / "SKILL.md"
    text = path.read_text(encoding="utf-8").replace("name: review", "name: another-name")
    path.write_text(text, encoding="utf-8")
    documents, issues = KnowledgeRepository(knowledge_repo).scan()
    assert not documents
    assert any("must match the skill directory" in issue.message for issue in issues)


def test_skill_name_defaults_to_directory(knowledge_repo: Path) -> None:
    path = knowledge_repo / "knowledge" / "skills" / "review" / "SKILL.md"
    text = path.read_text(encoding="utf-8").replace("name: review\n", "")
    path.write_text(text, encoding="utf-8")
    documents, issues = KnowledgeRepository(knowledge_repo).scan()
    assert not issues
    assert documents[0].id == "review"


def test_missing_referenced_resource_is_rejected(knowledge_repo: Path) -> None:
    path = knowledge_repo / "knowledge" / "skills" / "review" / "SKILL.md"
    text = path.read_text(encoding="utf-8").replace(
        "@references/checklist.md", "@references/missing.md"
    )
    path.write_text(text, encoding="utf-8")
    documents, issues = KnowledgeRepository(knowledge_repo).scan()
    assert not documents
    assert any("referenced skill resource does not exist" in issue.message for issue in issues)


def test_loose_skill_markdown_is_rejected(knowledge_repo: Path) -> None:
    loose = knowledge_repo / "knowledge" / "skills" / "loose.md"
    loose.write_text("not a packaged skill", encoding="utf-8")
    _, issues = KnowledgeRepository(knowledge_repo).scan()
    assert any("skills/{skill-name}/SKILL.md" in issue.message for issue in issues)
