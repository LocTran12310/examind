"""Tiny in-process sliding-window limiter (single api process per host is the deployment model)."""
from collections import defaultdict, deque
import threading
import time


class SlidingWindow:
    def __init__(self, limit: int, seconds: float = 60.0):
        self.limit, self.seconds = limit, seconds
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str) -> bool:
        """Record a hit; False when the key is over the limit."""
        t = time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and t - q[0] > self.seconds:
                q.popleft()
            if len(q) >= self.limit:
                return False
            q.append(t)
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()
