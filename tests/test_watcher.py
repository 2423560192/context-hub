from pathlib import Path
from threading import Event

from skillhub.watcher import KnowledgeWatcher


def test_watcher_notifies_on_markdown_change(tmp_path: Path) -> None:
    event = Event()
    watcher = KnowledgeWatcher(tmp_path, event.set, debounce_seconds=0.05)
    watcher.start()
    try:
        (tmp_path / "changed.py").write_text("print('changed')", encoding="utf-8")
        assert event.wait(timeout=3)
    finally:
        watcher.stop()
