import asyncio
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from app.config import Config
from app.subs_db import SubscriptionsDB
from app.ns import NetsapiensAPI
from app.models import Subscriptions, SubscriptionRequest
from app.db_utils import update_table, read_from_table

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define the subscription service that uses the new database utilities.
class SubscriptionService:
    def __init__(self):
        self.db = SubscriptionsDB()
        self.ns_api = NetsapiensAPI()
        self.renewal_interval = Config.RENEWAL_INTERVAL  # e.g., in seconds

    async def start(self):
        """
        Initialize the service: set up the database table and perform an initial subscription check.
        Then enter an infinite loop to periodically check subscriptions.
        """
        logger.info("Starting subscription service...")
        # Ensure the subscriptions table exists.
        await self.db.setup_table()
        # Perform an initial check.
        await self.check_and_update_subscriptions()

        # Continuously check for expiring subscriptions.
        while True:
            await asyncio.sleep(self.renewal_interval)
            await self.check_and_update_subscriptions()

    async def shutdown(self):
        """
        Shutdown cleanup logic.
        With the new async session management via get_session(), no explicit DB close is necessary.
        """
        logger.info("Shutting down subscription service...")

    async def check_and_update_subscriptions(self):
        """
        Check for subscriptions that are nearing expiration and renew them.
        """

        logger.info("Checking for subscriptions that need renewal...")
        # find all expiring/expired subscriptions
        subscriptions = await self.db.fetch_expiring_subscriptions()
        # filter out the unique domains with expiring subscriptions
        logger.info(
            "Filtering for unique domains with subscriptions that need updating..."
        )
        expiring_domain = list({d.domain for d in subscriptions})
        # for each expiring domain update all subscriptions therein
        logger.info(
            f"Fetched {len(expiring_domain)} domains with expiring subscriptions."
        )
        if expiring_domain:
            # generate a new expiration time
            now = datetime.now(timezone.utc)
            new_expire_dt_obj = now + Config.SUBSCRIPTION_DURATION
            new_expire = new_expire_dt_obj.strftime("%Y-%m-%d %H:%M:%S")
            for sub in expiring_domain:
                logger.info(f"Renewing subscriptions for {sub}")
                # find all the subscriptions for the current domain
                expiring_subs = await read_from_table(
                    model=Subscriptions, filters={"domain": f"{sub}"}
                )
                # renew oauth token using the first model returned from the database since they should all be the same... right?..... RIGHT?!
                new_token_data = await self.ns_api.refresh_access_token(
                    expiring_subs[0].refresh_token
                )
                if new_token_data.get("access_token"):
                    new_oauth_token = str(new_token_data.get("access_token"))
                else:
                    raise Exception("Failed to get new token for {sub.domain}")

                new_refresh_token = new_token_data.get("refresh_token")
                # update each subscription
                for sublist in expiring_subs:
                    # update subscription via NMS API
                    await self.ns_api.update_subscription(
                        new_expire,
                        sublist.subscription_id,
                        new_oauth_token,
                        sublist.domain,
                    )
                    # update DB
                    update_data = {
                        "expires": new_expire,
                        "last_updated": datetime.now(timezone.utc).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "oauth_token": new_oauth_token,
                        "refresh_token": new_refresh_token,
                    }
                    await update_table(
                        Subscriptions,
                        {"subscription_id": sublist.subscription_id},
                        update_data,
                    )

        else:
            logger.info("No subscriptions need renewal.")

    async def setup_new_subscription(self, request: SubscriptionRequest):
        logger.info(f"Creating new subscription for {request.user}@{request.domain}")
        # trade un/pw for tokens
        try:
            token_dict = await self.ns_api.get_token(request.username, request.password)
        except Exception as e:
            logger.error(f"Failed to Authenticate: {e}")
            raise HTTPException(status_code=401, detail="Authentication failed")
        access_token = token_dict.get("access_token")
        if not access_token:
            logger.error("No access token received from NS API")
            raise HTTPException(
                status_code=500, detail="Failed to retrieve access token"
            )

        try:
            # Pass the provided username and password to the NS API call.
            subscription_response = await self.ns_api.create_subscription(
                model=request.model,
                post_url=request.post_url,
                domain=request.domain,
                user=request.user,
                token=access_token,
            )

            subscription_id = subscription_response.get("subscription_id")
            if not subscription_id:
                raise Exception("Failed to retrieve subscription ID from NS API")

            logger.info(
                f"Subscription created successfully for {request.user}@{request.domain}"
            )

        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        # update database with new subscription info
        try:
            update_data = {
                "subscription_id": subscription_id,
                "domain": request.domain,
                "model": request.model,
                # Use "expires_at" if available; otherwise, fall back to "subscription-expires-datetime"
                "expires": subscription_response.get("expires_at")
                or subscription_response.get("subscription-expires-datetime"),
                "post_url": request.post_url,
                "user": request.user,
                "oauth_token": access_token,
                "renewal_token": token_dict.get("refresh_token"),
                "last_updated": datetime.now(timezone.utc).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            }
            filters = {"subscription_id": subscription_id}
            await update_table(Subscriptions, filters, update_data)
        except Exception as e:
            logger.error(f"Failed to upsert subscription data in database: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to update database with subscription info",
            ) from e

        return {
            "status": "success",
            "subscription_id": subscription_id,
            "expires": subscription_response.get("expires_at")
            or subscription_response.get("subscription-expires-datetime"),
        }


# Create an instance of the subscription service.
subscription_service = SubscriptionService()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    FastAPI lifespan handler for startup and shutdown.
    Starts the subscription service as a background task.
    """
    logger.info("Starting subscription service during startup...")
    task = asyncio.create_task(subscription_service.start())

    try:
        yield
    finally:
        logger.info("Shutting down subscription service...")
        await subscription_service.shutdown()
        task.cancel()


# Create the FastAPI app with the lifespan handler.
app = FastAPI(lifespan=lifespan)


@app.post("/create-subscription")
async def create_subscription_endpoint(request: SubscriptionRequest):
    """
    API endpoint to create a new subscription.
    """
    logger.info(f"Received subscription creation request: {request}")
    return await subscription_service.setup_new_subscription(request)


@app.get("/status")
async def get_status():
    """
    A simple status endpoint.
    """
    return {"status": "Service is running!"}
