from pathlib import Path

from skillhub.cli import main


def test_cli_validate(knowledge_repo: Path, capsys) -> None:
    exit_code = main(["--repo", str(knowledge_repo), "validate"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert '"valid": true' in output


def test_cli_search(knowledge_repo: Path, capsys) -> None:
    exit_code = main(["--repo", str(knowledge_repo), "search", "security"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert '"id": "review"' in output
