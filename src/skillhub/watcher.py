from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


class _MarkdownEventHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[], None], debounce_seconds: float) -> None:
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self._lock = threading.Lock()
        self._timer: threading.Timer | None = None

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        with self._lock:
            if self._timer:
                self._timer.cancel()
            self._timer = threading.Timer(self.debounce_seconds, self.callback)
            self._timer.daemon = True
            self._timer.start()

    def close(self) -> None:
        with self._lock:
            if self._timer:
                self._timer.cancel()
                self._timer = None


class KnowledgeWatcher:
    def __init__(self, path: Path, callback: Callable[[], None], debounce_seconds: float = 0.15) -> None:
        self.path = path
        self._handler = _MarkdownEventHandler(callback, debounce_seconds)
        self._observer = Observer()
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        self.path.mkdir(parents=True, exist_ok=True)
        self._observer.schedule(self._handler, str(self.path), recursive=True)
        self._observer.start()
        self._started = True

    def stop(self) -> None:
        if not self._started:
            return
        self._handler.close()
        self._observer.stop()
        self._observer.join(timeout=3)
        self._started = False
