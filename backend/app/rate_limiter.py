import threading
import time
from collections import deque
from typing import Optional

from fastapi import HTTPException

from . import config


class RateLimiter:
    """A simple in-memory sliding-window rate limiter, keyed by an arbitrary
    string (a session id, a client IP, ...).

    Not distributed -- state lives in this process only, so it resets on
    restart and doesn't coordinate across multiple worker processes. Fine
    for this app's single-process deployment; a multi-instance deployment
    would need a shared store (e.g. Redis) instead.
    """

    def __init__(self, max_requests: int, window_seconds: float, purge_interval_seconds: float = 300):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._purge_interval = purge_interval_seconds
        self._hits: dict[str, deque] = {}
        self._guard = threading.Lock()
        self._last_purge = 0.0

    def check(self, key: str, now: Optional[float] = None) -> None:
        """Raise HTTPException(429) if `key` has already used up its
        allowance within the current window; otherwise record this call."""
        now = now if now is not None else time.time()
        with self._guard:
            self._maybe_purge_locked(now)

            hits = self._hits.setdefault(key, deque())
            while hits and now - hits[0] > self.window_seconds:
                hits.popleft()

            if len(hits) >= self.max_requests:
                retry_after = max(1, int(self.window_seconds - (now - hits[0])) + 1)
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many requests. Try again in about {retry_after} seconds.",
                    headers={"Retry-After": str(retry_after)},
                )

            hits.append(now)

    def _maybe_purge_locked(self, now: float) -> None:
        # Caller already holds self._guard. Bounds memory growth the same
        # way session expiry does: a key nobody's used in a full window is
        # dropped instead of sitting in the dict forever.
        if now - self._last_purge < self._purge_interval:
            return
        self._last_purge = now
        idle_keys = [key for key, hits in self._hits.items() if not hits or now - hits[-1] > self.window_seconds]
        for key in idle_keys:
            del self._hits[key]


# Caps how often one session can trigger a Claude API call (lesson intro,
# chat, practice feedback).
claude_call_limiter = RateLimiter(max_requests=config.CLAUDE_CALLS_PER_MINUTE, window_seconds=60)

# Caps how often one client IP can create new sessions -- otherwise the
# limiter above is trivially bypassed by just making a fresh session.
session_creation_limiter = RateLimiter(max_requests=config.SESSION_CREATES_PER_MINUTE_PER_IP, window_seconds=60)
