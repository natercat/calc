import uuid
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
