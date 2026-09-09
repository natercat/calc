import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field

from fastapi import HTTPException

from . import config
from .models import SkillLevel
from .topics.registry import ALL_SKILLS


@dataclass
class ProblemAttempt:
    topic: str
    problem: dict
    skill: str
    attempts: int = 0
    solved: bool = False


@dataclass
class SessionState:
    profile: dict = field(default_factory=lambda: {skill: SkillLevel.UNKNOWN for skill in ALL_SKILLS})
    history: list = field(default_factory=list)
    active_problems: dict = field(default_factory=dict)
    last_active: float = field(default_factory=time.time)


_sessions: dict[str, SessionState] = {}

# FastAPI runs each sync route handler in a thread pool, so two requests
# against the SAME session_id (a double-click before the UI disables the
# button, a slow Claude call overlapping a fast follow-up request, etc.) can
# genuinely run concurrently. A per-session lock serializes all work against
# one session's mutable state without blocking unrelated sessions. It is NOT
# reentrant -- nothing that runs while holding it should try to acquire it
# again for the same session_id.
_session_locks: dict[str, threading.Lock] = {}
_locks_guard = threading.Lock()


def _get_lock(session_id: str) -> threading.Lock:
    with _locks_guard:
        lock = _session_locks.get(session_id)
        if lock is None:
            lock = threading.Lock()
            _session_locks[session_id] = lock
        return lock


@contextmanager
def session_lock(session_id: str):
    """Serialize all reads/writes against one session's state. Route
    handlers should wrap their entire body (after validating the session
    exists) in `with session_lock(session_id):` if they mutate session
    state or read it in a way that assumes it won't change mid-request."""
    with _get_lock(session_id):
        yield


# There's no accounts system and no client identity beyond a session_id, so
# an abandoned browser tab's session (and its lock) would otherwise sit in
# memory forever. Rather than run a background thread, expiry is swept
# lazily: any call to create_session/get_session may trigger a sweep, but at
# most once per _SWEEP_INTERVAL_SECONDS of wall-clock time, so the O(sessions)
# scan doesn't run on every single request.
_SWEEP_INTERVAL_SECONDS = 300
_last_sweep = 0.0


def _maybe_sweep(now: float) -> None:
    global _last_sweep
    if now - _last_sweep < _SWEEP_INTERVAL_SECONDS:
        return
    _last_sweep = now
    purge_expired_sessions(now)


def purge_expired_sessions(now: float | None = None) -> int:
    """Evict sessions inactive for longer than SESSION_TTL_SECONDS. Returns
    the number purged. A session currently mid-request (its lock is held) is
    left for the next sweep rather than evicted out from under it."""
    now = now if now is not None else time.time()
    expired_ids = [
        sid for sid, session in list(_sessions.items()) if now - session.last_active > config.SESSION_TTL_SECONDS
    ]

    purged = 0
    for session_id in expired_ids:
        with _locks_guard:
            lock = _session_locks.get(session_id)
            if lock is not None:
                if not lock.acquire(blocking=False):
                    continue
                lock.release()
                del _session_locks[session_id]
        _sessions.pop(session_id, None)
        purged += 1
    return purged


def create_session() -> str:
    _maybe_sweep(time.time())
    session_id = str(uuid.uuid4())
    _sessions[session_id] = SessionState()
    return session_id


def get_session(session_id: str) -> SessionState:
    now = time.time()
    _maybe_sweep(now)
    session = _sessions.get(session_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Unknown session_id. Create a session first via POST /api/session.",
        )
    session.last_active = now
    return session


def apply_profile_updates(session: SessionState, updates: dict) -> None:
    valid_levels = {level.value for level in SkillLevel}
    for skill, level in (updates or {}).items():
        if skill in session.profile and level in valid_levels:
            session.profile[skill] = SkillLevel(level)


def add_history(session: SessionState, role: str, content: str, max_turns: int = 20) -> None:
    session.history.append({"role": role, "content": content})
    if len(session.history) > max_turns:
        session.history[:] = session.history[-max_turns:]
