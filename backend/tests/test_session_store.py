import pytest
from fastapi import HTTPException

from app.models import SkillLevel
from app.session_store import (
    ProblemAttempt,
    add_history,
    apply_profile_updates,
    create_session,
    get_session,
)
from app.topics.derivatives import SKILLS


class TestCreateAndGetSession:
    def test_create_session_returns_unique_ids(self):
        a = create_session()
        b = create_session()
        assert a != b

    def test_new_session_has_default_profile(self):
        session_id = create_session()
        session = get_session(session_id)
        assert set(session.profile.keys()) == set(SKILLS)
        assert all(level == SkillLevel.UNKNOWN for level in session.profile.values())

    def test_new_session_has_empty_history_and_problems(self):
        session_id = create_session()
        session = get_session(session_id)
        assert session.history == []
        assert session.active_problems == {}

    def test_unknown_session_id_raises_404(self):
        with pytest.raises(HTTPException) as exc_info:
            get_session("does-not-exist")
        assert exc_info.value.status_code == 404

    def test_sessions_are_independent(self):
        a = get_session(create_session())
        b = get_session(create_session())
        a.profile["power_rule"] = SkillLevel.STRONG
        assert b.profile["power_rule"] == SkillLevel.UNKNOWN


class TestApplyProfileUpdates:
    def test_valid_update_applied(self):
        session = get_session(create_session())
        apply_profile_updates(session, {"power_rule": "strong"})
        assert session.profile["power_rule"] == SkillLevel.STRONG

    def test_unknown_skill_name_ignored(self):
        session = get_session(create_session())
        before = dict(session.profile)
        apply_profile_updates(session, {"not_a_real_skill": "strong"})
        assert session.profile == before

    def test_invalid_level_value_ignored(self):
        session = get_session(create_session())
        before = session.profile["power_rule"]
        apply_profile_updates(session, {"power_rule": "expert"})
        assert session.profile["power_rule"] == before

    def test_empty_updates_is_a_noop(self):
        session = get_session(create_session())
        before = dict(session.profile)
        apply_profile_updates(session, {})
        assert session.profile == before

    def test_none_updates_is_a_noop(self):
        session = get_session(create_session())
        before = dict(session.profile)
        apply_profile_updates(session, None)
        assert session.profile == before


class TestAddHistory:
    def test_appends_role_and_content(self):
        session = get_session(create_session())
        add_history(session, "user", "hello")
        assert session.history == [{"role": "user", "content": "hello"}]

    def test_trims_to_max_turns_keeping_most_recent(self):
        session = get_session(create_session())
        for i in range(5):
            add_history(session, "user", f"turn-{i}", max_turns=3)
        assert len(session.history) == 3
        assert [h["content"] for h in session.history] == ["turn-2", "turn-3", "turn-4"]


class TestProblemAttempt:
    def test_defaults(self):
        attempt = ProblemAttempt(expression="x**2", skill="power_rule")
        assert attempt.attempts == 0
        assert attempt.solved is False
