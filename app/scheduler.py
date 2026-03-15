"""Autonomous agent scheduler: runs forecast agent on a timer without user input."""
import logging
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import Settings
from app.services.agent import ForecastAgent

logger = logging.getLogger(__name__)

# In-memory store for latest forecast (optional: replace with DB or file)
_latest_forecast: Optional[dict] = None


def _run_agent_sync() -> None:
    """Synchronous job: run agent and store result."""
    global _latest_forecast
    try:
        settings = Settings()
        if not settings.AGENT_ENABLED:
            return
        agent = ForecastAgent(settings)
        forecast = agent.run(use_simulated_data=True)
        _latest_forecast = forecast.model_dump(mode="json")
        logger.info("Prism agent run completed: score=%.1f", forecast.score_1_to_10)
    except Exception as e:
        logger.exception("Prism agent run failed: %s", e)


def get_latest_forecast() -> Optional[dict]:
    """Return the last forecast produced by the scheduled agent (or None)."""
    return _latest_forecast


def setup_scheduler(settings: Optional[Settings] = None) -> AsyncIOScheduler:
    """Create and start the scheduler; agent runs on AGENT_RUN_CRON."""
    s = settings or Settings()
    scheduler = AsyncIOScheduler()
    if s.AGENT_ENABLED:
        try:
            trigger = CronTrigger.from_crontab(s.AGENT_RUN_CRON)
        except Exception:
            trigger = CronTrigger(hour=6, minute=0)  # default 6 AM
        scheduler.add_job(_run_agent_sync, trigger, id="prism_forecast")
        scheduler.start()
        logger.info("Prism scheduler started (cron=%s)", s.AGENT_RUN_CRON)
    return scheduler
