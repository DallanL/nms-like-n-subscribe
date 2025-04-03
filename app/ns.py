import logging
import httpx
from datetime import datetime, timezone, timedelta

from .config import Config

logger = logging.getLogger(__name__)


class NetsapiensAPI:
    def __init__(self):
        self.base_url = Config.NETSAPIENS_API_URL
        self.client_id = Config.NETSAPIENS_API_CLIENT_ID
        self.client_secret = Config.NETSAPIENS_API_CLIENT_PASS

    async def get_token(self, username: str, password: str) -> dict:
        """
        Request a new OAuth2 token using the provided username and password.
        """
        url = f"{self.base_url}/ns-api/v2/tokens"
        headers = {"accept": "application/json", "content-type": "application/json"}
        payload = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": username,
            "password": password,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                token_data = response.json()
                if token_data.get("access_token"):
                    expires_in = token_data.get("expires_in", 0)
                    token_data["expires"] = (
                        datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                    ).strftime("%Y-%m-%d %H:%M:%S")
                    return token_data
                else:
                    raise Exception(
                        f"Oauth Failed to return an access token: {token_data}"
                    )
            else:
                error_message = response.text
                logger.error(
                    f"get_token - Failed to retrieve token. Response: {error_message}"
                )
                raise Exception(f"Failed to get token: {error_message}")

    async def refresh_access_token(self, refresh_token: str) -> dict:
        """
        Refresh the OAuth2 token using the provided refresh token.
        """
        url = f"{self.base_url}/ns-api/v2/tokens"
        headers = {"accept": "application/json", "content-type": "application/json"}
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
        }
        logger.info(f"Sending Token refresh to:\n{url}\n{payload}")
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                token_data = response.json()
                expires_in = token_data.get("expires_in", 0)
                token_data["expires"] = (
                    datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                ).strftime("%Y-%m-%d %H:%M:%S")
                return token_data
            else:
                error_message = response.text
                logger.error(
                    f"refresh_access_token - Failed to refresh token. Response: {error_message}"
                )
                raise Exception(f"Failed to refresh token: {error_message}")

    async def create_subscription(
        self,
        model: str,
        post_url: str,
        domain: str,
        user: str,
        token: str,
    ) -> dict:
        """
        Create a new subscription using the new NS API format.

        This method expects a valid access token to be provided (via the 'token' parameter).
        It sends a POST request with a JSON payload to create the subscription and returns
        the subscription data from the API response.

        Parameters:
          - model: The subscription model.
          - post_url: The callback URL.
          - domain: The domain for the subscription.
          - user: The user associated with the subscription.
          - token: A valid OAuth access token.

        Returns:
          A dictionary containing the subscription details returned by the API.
        """
        payload = {
            "model": model,
            "post_url": post_url,
            "domain": domain,
            "user": user,
        }

        url = f"{self.base_url}/ns-api/v2/subscriptions"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            logger.debug(
                f"create_subscription - Response status: {response.status_code}"
            )
            logger.debug(f"create_subscription - Response text: {response.text}")

            if response.status_code in (200, 201):
                try:
                    subscription_data = response.json()
                    logger.info(
                        f"Subscription created successfully: "
                        f"ID={subscription_data.get('id')}, "
                        f"User={subscription_data.get('user')}@{subscription_data.get('domain')}, "
                        f"Expires={subscription_data.get('subscription-expires-datetime')}"
                    )
                    # add formatted versions of creation and expiration date/times to the return dict
                    subscription_data["created_at"] = datetime.fromisoformat(
                        subscription_data.get("subscription-creation-datetime")
                    ).strftime("%Y-%m-%d %H:%M:%S")

                    subscription_data["expires_at"] = datetime.fromisoformat(
                        subscription_data.get("subscription-expires-datetime")
                    ).strftime("%Y-%m-%d %H:%M:%S")
                    return subscription_data
                except Exception as parse_error:
                    logger.error(f"Error parsing subscription response: {parse_error}")
                    raise Exception(
                        "Failed to parse subscription response"
                    ) from parse_error
            else:
                raise Exception(
                    f"Failed to create subscription. Status: {response.status_code}"
                )

    async def ns_delete_subscription(
        self, subscription_id: str, domain: str, token: str
    ) -> dict:
        """
        Delete an existing subscription.
        This method expects a valid access token to be provided (via the 'token' parameter).
        It sends a DELETE request to remove the subscription in question.

        Parameters:
          - subscription_id: subscription ID to be updated.
          - token: A valid OAuth access token.
          - domain: domain of the subscription being deleted.
        """
        url = f"{self.base_url}/ns-api/v2/subscriptions/{subscription_id}"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {token}",
        }
        payload = {"domain": domain}
        logger.info(f"Deleting subscription for {payload}")
        async with httpx.AsyncClient() as client:
            response = await client.delete(url, headers=headers)
            response_text = response.text
            logger.debug(
                f"ns_delete_subscription - Response status: {response.status_code}"
            )
            logger.debug(f"ns_delete_subscription - Response text: {response_text}")

            if response.status_code is 202:
                logger.info(f"Subscription {subscription_id} deleted successfully.")
                return {"status": "success", "subscription_id": subscription_id}
            else:
                raise Exception(
                    f"Failed to delete subscription. Status: {response.status_code}"
                )

    async def update_subscription(
        self,
        new_expire: str,
        subscription_id: str,
        token: str,
        domain: str,
    ) -> None:
        """
        Update subscription using the new NS API format.

        This method expects a valid access token to be provided (via the 'token' parameter).
        It sends a PUT request with a JSON payload to update the subscription expiration date/time and returns
        the subscription data from the API response.

        Parameters:
          - subscription_id: subscription ID to be updated
          - new_expire: Expiration datetime as a formatted string YYYY-MM-DD HH:MM:SS.
          - token: A valid OAuth access token.
          - domain: the domain of the subscription being deleted.

        Returns:
          A dictionary containing the subscription details returned by the API.
        """
        payload = {
            "subscription-expires-datetime": new_expire,
            "domain": domain,
        }

        url = f"{self.base_url}/ns-api/v2/subscriptions/{subscription_id}"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {token}",
        }
        logger.info(f"Updating subscription:\n{url}\n{headers}\n{payload}")

        async with httpx.AsyncClient() as client:
            response = await client.put(url, json=payload, headers=headers)
            logger.debug(
                f"create_subscription - Response status: {response.status_code}"
            )
            logger.debug(f"create_subscription - Response text: {response.text}")

            if response.status_code is 202:
                try:
                    logger.info(
                        f"Subscription updated successfully: "
                        f"ID={subscription_id}, "
                        f"Expires={new_expire}"
                    )
                    return
                except Exception as parse_error:
                    logger.error(f"Error parsing subscription response: {parse_error}")
                    raise Exception(
                        "Failed to parse subscription response"
                    ) from parse_error
            else:
                raise Exception(
                    f"Failed to update subscription. Status: {response.status_code}"
                )
