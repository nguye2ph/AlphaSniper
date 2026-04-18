"""Tests for adjustment engine — EMA rules, circuit breaker, cooldown."""

from datetime import datetime, timedelta, timezone

import pytest

from src.scheduler.adjustment_engine import evaluate
from src.scheduler.models import SourceMetrics, SourceScheduleConfig


def _config(**overrides) -> SourceScheduleConfig:
    defaults = {
        "name": "test_source",
        "current_interval_seconds": 300,
        "min_interval_seconds": 60,
        "max_interval_seconds": 3600,
        "articles_per_poll_high": 50,
        "articles_per_poll_low": 5,
        "max_rate_errors": 5,
        "adjustment_cooldown_seconds": 300,
    }
    defaults.update(overrides)
    return SourceScheduleConfig(**defaults)


def _metrics(**overrides) -> SourceMetrics:
    return SourceMetrics(**overrides)


class TestCooldown:
    def test_skip_when_recently_adjusted(self):
        config = _config(last_adjustment_at=datetime.now(timezone.utc) - timedelta(seconds=60))
        result = evaluate(config, _metrics())
        assert result.action == "cooldown_skip"

    def test_allow_when_cooldown_expired(self):
        config = _config(last_adjustment_at=datetime.now(timezone.utc) - timedelta(seconds=600))
        result = evaluate(config, _metrics(ema=3.0))
        assert result.action != "cooldown_skip"

    def test_allow_when_never_adjusted(self):
        config = _config(last_adjustment_at=None)
        result = evaluate(config, _metrics())
        assert result.action != "cooldown_skip"


class TestCircuitBreaker:
    def test_triggers_on_rate_limit_errors(self):
        config = _config()
        metrics = _metrics(rate_limit_errors=5)
        result = evaluate(config, metrics)
        assert result.action == "circuit_break"
        assert result.new_interval == 600  # 300 * 2

    def test_clamped_to_max(self):
        config = _config(current_interval_seconds=2000, max_interval_seconds=3600)
        metrics = _metrics(rate_limit_errors=5)
        result = evaluate(config, metrics)
        assert result.new_interval == 3600  # clamped

    def test_below_threshold_no_break(self):
        config = _config()
        metrics = _metrics(rate_limit_errors=4)
        result = evaluate(config, metrics)
        assert result.action != "circuit_break"


class TestEMAHighThreshold:
    def test_decrease_interval_when_ema_high(self):
        config = _config(current_interval_seconds=400)
        metrics = _metrics(ema=60.0)
        result = evaluate(config, metrics)
        assert result.action == "decrease"
        assert result.new_interval == 300  # 400 * 0.75 = 300

    def test_clamped_to_min(self):
        config = _config(current_interval_seconds=80, min_interval_seconds=60)
        metrics = _metrics(ema=60.0)
        result = evaluate(config, metrics)
        assert result.action == "decrease"
        assert result.new_interval == 60  # 80*0.75=60, clamped

    def test_no_decrease_at_min(self):
        config = _config(current_interval_seconds=60, min_interval_seconds=60)
        metrics = _metrics(ema=60.0)
        result = evaluate(config, metrics)
        # Can't decrease further, already at min
        assert result.action == "no_change"


class TestEMALowThreshold:
    def test_increase_interval_when_ema_low(self):
        config = _config(current_interval_seconds=300)
        metrics = _metrics(ema=2.0)
        result = evaluate(config, metrics)
        assert result.action == "increase"
        assert result.new_interval == 450  # 300 * 1.5

    def test_clamped_to_max(self):
        config = _config(current_interval_seconds=3000, max_interval_seconds=3600)
        metrics = _metrics(ema=2.0)
        result = evaluate(config, metrics)
        assert result.action == "increase"
        assert result.new_interval == 3600  # clamped

    def test_no_increase_at_max(self):
        config = _config(current_interval_seconds=3600, max_interval_seconds=3600)
        metrics = _metrics(ema=2.0)
        result = evaluate(config, metrics)
        assert result.action == "no_change"


class TestNoChange:
    def test_within_normal_range(self):
        config = _config()
        metrics = _metrics(ema=20.0)
        result = evaluate(config, metrics)
        assert result.action == "no_change"
        assert result.old_interval == result.new_interval


class TestEMAComputation:
    def test_ema_function(self):
        from src.scheduler.metrics_tracker import compute_ema

        # First value
        assert compute_ema(10.0, 0.0, 0.3) == pytest.approx(3.0)
        # Second value
        assert compute_ema(10.0, 3.0, 0.3) == pytest.approx(5.1)
        # Steady state
        assert compute_ema(10.0, 10.0, 0.3) == pytest.approx(10.0)


class TestIntervalToCron:
    def test_cron_expressions(self):
        from src.scheduler.scheduler_integration import _interval_to_cron

        assert _interval_to_cron(30) == "* * * * *"  # sub-minute -> every minute
        assert _interval_to_cron(60) == "*/1 * * * *"
        assert _interval_to_cron(300) == "*/5 * * * *"
        assert _interval_to_cron(900) == "*/15 * * * *"
        assert _interval_to_cron(3600) == "0 */1 * * *"
        assert _interval_to_cron(7200) == "0 */2 * * *"
