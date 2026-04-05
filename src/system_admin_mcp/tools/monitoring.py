import json
import logging
import os
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger("system_admin_mcp.monitoring")

@dataclass
class WatchEvent:
    timestamp: float
    event_type: str
    src_path: str
    is_directory: bool
    dest_path: str | None = None

class BufferedEventHandler(FileSystemEventHandler):
    def __init__(self, manager: "FileWatcherManager", path: str):
        self.manager = manager
        self.path = path

    def on_any_event(self, event):
        watch_event = WatchEvent(
            timestamp=time.time(),
            event_type=event.event_type,
            src_path=event.src_path,
            is_directory=event.is_directory,
            dest_path=getattr(event, "dest_path", None)
        )
        self.manager.add_event(self.path, watch_event)

class FileWatcherManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.observer = Observer()
        self.watches: dict[str, BufferedEventHandler] = {}
        self.events: dict[str, deque] = {}
        self.state_file = Path(os.environ.get("USERPROFILE", ".")) / ".gemini" / "antigravity" / "system-admin-mcp" / "watches.json"
        self._initialized = True
        self.observer.start()
        self._load_state()

    def _load_state(self):
        """Restore active watches from disk."""
        if not self.state_file.exists():
            return

        try:
            with open(self.state_file) as f:
                data = json.load(f)
                for path in data.get("active_watches", []):
                    if os.path.exists(path):
                        self.start_watch(path, persist=False)
        except Exception as e:
            logger.error(f"Failed to load watcher state: {e}")

    def _save_state(self):
        """Persist active watches to disk."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, "w") as f:
                json.dump({"active_watches": list(self.watches.keys())}, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save watcher state: {e}")

    def start_watch(self, path: str, persist: bool = True) -> bool:
        path = os.path.abspath(path)
        if path in self.watches:
            return True

        if not os.path.exists(path):
            raise FileNotFoundError(f"Path not found: {path}")

        handler = BufferedEventHandler(self, path)
        self.observer.schedule(handler, path, recursive=True)
        self.watches[path] = handler
        self.events[path] = deque(maxlen=100) # Keep last 100 events

        if persist:
            self._save_state()
        return True

    def stop_watch(self, path: str) -> bool:
        path = os.path.abspath(path)
        if path not in self.watches:
            return False

        # Watchdog doesn't support easy unscheduling by path efficiently
        # without searching emitters, so we usually restart the observer or
        # just handle it in the handler if we want to be surgical.
        # For simplicity in this SOTA implementation, we'll unschedule the specific handler.
        for search_path, _handler in list(self.watches.items()):
            if search_path == path:
                self.observer.unschedule_all() # Brute force for now, and reschedule others
                del self.watches[path]
                # Reschedule remaining
                for p, h in self.watches.items():
                    self.observer.schedule(h, p, recursive=True)
                break

        self._save_state()
        return True

    def add_event(self, watch_path: str, event: WatchEvent):
        if watch_path in self.events:
            self.events[watch_path].append(event)
            logger.info(f"Event in {watch_path}: {event.event_type} - {event.src_path}")

    def get_events(self, path: str | None = None) -> list[dict]:
        if path:
            path = os.path.abspath(path)
            events = list(self.events.get(path, []))
        else:
            # Flatten all events
            events = []
            for e_list in self.events.values():
                events.extend(list(e_list))
            events.sort(key=lambda x: x.timestamp, reverse=True)

        return [asdict(e) for e in events]

    def shutdown(self):
        self.observer.stop()
        self.observer.join()

# Global manager instance
watcher_manager = FileWatcherManager()
