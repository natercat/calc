import threading
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field

from fastapi import HTTPException

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


def create_session() -> str:
    session_id = str(uuid.uuid4())
    _sessions[session_id] = SessionState()
    return session_id


def get_session(session_id: str) -> SessionState:
    session = _sessions.get(session_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Unknown session_id. Create a session first via POST /api/session.",
        )
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
