import logging
from typing import List
from datetime import datetime, timezone, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select

from .config import Config
from .models import (
    Base,
    Subscriptions,
)
from .db_utils import engine, get_session

logger = logging.getLogger(__name__)


# Subscription-specific database interactions.
class SubscriptionsDB:
    async def setup_table(self) -> None:
        """
        Creates the subscriptions table using the SQLAlchemy metadata.
        """
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Subscriptions table checked/created successfully.")

    async def fetch_expiring_subscriptions(self) -> List[Subscriptions]:
        """
        Fetches subscriptions that are set to expire before the next renewal interval.
        Assumes the 'expires' column is stored as a formatted string.
        """
        now = datetime.now(timezone.utc)
        renewal_threshold = now + timedelta(seconds=Config.RENEWAL_INTERVAL)
        renewal_threshold_str = renewal_threshold.strftime("%Y-%m-%d %H:%M:%S")
        try:
            async with get_session() as session:
                stmt = select(Subscriptions).where(
                    Subscriptions.expires <= renewal_threshold_str
                )
                result = await session.execute(stmt)
                subscriptions = list(result.scalars().all())
                logger.info(f"Fetched {len(subscriptions)} expiring subscriptions.")
                return subscriptions
        except SQLAlchemyError as e:
            logger.exception("Error fetching expiring subscriptions: {e}")
            raise Exception("Failed to fetch subscriptions") from e
