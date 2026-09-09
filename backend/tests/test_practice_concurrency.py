import threading
import time

import pytest
from fastapi import HTTPException

from app.models import StartPracticeRequest, StepRequest
from app.routers import practice as practice_router
from app.session_store import create_session
from app.topics import derivatives as derivatives_topic


@pytest.fixture(autouse=True)
def fake_claude_feedback(monkeypatch):
    # These tests are about request-level concurrency, not Claude's output --
    # stub it out so they run fast and need no API key.
    monkeypatch.setattr(
        practice_router.claude_client,
        "practice_feedback",
        lambda **kwargs: {"reply": "ok", "profile_updates": {}},
    )


@pytest.fixture
def slow_check_answer(monkeypatch):
    # Widens the race window inside submit_step (between reading
    # attempt.solved and the point where a correct answer sets it) so a race
    # is deterministic rather than a matter of unlucky thread scheduling --
    # this stands in for the real, much larger window a live Claude API call
    # creates in production.
    original = derivatives_topic.check_answer

    def delayed(student_text, problem):
        time.sleep(0.02)
        return original(student_text, problem)

    monkeypatch.setattr(derivatives_topic, "check_answer", delayed)


def _start_problem(session_id):
    return practice_router.start_practice(StartPracticeRequest(session_id=session_id, topic="derivatives"))


def test_concurrent_wrong_submissions_do_not_lose_attempt_increments(slow_check_answer):
    session_id = create_session()
    problem = _start_problem(session_id)

    results = []
    results_lock = threading.Lock()

    def submit():
        req = StepRequest(session_id=session_id, problem_id=problem.problem_id, student_answer="99")
        result = practice_router.submit_step(req)
        with results_lock:
            results.append(result.attempt_number)

    threads = [threading.Thread(target=submit) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Without serialization, two threads could both read attempts=N and both
    # write back N+1, producing duplicate attempt numbers and an undercount.
    assert sorted(results) == list(range(1, 7))


def test_concurrent_correct_submissions_only_one_solves_it(slow_check_answer):
    session_id = create_session()
    problem = _start_problem(session_id)  # "x**2 + 3*x" -> derivative "2*x + 3"

    outcomes = []
    outcomes_lock = threading.Lock()

    def submit():
        req = StepRequest(session_id=session_id, problem_id=problem.problem_id, student_answer="2*x+3")
        try:
            result = practice_router.submit_step(req)
            with outcomes_lock:
                outcomes.append(("ok", result))
        except HTTPException as exc:
            with outcomes_lock:
                outcomes.append(("blocked", exc))

    threads = [threading.Thread(target=submit) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    ok = [result for kind, result in outcomes if kind == "ok"]
    blocked = [exc for kind, exc in outcomes if kind == "blocked"]

    # Without the lock, multiple threads could all see attempt.solved==False
    # before any of them set it True, each triggering its own "correct!"
    # feedback call and profile update -- wasted API calls and a student
    # seeing the same congratulation message repeated.
    assert len(ok) == 1
    assert ok[0].correct is True
    assert ok[0].solved is True
    assert len(blocked) == 4
    assert all(exc.status_code == 400 for exc in blocked)
