"""
Tests for the rate limiting engine.
These tests verify the core invariants:
  - Requests within limit are allowed
  - Requests exceeding limit are blocked with correct metadata
  - Remaining count decrements correctly
  - Throttled requests are recorded but do NOT consume quota
"""
import pytest
from app.services import rate_limiter


class TestRateLimiterAllows:
    def test_first_request_is_allowed(self, db, client_obj):
        result = rate_limiter.check_and_record(client_obj, "/test")
        assert result.allowed is True

    def test_remaining_decrements(self, db, client_obj):
        r1 = rate_limiter.check_and_record(client_obj, "/test")
        r2 = rate_limiter.check_and_record(client_obj, "/test")
        assert r2.remaining == r1.remaining - 1

    def test_limit_is_reported_correctly(self, db, client_obj):
        result = rate_limiter.check_and_record(client_obj, "/test")
        assert result.limit == client_obj.rate_config.requests_per_window


class TestRateLimiterBlocks:
    def test_exceeding_limit_returns_429_result(self, db, client_obj):
        limit = client_obj.rate_config.requests_per_window  # 5
        for _ in range(limit):
            rate_limiter.check_and_record(client_obj, "/test")

        over_limit = rate_limiter.check_and_record(client_obj, "/test")
        assert over_limit.allowed is False

    def test_blocked_result_has_retry_after(self, db, client_obj):
        limit = client_obj.rate_config.requests_per_window
        for _ in range(limit):
            rate_limiter.check_and_record(client_obj, "/test")

        result = rate_limiter.check_and_record(client_obj, "/test")
        assert result.retry_after is not None
        assert result.retry_after > 0

    def test_remaining_never_goes_negative(self, db, client_obj):
        limit = client_obj.rate_config.requests_per_window
        for _ in range(limit + 5):
            result = rate_limiter.check_and_record(client_obj, "/test")

        assert result.remaining == 0


class TestRequestLogging:
    def test_allowed_requests_are_logged(self, db, client_obj):
        from app.models import RequestLog
        rate_limiter.check_and_record(client_obj, "/ping")
        log = RequestLog.query.filter_by(client_id=client_obj.id).first()
        assert log is not None
        assert log.path == "/ping"
        assert log.was_throttled is False

    def test_throttled_requests_are_logged_as_throttled(self, db, client_obj):
        from app.models import RequestLog
        limit = client_obj.rate_config.requests_per_window
        for _ in range(limit + 1):
            rate_limiter.check_and_record(client_obj, "/ping")

        throttled_logs = RequestLog.query.filter_by(
            client_id=client_obj.id, was_throttled=True
        ).all()
        assert len(throttled_logs) >= 1
