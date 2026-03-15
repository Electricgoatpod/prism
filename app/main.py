"""FastAPI app: API routes and lifecycle (scheduler)."""
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings
from app.models import PerformanceForecast, WearablePayload
from app.services.agent import ForecastAgent
from app.services.preprocessor import preprocess_to_payload
from app.services.simulator import WearableSimulator
from app.scheduler import setup_scheduler, get_latest_forecast

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler
    settings = Settings()
    scheduler = setup_scheduler(settings)
    yield
    if scheduler:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title="Prism",
    description="Private edge inference agent: wearable data → anonymous LLM → daily performance forecast",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5204", "http://127.0.0.1:5204", "https://frontend-brown-nu-53.vercel.app", "https://electricgoatpod.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/forecast/latest")
def forecast_latest() -> Optional[dict]:
    """Return the latest forecast from the autonomous agent (if any)."""
    return get_latest_forecast()


@app.post("/api/forecast/run", response_model=PerformanceForecast)
def forecast_run(use_simulated: bool = True) -> PerformanceForecast:
    """Run the agent once (simulated wearables) and return the forecast."""
    agent = ForecastAgent()
    return agent.run(use_simulated_data=use_simulated)


@app.post("/api/forecast/from-payload", response_model=PerformanceForecast)
def forecast_from_payload(payload: WearablePayload) -> PerformanceForecast:
    """Produce forecast from an anonymous preprocessed payload (e.g. from real wearables)."""
    agent = ForecastAgent()
    return agent.run_from_payload(payload)


@app.get("/api/simulate")
def simulate_wearables() -> dict:
    """Return one set of simulated wearable data + preprocessed payload (no LLM call)."""
    sim = WearableSimulator(seed=Settings().SIMULATOR_SEED)
    hrv, sleep, activity = sim.generate_for_today()
    payload = preprocess_to_payload(hrv, sleep, activity)
    return {
        "hrv": hrv.model_dump(mode="json"),
        "sleep": sleep.model_dump(mode="json"),
        "activity": activity.model_dump(mode="json"),
        "payload": payload.model_dump(mode="json"),
    }
