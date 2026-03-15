"""Autonomous agent: simulate → preprocess → LLM → forecast. Runs on a timer."""
from datetime import date
from typing import Optional

from app.models import PerformanceForecast, WearablePayload
from app.services.simulator import WearableSimulator
from app.services.preprocessor import preprocess_to_payload
from app.services.nebius import NebiusLLMClient
from app.config import Settings


class ForecastAgent:
    """Orchestrates one run: get wearable data (simulated), preprocess, call LLM, return forecast."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or Settings()
        self._simulator = WearableSimulator(seed=self._settings.SIMULATOR_SEED)
        self._llm = NebiusLLMClient(self._settings)

    def run(self, use_simulated_data: bool = True) -> PerformanceForecast:
        """Produce today's performance forecast. If use_simulated_data, generate fake wearables locally."""
        if use_simulated_data:
            hrv, sleep, activity = self._simulator.generate_for_today()
            payload = preprocess_to_payload(hrv, sleep, activity)
        else:
            # TODO: plug in real wearable ingestion (local only, no PII sent)
            raise NotImplementedError("Real wearable ingestion not implemented; use simulated data.")
        return self._llm.forecast(payload)

    def run_from_payload(self, payload: WearablePayload) -> PerformanceForecast:
        """Produce forecast from an existing preprocessed payload (e.g. from API)."""
        return self._llm.forecast(payload)
