from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def knowledge_repo(tmp_path: Path) -> Path:
    skill = tmp_path / "knowledge" / "skills" / "review"
    (skill / "references").mkdir(parents=True)
    (skill / "templates").mkdir()
    (skill / "SKILL.md").write_text(
        """---
name: review
display_name: 安全 Code Review
display_name_en: Secure Code Review
description: 检查安全漏洞和回归风险，在需要安全审查、security review 时触发。
description_zh: 检查安全漏洞和回归风险。
description_en: Review code for security vulnerabilities and regressions.
category: software-development
tags: [安全, review]
keywords: [security, regression]
version: 1.0.0
author: Test Author
---
# Review

Check authentication, authorization, input validation, and regression tests. See @references/checklist.md.
""",
        encoding="utf-8",
    )
    (skill / "references" / "checklist.md").write_text(
        "# Checklist\n\nVerify access control.", encoding="utf-8"
    )
    (skill / "templates" / "report.md").write_text(
        "# Review report\n", encoding="utf-8"
    )
    return tmp_path
