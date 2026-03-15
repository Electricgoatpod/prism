"""Simulated wearable data (HRV, sleep, activity) for local/dev use."""
import random
from datetime import date, datetime, timedelta
from typing import Optional

from app.models import ActivitySample, HRVSample, SleepSample


class WearableSimulator:
    """Generates plausible synthetic wearable data. No PII; for edge/testing."""

    def __init__(self, seed: Optional[int] = None) -> None:
        self._rng = random.Random(seed)

    def hrv_for_last_night(self, for_date: date) -> HRVSample:
        # Typical RMSSD range ~20–80 ms; resting HR 50–70
        rmssd = self._rng.gauss(45, 15)
        resting_hr = self._rng.gauss(60, 6)
        # Midnight UTC as placeholder
        ts = datetime(for_date.year, for_date.month, for_date.day, 0, 0, 0)
        return HRVSample(timestamp_utc=ts, rmssd_ms=max(10, rmssd), resting_hr_bpm=max(40, min(100, resting_hr)))

    def sleep_for(self, for_date: date) -> SleepSample:
        duration = self._rng.gauss(7.2, 1.0)
        efficiency = self._rng.gauss(88, 6)
        deep = int(self._rng.gauss(90, 25))
        rem = int(self._rng.gauss(100, 30))
        latency = int(self._rng.gauss(15, 10))
        return SleepSample(
            date=for_date,
            duration_hours=max(3, min(12, duration)),
            efficiency_pct=max(50, min(100, efficiency)),
            deep_minutes=max(0, deep),
            rem_minutes=max(0, rem),
            latency_minutes=max(0, min(120, latency)),
        )

    def activity_for(self, for_date: date) -> ActivitySample:
        steps = int(self._rng.gauss(7500, 3000))
        active = int(self._rng.gauss(45, 25))
        calories = int(1800 + steps * 0.04 + active * 3)
        return ActivitySample(
            date=for_date,
            steps=max(0, steps),
            active_minutes=max(0, min(1440, active)),
            calories_est=max(1000, min(5000, calories)),
        )

    def generate_for_today(self) -> tuple[HRVSample, SleepSample, ActivitySample]:
        """Last night's HRV/sleep, yesterday's activity."""
        today = date.today()
        yesterday = today - timedelta(days=1)
        return (
            self.hrv_for_last_night(today),
            self.sleep_for(today),  # sleep "for" today = last night
            self.activity_for(yesterday),
        )
