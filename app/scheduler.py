from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.future import select
from sqlalchemy import update
from datetime import datetime, timezone
from .db_utils import get_session
from .models import Subscriptions
from .config import Config
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the scheduler
scheduler = AsyncIOScheduler()

# Define the time before expiration to update (e.g., 5 minutes before expiration)
TIME_BEFORE_EXPIRATION = Config.TIME_BEFORE_EXPIRATION


async def update_expiring_subscriptions(session):
    now = datetime.now(timezone.utc)
    expiration_threshold = now + TIME_BEFORE_EXPIRATION
    renewal_threshold_str = expiration_threshold.strftime("%Y-%m-%d %H:%M:%S")

    try:
        # Query subscriptions that are expiring within the threshold
        stmt = select(Subscriptions).where(
            Subscriptions.expires <= renewal_threshold_str
        )
        result = await session.execute(stmt)
        expiring_subscriptions = list(result.scalars().all())
        logger.info(f"Fetched {len(expiring_subscriptions)} expiring subscriptions.")

        for subscription in expiring_subscriptions:
            # Log subscription details (using 'user' as defined in your model)
            logger.info(
                f"Updating subscription for user {subscription.user} with expiration {subscription.expires}"
            )
            # Update only the last_updated field
            update_stmt = (
                update(Subscriptions)
                .where(Subscriptions.id == subscription.id)
                .values(last_updated=now.strftime("%Y-%m-%d %H:%M:%S"))
            )
            await session.execute(update_stmt)

        await session.commit()
    except Exception as e:
        logger.error(f"Error updating subscriptions: {str(e)}")
        await session.rollback()


async def check_and_update_subscriptions():
    """
    Background task to check and update subscriptions nearing expiration.
    This task is called periodically by the scheduler.
    """
    async with get_session() as session:
        await update_expiring_subscriptions(session)


def start_scheduler():
    """
    Starts the APScheduler with the specified interval and job.
    Called during application startup.
    """
    scheduler.add_job(
        check_and_update_subscriptions,
        trigger=IntervalTrigger(minutes=1),  # Runs every minute; adjust as needed
        next_run_time=datetime.now(timezone.utc),  # Start immediately
    )
    scheduler.start()


def stop_scheduler():
    """
    Stops the scheduler gracefully.
    Called during application shutdown.
    """
    scheduler.shutdown()
