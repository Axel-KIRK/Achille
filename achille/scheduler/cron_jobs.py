"""
Achille — Cron Jobs
Configure APScheduler pour les tâches récurrentes.
"""
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from zoneinfo import ZoneInfo

from config.settings import (
    TIMEZONE,
    MORNING_BRIEFING_HOUR, MORNING_BRIEFING_MINUTE,
    EVENING_CHECKIN_HOUR, EVENING_CHECKIN_MINUTE,
)
from scheduler.heartbeat import (
    morning_briefing,
    evening_checkin,
    weekly_review,
    inactivity_check,
)

tz = ZoneInfo(TIMEZONE)


def create_scheduler() -> AsyncIOScheduler:
    """Crée et configure le scheduler."""
    scheduler = AsyncIOScheduler(timezone=tz)
    
    # Briefing matin — tous les jours
    scheduler.add_job(
        morning_briefing,
        CronTrigger(
            hour=MORNING_BRIEFING_HOUR,
            minute=MORNING_BRIEFING_MINUTE,
            timezone=tz,
        ),
        id="morning_briefing",
        name="Briefing matin",
    )
    
    # Check-in du soir — tous les jours
    scheduler.add_job(
        evening_checkin,
        CronTrigger(
            hour=EVENING_CHECKIN_HOUR,
            minute=EVENING_CHECKIN_MINUTE,
            timezone=tz,
        ),
        id="evening_checkin",
        name="Check-in soir",
    )
    
    # Revue hebdomadaire — dimanche 18h
    scheduler.add_job(
        weekly_review,
        CronTrigger(
            day_of_week="sun",
            hour=18,
            minute=0,
            timezone=tz,
        ),
        id="weekly_review",
        name="Revue hebdomadaire",
    )
    
    # Check inactivité — toutes les 12h
    scheduler.add_job(
        inactivity_check,
        CronTrigger(
            hour="8,20",
            minute=0,
            timezone=tz,
        ),
        id="inactivity_check",
        name="Check inactivité",
    )
    
    return scheduler
