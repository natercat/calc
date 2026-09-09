import pytest
from fastapi import HTTPException

from app.rate_limiter import RateLimiter


class TestRateLimiterBasics:
    def test_allows_up_to_the_limit(self):
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            limiter.check("key", now=1000.0)  # should not raise

    def test_rejects_the_request_over_the_limit(self):
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            limiter.check("key", now=1000.0)

        with pytest.raises(HTTPException) as exc_info:
            limiter.check("key", now=1000.0)
        assert exc_info.value.status_code == 429

    def test_response_includes_retry_after_header(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        limiter.check("key", now=1000.0)

        with pytest.raises(HTTPException) as exc_info:
            limiter.check("key", now=1000.0)
        assert "Retry-After" in exc_info.value.headers
        assert int(exc_info.value.headers["Retry-After"]) > 0

    def test_allowance_frees_up_as_the_window_slides(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        limiter.check("key", now=1000.0)
        limiter.check("key", now=1000.0)

        with pytest.raises(HTTPException):
            limiter.check("key", now=1010.0)  # still within the window

        limiter.check("key", now=1061.0)  # the first hit has aged out


class TestRateLimiterKeyIsolation:
    def test_different_keys_have_independent_allowances(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        limiter.check("session-a", now=1000.0)
        limiter.check("session-b", now=1000.0)  # should not raise -- separate key

        with pytest.raises(HTTPException):
            limiter.check("session-a", now=1000.0)


class TestRateLimiterPurging:
    def test_idle_keys_are_dropped_after_a_purge_interval(self):
        limiter = RateLimiter(max_requests=5, window_seconds=60, purge_interval_seconds=100)
        limiter.check("key", now=1000.0)
        assert "key" in limiter._hits

        # Long past the window, and a purge interval has elapsed since the
        # limiter's internal _last_purge (0.0) baseline.
        limiter.check("other-key", now=1200.0)

        assert "key" not in limiter._hits

    def test_purge_does_not_drop_keys_still_within_their_window(self):
        limiter = RateLimiter(max_requests=5, window_seconds=120, purge_interval_seconds=10)
        limiter.check("key", now=1000.0)

        limiter.check("other-key", now=1050.0)  # triggers a purge sweep

        assert "key" in limiter._hits  # still within its 120s window
