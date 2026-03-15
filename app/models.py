"""Domain models: wearable data and performance forecast."""
from datetime import date, datetime
from pydantic import BaseModel, Field


# ---- Simulated wearable inputs ----

class HRVSample(BaseModel):
    """Heart rate variability sample (e.g. overnight)."""
    timestamp_utc: datetime
    rmssd_ms: float = Field(..., ge=0, description="RMSSD in ms")
    resting_hr_bpm: float = Field(..., ge=30, le=120)


class SleepSample(BaseModel):
    """Sleep session summary."""
    date: date
    duration_hours: float = Field(..., ge=0, le=24)
    efficiency_pct: float = Field(..., ge=0, le=100)
    deep_minutes: int = Field(0, ge=0, le=600)
    rem_minutes: int = Field(0, ge=0, le=600)
    latency_minutes: int = Field(0, ge=0, le=120)


class ActivitySample(BaseModel):
    """Activity summary (e.g. previous day)."""
    date: date
    steps: int = Field(0, ge=0, le=100_000)
    active_minutes: int = Field(0, ge=0, le=1440)
    calories_est: int = Field(0, ge=0, le=10_000)


class WearablePayload(BaseModel):
    """Anonymous payload sent to LLM: preprocessed, no PII."""
    hrv_rmssd_last_night: float
    sleep_hours: float
    sleep_efficiency_pct: float
    steps_yesterday: int
    active_minutes_yesterday: int
    # Optional: add derived signals (e.g. "recovery_score", "readiness")
    recovery_signal: float = Field(1.0, ge=0, le=1)


# ---- LLM output ----

class HourlyEnergy(BaseModel):
    """Predicted energy level for a given hour."""
    hour: int = Field(..., ge=0, le=23)
    energy: float = Field(..., ge=0, le=10)


class PerformanceForecast(BaseModel):
    """Daily performance forecast returned by the agent."""
    date: date
    summary: str = Field(..., description="Short human-readable summary")
    score_1_to_10: float = Field(..., ge=1, le=10)
    focus_window: str = Field("", description="Recommended best focus window")
    crash_window: str = Field("", description="Predicted low-energy window e.g. '2–4 PM'")
    suggestions: list[str] = Field(default_factory=list)
    hourly_energy_curve: list[HourlyEnergy] = Field(default_factory=list)
    generated_at_utc: datetime = Field(default_factory=datetime.utcnow)
