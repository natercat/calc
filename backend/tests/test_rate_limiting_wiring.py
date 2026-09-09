"""Confirms each route actually calls the shared rate limiter (as opposed to
RateLimiter's own logic, covered exhaustively in test_rate_limiter.py). Each
test uses a fresh session/key so it can't be polluted by other tests sharing
the same module-level limiter singleton, and lowers max_requests on the
singleton directly (it's a real mutable attribute) rather than trying to
recreate one from config at import time.
"""

import pytest
from fastapi import HTTPException, Request

from app.models import ChatRequest, StartPracticeRequest, StepRequest
from app.rate_limiter import claude_call_limiter, session_creation_limiter
from app.routers import chat as chat_router
from app.routers import practice as practice_router
from app.routers import session as session_router
from app.session_store import create_session


class _FakeClient:
    def __init__(self, host):
        self.host = host


class _FakeRequest:
    def __init__(self, host):
        self.client = _FakeClient(host)


@pytest.fixture(autouse=True)
def fake_claude(monkeypatch):
    monkeypatch.setattr(chat_router.claude_client, "chat_reply", lambda *a, **k: {"reply": "ok"})
    monkeypatch.setattr(practice_router.claude_client, "practice_feedback", lambda **k: {"reply": "ok"})


def test_session_creation_is_rate_limited_per_ip(monkeypatch):
    monkeypatch.setattr(session_creation_limiter, "max_requests", 2)
    ip = "203.0.113.5"  # unique to this test, isolated from other tests

    session_router.new_session(_FakeRequest(ip))
    session_router.new_session(_FakeRequest(ip))
    with pytest.raises(HTTPException) as exc_info:
        session_router.new_session(_FakeRequest(ip))
    assert exc_info.value.status_code == 429


def test_session_creation_limit_is_per_ip_not_global(monkeypatch):
    monkeypatch.setattr(session_creation_limiter, "max_requests", 1)

    session_router.new_session(_FakeRequest("203.0.113.10"))
    # A different IP should not be blocked by the first one's usage.
    session_router.new_session(_FakeRequest("203.0.113.11"))


def test_chat_is_rate_limited_per_session(monkeypatch):
    monkeypatch.setattr(claude_call_limiter, "max_requests", 2)
    session_id = create_session()

    chat_router.chat(ChatRequest(session_id=session_id, message="hi"))
    chat_router.chat(ChatRequest(session_id=session_id, message="hi again"))
    with pytest.raises(HTTPException) as exc_info:
        chat_router.chat(ChatRequest(session_id=session_id, message="one more"))
    assert exc_info.value.status_code == 429


def test_practice_step_is_rate_limited_per_session(monkeypatch):
    monkeypatch.setattr(claude_call_limiter, "max_requests", 1)
    session_id = create_session()
    problem = practice_router.start_practice(StartPracticeRequest(session_id=session_id, topic="derivatives"))

    practice_router.submit_step(StepRequest(session_id=session_id, problem_id=problem.problem_id, student_answer="wrong"))
    with pytest.raises(HTTPException) as exc_info:
        practice_router.submit_step(
            StepRequest(session_id=session_id, problem_id=problem.problem_id, student_answer="also wrong")
        )
    assert exc_info.value.status_code == 429


def test_practice_start_is_not_rate_limited_by_the_claude_limiter(monkeypatch):
    # /practice/start never calls Claude -- it shouldn't burn Claude-call
    # allowance or be blocked by it.
    monkeypatch.setattr(claude_call_limiter, "max_requests", 0)
    session_id = create_session()

    practice_router.start_practice(StartPracticeRequest(session_id=session_id, topic="derivatives"))
