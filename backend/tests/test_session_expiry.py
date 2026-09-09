import threading

from fastapi import HTTPException

from app import config
from app.session_store import (
    _get_lock,
    _sessions,
    create_session,
    get_session,
    purge_expired_sessions,
)


def _expire(session_id, seconds_ago):
    _sessions[session_id].last_active -= seconds_ago


class TestPurgeExpiredSessions:
    def test_inactive_session_past_ttl_is_purged(self):
        session_id = create_session()
        _expire(session_id, config.SESSION_TTL_SECONDS + 1)

        purged = purge_expired_sessions()

        assert purged == 1
        assert session_id not in _sessions

    def test_session_within_ttl_survives(self):
        session_id = create_session()
        _expire(session_id, config.SESSION_TTL_SECONDS - 10)

        purged = purge_expired_sessions()

        assert purged == 0
        assert session_id in _sessions

    def test_expired_session_lock_is_also_removed(self):
        session_id = create_session()
        lock_before = _get_lock(session_id)
        _expire(session_id, config.SESSION_TTL_SECONDS + 1)

        purge_expired_sessions()

        # A fresh lock for the same (now nonexistent) id proves the old one
        # was cleaned up rather than leaking forever.
        assert _get_lock(session_id) is not lock_before

    def test_get_session_after_expiry_raises_404(self):
        session_id = create_session()
        _expire(session_id, config.SESSION_TTL_SECONDS + 1)
        purge_expired_sessions()

        try:
            get_session(session_id)
            assert False, "expected HTTPException"
        except HTTPException as exc:
            assert exc.status_code == 404

    def test_only_expired_sessions_are_purged_not_active_ones(self):
        stale = create_session()
        fresh = create_session()
        _expire(stale, config.SESSION_TTL_SECONDS + 1)

        purge_expired_sessions()

        assert stale not in _sessions
        assert fresh in _sessions

    def test_a_session_actively_held_by_its_lock_is_not_evicted(self):
        # Simulates a request that is mid-flight (holding the session's
        # lock) at the exact moment a sweep decides the session looks
        # expired -- the sweep must not rip state out from under it.
        session_id = create_session()
        _expire(session_id, config.SESSION_TTL_SECONDS + 1)
        lock = _get_lock(session_id)

        lock.acquire()
        try:
            purged = purge_expired_sessions()
            assert purged == 0
            assert session_id in _sessions
        finally:
            lock.release()

        # Once released, a later sweep can evict it normally.
        assert purge_expired_sessions() == 1
        assert session_id not in _sessions


class TestSweepThrottling:
    def test_sweep_runs_at_most_once_per_interval(self, monkeypatch):
        import app.session_store as session_store

        monkeypatch.setattr(session_store, "_last_sweep", 0.0)
        calls = []
        monkeypatch.setattr(session_store, "purge_expired_sessions", lambda now=None: calls.append(now))

        interval = session_store._SWEEP_INTERVAL_SECONDS
        session_store._maybe_sweep(interval + 1)  # first sweep ever (now - 0.0 >= interval) -> runs
        session_store._maybe_sweep(interval + 1 + interval - 1)  # too soon since last sweep -> skipped
        session_store._maybe_sweep(interval + 1 + interval + 1)  # interval elapsed again -> runs

        assert len(calls) == 2


class TestGetSessionTouchesActivity:
    def test_get_session_resets_the_inactivity_clock(self):
        session_id = create_session()
        _expire(session_id, config.SESSION_TTL_SECONDS - 10)

        get_session(session_id)  # should bump last_active back to "now"

        # If get_session hadn't refreshed it, this would now be expired.
        _expire(session_id, config.SESSION_TTL_SECONDS - 10)
        assert purge_expired_sessions() == 0
