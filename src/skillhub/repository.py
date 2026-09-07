from __future__ import annotations

import mimetypes
import re
from pathlib import Path
from typing import Any

import yaml

from .models import KNOWLEDGE_TYPES, KnowledgeDocument, KnowledgeResource, ValidationIssue


_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
_FRONT_MATTER_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n?", re.DOTALL)


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return str(value)


def _string_list(value: Any, field: str, path: str, issues: list[ValidationIssue]) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        issues.append(ValidationIssue(path, "must be a list of strings", field))
        return ()
    cleaned = tuple(dict.fromkeys(item.strip() for item in value if item.strip()))
    return cleaned


class KnowledgeRepository:
    """Loads Markdown documents from the repository; it never mutates source files."""

    def __init__(self, root: Path | str, knowledge_dir: str = "knowledge") -> None:
        self.root = Path(root).expanduser().resolve()
        self.knowledge_root = (self.root / knowledge_dir).resolve()

    def fingerprint(self) -> tuple[tuple[str, int, int], ...]:
        if not self.knowledge_root.exists():
            return ()
        rows: list[tuple[str, int, int]] = []
        for path in sorted(self.knowledge_root.rglob("*")):
            if not path.is_file():
                continue
            try:
                stat = path.stat()
            except OSError:
                continue
            rows.append((path.relative_to(self.root).as_posix(), stat.st_mtime_ns, stat.st_size))
        return tuple(rows)

    def scan(self) -> tuple[list[KnowledgeDocument], list[ValidationIssue]]:
        if not self.knowledge_root.exists():
            return [], [
                ValidationIssue(
                    self.knowledge_root.relative_to(self.root).as_posix(),
                    "knowledge directory does not exist",
                )
            ]

        documents: list[KnowledgeDocument] = []
        issues: list[ValidationIssue] = []
        seen_ids: dict[str, str] = {}
        skill_root = self.knowledge_root / "skills"
        skill_entrypoints: set[Path] = set()
        if skill_root.exists():
            skill_entrypoints = self._collect_skill_packages(skill_root, issues)
        candidates: list[tuple[Path, bool]] = [(path, True) for path in sorted(skill_entrypoints)]
        for path in sorted(self.knowledge_root.rglob("*.md")):
            if not path.is_file():
                continue
            if path in skill_entrypoints:
                continue
            resolved = path.resolve()
            if skill_root.resolve() in resolved.parents:
                continue
            candidates.append((path, False))

        for path, is_skill in candidates:
            document, file_issues = self.parse_skill(path) if is_skill else self.parse(path)
            issues.extend(file_issues)
            if document is None:
                continue
            previous = seen_ids.get(document.id)
            if previous:
                issues.append(
                    ValidationIssue(
                        document.relative_path,
                        f"duplicate id '{document.id}', first defined in {previous}",
                        "id",
                    )
                )
                continue
            seen_ids[document.id] = document.relative_path
            documents.append(document)
        return documents, issues

    def _collect_skill_packages(self, skill_root: Path, issues: list[ValidationIssue]) -> set[Path]:
        """Discover every skill package under ``skills/``.

        A skill package is any directory that directly contains ``SKILL.md``.
        Directories above a package act as free-form category groups, so both
        ``skills/{skill-name}/`` and ``skills/{category}/.../{skill-name}/``
        layouts are accepted. A non-package directory that holds markdown (or
        any file without child packages) is reported as a malformed package.
        """
        entrypoints: set[Path] = set()

        def visit(directory: Path) -> None:
            try:
                children = [
                    entry for entry in sorted(directory.iterdir()) if not entry.name.startswith(".")
                ]
            except OSError:
                return
            directories: list[Path] = []
            direct_markdown: list[Path] = []
            has_entrypoint = False
            for entry in children:
                if entry.is_dir():
                    directories.append(entry)
                elif entry.name == "SKILL.md":
                    has_entrypoint = True
                elif entry.suffix.lower() == ".md":
                    direct_markdown.append(entry)
            if has_entrypoint:
                entrypoints.add(directory / "SKILL.md")
                return
            if direct_markdown:
                if directory == skill_root:
                    for markdown in direct_markdown:
                        issues.append(
                            ValidationIssue(
                                markdown.relative_to(self.root).as_posix(),
                                "skills must use the skills/{skill-name}/SKILL.md package structure",
                            )
                        )
                else:
                    issues.append(
                        ValidationIssue(
                            directory.relative_to(self.root).as_posix(),
                            "skill directory must contain SKILL.md",
                        )
                    )
            elif not directories and children:
                issues.append(
                    ValidationIssue(
                        directory.relative_to(self.root).as_posix(),
                        "skill directory must contain SKILL.md",
                    )
                )
            for child in directories:
                visit(child)

        visit(skill_root)
        return entrypoints

    def _skill_category_tags(self, package_root: Path) -> tuple[str, ...]:
        """Return category directory names above the package leaf, outermost first."""
        skill_root = (self.knowledge_root / "skills").resolve()
        try:
            relative = package_root.resolve().relative_to(skill_root)
        except ValueError:
            return ()
        parts = relative.parts
        return tuple(parts[:-1]) if len(parts) > 1 else ()

    def parse_skill(self, path: Path) -> tuple[KnowledgeDocument | None, list[ValidationIssue]]:
        relative = path.resolve().relative_to(self.root).as_posix()
        metadata, content, issues = self._read_front_matter(path)
        if metadata is None:
            return None, issues

        def required_string(name: str) -> str:
            value = metadata.get(name)
            if not isinstance(value, str) or not value.strip():
                issues.append(ValidationIssue(relative, "is required and must be a non-empty string", name))
                return ""
            return value.strip()

        folder_name = path.parent.name
        raw_name = metadata.get("name")
        if raw_name is None:
            name = folder_name
        elif not isinstance(raw_name, str) or not raw_name.strip():
            issues.append(ValidationIssue(relative, "must be a non-empty string when present", "name"))
            name = ""
        else:
            name = raw_name.strip()
        if name and not _ID_RE.fullmatch(name):
            issues.append(ValidationIssue(relative, "contains unsupported characters", "name"))
        if name and name != folder_name:
            issues.append(
                ValidationIssue(relative, f"must match the skill directory name '{folder_name}'", "name")
            )

        description = required_string("description")
        description_zh = required_string("description_zh")
        description_en = required_string("description_en")
        version = required_string("version")
        author = required_string("author")
        display_name = metadata.get("display_name")
        if display_name is not None and (not isinstance(display_name, str) or not display_name.strip()):
            issues.append(ValidationIssue(relative, "must be a non-empty string when present", "display_name"))
        allowed_tools = metadata.get("allowed-tools")
        if allowed_tools is not None and not isinstance(allowed_tools, str):
            issues.append(ValidationIssue(relative, "must be a comma-separated string", "allowed-tools"))
        for boolean_field in ("disable-model-invocation", "user-invocable"):
            value = metadata.get(boolean_field)
            if value is not None and not isinstance(value, bool):
                issues.append(ValidationIssue(relative, "must be true or false", boolean_field))
        if not content:
            issues.append(ValidationIssue(relative, "Markdown body must not be empty", "content"))

        tags = list(_string_list(metadata.get("tags"), "tags", relative, issues))
        category = metadata.get("category")
        if category is not None:
            if not isinstance(category, str) or not category.strip():
                issues.append(ValidationIssue(relative, "must be a non-empty string when present", "category"))
            elif category.strip() not in tags:
                tags.insert(0, category.strip())
        category_tags = [tag for tag in self._skill_category_tags(path.parent) if tag not in tags]
        tags = category_tags + tags
        keywords = _string_list(metadata.get("keywords"), "keywords", relative, issues)
        resources = self._skill_resources(path.parent)
        resource_paths = {resource.path for resource in resources}
        referenced_paths = re.findall(
            r"@((?:references|scripts|templates)/[^\s)`'\"，。]+)", content
        )
        for raw_referenced_path in referenced_paths:
            referenced_path = raw_referenced_path.rstrip(".,;:!?")
            if referenced_path not in resource_paths:
                issues.append(
                    ValidationIssue(
                        relative,
                        f"referenced skill resource does not exist: {referenced_path}",
                        "content",
                    )
                )
        if issues:
            return None, issues

        stat = path.stat()
        safe_metadata = {str(key): _json_safe(value) for key, value in metadata.items()}
        safe_metadata.update(
            {
                "name": name,
                "description_zh": description_zh,
                "description_en": description_en,
                "version": version,
                "author": author,
            }
        )
        return (
            KnowledgeDocument(
                id=name,
                type="skill",
                title=(display_name.strip() if isinstance(display_name, str) else name),
                description=description,
                tags=tuple(tags),
                keywords=keywords,
                content=content,
                path=path.resolve(),
                relative_path=relative,
                metadata=safe_metadata,
                resources=resources,
                mtime_ns=stat.st_mtime_ns,
            ),
            [],
        )

    def _skill_resources(self, package_root: Path) -> tuple[KnowledgeResource, ...]:
        resources: list[KnowledgeResource] = []
        for kind in ("references", "scripts", "templates"):
            resource_root = package_root / kind
            if not resource_root.exists():
                continue
            for path in sorted(resource_root.rglob("*")):
                if not path.is_file():
                    continue
                relative = path.relative_to(package_root).as_posix()
                media_type, _ = mimetypes.guess_type(path.name)
                try:
                    size = path.stat().st_size
                except OSError:
                    continue
                resources.append(
                    KnowledgeResource(path=relative, kind=kind, size=size, media_type=media_type)
                )
        return tuple(resources)

    def parse(self, path: Path) -> tuple[KnowledgeDocument | None, list[ValidationIssue]]:
        relative = path.resolve().relative_to(self.root).as_posix()
        metadata, content, issues = self._read_front_matter(path)
        if metadata is None:
            return None, issues

        def required_string(name: str) -> str:
            value = metadata.get(name)
            if not isinstance(value, str) or not value.strip():
                issues.append(ValidationIssue(relative, "is required and must be a non-empty string", name))
                return ""
            return value.strip()

        document_id = required_string("id")
        kind = required_string("type")
        title = required_string("title")
        description = required_string("description")
        if document_id and not _ID_RE.fullmatch(document_id):
            issues.append(
                ValidationIssue(
                    relative,
                    "must start with an alphanumeric character and contain only letters, numbers, '.', '_', '/', '-'",
                    "id",
                )
            )
        if kind and kind not in KNOWLEDGE_TYPES:
            issues.append(
                ValidationIssue(relative, f"must be one of: {', '.join(sorted(KNOWLEDGE_TYPES))}", "type")
            )

        tags = _string_list(metadata.get("tags"), "tags", relative, issues)
        keywords = _string_list(metadata.get("keywords"), "keywords", relative, issues)
        if not content:
            issues.append(ValidationIssue(relative, "Markdown body must not be empty", "content"))
        if issues:
            return None, issues

        stat = path.stat()
        reserved = {"id", "type", "title", "description", "tags", "keywords"}
        extra = {str(k): _json_safe(v) for k, v in metadata.items() if k not in reserved}
        return (
            KnowledgeDocument(
                id=document_id,
                type=kind,  # type: ignore[arg-type]
                title=title,
                description=description,
                tags=tags,
                keywords=keywords,
                content=content,
                path=path.resolve(),
                relative_path=relative,
                metadata=extra,
                mtime_ns=stat.st_mtime_ns,
            ),
            [],
        )

    def _read_front_matter(
        self, path: Path
    ) -> tuple[dict[str, Any] | None, str, list[ValidationIssue]]:
        relative = path.resolve().relative_to(self.root).as_posix()
        issues: list[ValidationIssue] = []
        try:
            raw = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as exc:
            return None, "", [ValidationIssue(relative, f"cannot read UTF-8 file: {exc}")]

        match = _FRONT_MATTER_RE.match(raw)
        if not match:
            return None, "", [ValidationIssue(relative, "missing or malformed YAML front matter")]
        try:
            metadata = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError as exc:
            return None, "", [ValidationIssue(relative, f"invalid YAML: {exc}")]
        if not isinstance(metadata, dict):
            return None, "", [ValidationIssue(relative, "front matter must be a YAML mapping")]
        content = raw[match.end() :].strip()
        return metadata, content, issues
