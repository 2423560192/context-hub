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


def _write_nested_skill(repo: Path, *segments: str, name: str | None = None) -> None:
    package = repo.joinpath("knowledge", "skills", *segments)
    package.mkdir(parents=True)
    skill_name = name or segments[-1]
    (package / "SKILL.md").write_text(
        f"""---
name: {skill_name}
description: 嵌套分类技能，用于测试中文目录分类。
description_zh: 嵌套分类技能，用于测试中文目录分类。
description_en: A nested skill used to test Chinese category directories.
version: 1.0.0
author: Test Author
---
# Nested

Body with details.
""",
        encoding="utf-8",
    )


def test_nested_chinese_category_skill_is_discovered(knowledge_repo: Path) -> None:
    _write_nested_skill(knowledge_repo, "前端测试", "登录", "login-check")
    documents, issues = KnowledgeRepository(knowledge_repo).scan()
    assert not issues
    ids = [document.id for document in documents]
    assert "login-check" in ids and "review" in ids
    nested = next(document for document in documents if document.id == "login-check")
    assert nested.tags[:2] == ("前端测试", "登录")
    assert "knowledge/skills/前端测试/登录/login-check/SKILL.md" in nested.relative_path


def test_empty_category_directory_is_allowed(knowledge_repo: Path) -> None:
    (knowledge_repo / "knowledge" / "skills" / "待整理").mkdir(parents=True)
    documents, issues = KnowledgeRepository(knowledge_repo).scan()
    assert not issues
    assert [document.id for document in documents] == ["review"]


def test_nested_skill_name_must_match_leaf_directory(knowledge_repo: Path) -> None:
    _write_nested_skill(knowledge_repo, "测试", "regression", name="wrong-name")
    documents, issues = KnowledgeRepository(knowledge_repo).scan()
    assert "regression" not in [document.id for document in documents]
    assert any("must match the skill directory" in issue.message for issue in issues)
