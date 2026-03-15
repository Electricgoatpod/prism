"""Nebius Token Factory LLM client (OpenAI-compatible API)."""
from typing import Optional
from openai import OpenAI

from app.config import Settings
from app.models import PerformanceForecast, WearablePayload


def _build_prompt(payload: WearablePayload) -> str:
    return f"""You are a concise personal performance coach. Based only on these anonymous wearable-derived signals, give a daily performance forecast. No medical advice.

Signals (anonymous, no user identity):
- HRV (RMSSD last night): {payload.hrv_rmssd_last_night} ms
- Sleep: {payload.sleep_hours} h, {payload.sleep_efficiency_pct}% efficiency
- Yesterday: {payload.steps_yesterday} steps, {payload.active_minutes_yesterday} active minutes
- Recovery signal (0–1): {payload.recovery_signal}

Respond with EXACTLY this structure, one line each:
SUMMARY: <one short sentence>
SCORE: <number 1-10>
FOCUS_WINDOW: <e.g. "9–11 AM" or "2–4 PM">
CRASH_WINDOW: <predicted low-energy window e.g. "2–4 PM" or "None">
SUGGESTIONS: <comma-separated short tips, or "None">
HOURLY_ENERGY: <comma-separated energy values (0-10) for hours 6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21>
"""


class NebiusLLMClient:
    """Calls Nebius Token Factory (OpenAI-compatible) with anonymous payloads only."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or Settings()
        self._client = OpenAI(
            api_key=self._settings.NEBIUS_API_KEY or "not-set",
            base_url=self._settings.NEBIUS_BASE_URL,
        )

    def forecast(self, payload: WearablePayload) -> PerformanceForecast:
        """Send anonymous payload to LLM; parse structured forecast."""
        from datetime import date, datetime
        import re

        prompt = _build_prompt(payload)
        resp = self._client.chat.completions.create(
            model=self._settings.NEBIUS_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )
        text = (resp.choices[0].message.content or "").strip()

        summary = ""
        score = 5.0
        focus_window = ""
        crash_window = ""
        suggestions: list[str] = []
        hourly_energy_curve = []

        for line in text.splitlines():
            line = line.strip()
            if line.upper().startswith("SUMMARY:"):
                summary = line.split(":", 1)[-1].strip()
            elif line.upper().startswith("SCORE:"):
                try:
                    score = float(re.search(r"[\d.]+", line).group())
                except (AttributeError, ValueError):
                    pass
                score = max(1, min(10, score))
            elif line.upper().startswith("FOCUS_WINDOW:"):
                focus_window = line.split(":", 1)[-1].strip()
            elif line.upper().startswith("CRASH_WINDOW:"):
                crash_window = line.split(":", 1)[-1].strip()
                if crash_window.upper() == "NONE":
                    crash_window = ""
            elif line.upper().startswith("SUGGESTIONS:"):
                raw = line.split(":", 1)[-1].strip()
                if raw and raw.upper() != "NONE":
                    suggestions = [s.strip() for s in raw.split(",") if s.strip()]
            elif line.upper().startswith("HOURLY_ENERGY:"):
                raw = line.split(":", 1)[-1].strip()
                hours = [6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21]
                try:
                    values = [float(v.strip()) for v in raw.split(",")]
                    hourly_energy_curve = [
                        {"hour": h, "energy": max(0, min(10, v))}
                        for h, v in zip(hours, values)
                    ]
                except (ValueError, AttributeError):
                    pass

        if not summary:
            summary = "Unable to generate forecast from model response."

        return PerformanceForecast(
            date=date.today(),
            summary=summary,
            score_1_to_10=score,
            focus_window=focus_window,
            crash_window=crash_window,
            suggestions=suggestions,
            hourly_energy_curve=hourly_energy_curve,
            generated_at_utc=datetime.utcnow(),
        )
