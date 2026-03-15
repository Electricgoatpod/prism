"""Local preprocessing: raw wearable data → anonymous signals for LLM."""
from app.models import ActivitySample, HRVSample, SleepSample, WearablePayload


def preprocess_to_payload(
    hrv: HRVSample,
    sleep: SleepSample,
    activity: ActivitySample,
) -> WearablePayload:
    """Convert raw samples to a single anonymous payload. No PII."""
    # Simple recovery heuristic: good sleep + higher HRV = higher signal
    hrv_norm = min(1.0, hrv.rmssd_ms / 60.0) if hrv.rmssd_ms else 0.5
    sleep_norm = (sleep.duration_hours / 8.0) * (sleep.efficiency_pct / 100.0)
    recovery_signal = min(1.0, 0.5 * hrv_norm + 0.5 * sleep_norm)
    return WearablePayload(
        hrv_rmssd_last_night=round(hrv.rmssd_ms, 1),
        sleep_hours=round(sleep.duration_hours, 1),
        sleep_efficiency_pct=round(sleep.efficiency_pct, 1),
        steps_yesterday=activity.steps,
        active_minutes_yesterday=activity.active_minutes,
        recovery_signal=round(recovery_signal, 3),
    )
