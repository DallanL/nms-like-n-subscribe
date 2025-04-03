import os
from dotenv import dotenv_values
from datetime import timedelta

# Load the .env file if present (useful for local development)
file_env_vars = dotenv_values()


# Use environment variables from the runtime environment, falling back to .env file if not found
def get_env_variable(key, default=None):
    return os.getenv(key, file_env_vars.get(key, default))


class Config:
    # PostgreSQL settings
    POSTGRESQL_HOST = get_env_variable("POSTGRESQL_HOST", "localhost")
    POSTGRESQL_PORT = int(get_env_variable("POSTGRESQL_PORT", 5432) or 5432)
    POSTGRESQL_USER = get_env_variable("POSTGRESQL_USER", "postgres")
    POSTGRESQL_PASS = get_env_variable("POSTGRESQL_PASS", "password")
    POSTGRESQL_DATABASE = get_env_variable("POSTGRESQL_DATABASE", "postgres")
    POSTGRESQL_TABLE_SUBSCRIPTIONS = get_env_variable(
        "POSTGRESQL_TABLE_SUBSCRIPTIONS", "subscriptions"
    )
    POSTGRESQL_URL = f"postgresql://{POSTGRESQL_USER}:{POSTGRESQL_PASS}@{POSTGRESQL_HOST}:{POSTGRESQL_PORT}/{POSTGRESQL_DATABASE}"

    # Netsapiens config
    NETSAPIENS_API_URL = (
        get_env_variable("NETSAPIENS_API_URL", "https://<your-api-server>")
        or "https://<your-api-server>"
    )
    NETSAPIENS_API_CLIENT_ID = get_env_variable("NETSAPIENS_API_CLIENT_ID", "")
    NETSAPIENS_API_CLIENT_PASS = get_env_variable("NETSAPIENS_API_CLIENT_PASS", "")

    # Other configurations
    SUBSCRIPTION_DURATION = timedelta(
        days=int(get_env_variable("SUBSCRIPTION_DURATION", 1) or 1)
    )  # Duration of subscription in days

    RENEWAL_INTERVAL = int(get_env_variable("RENEWAL_INTERVAL", 3600) or 3600)
    TIME_BEFORE_EXPIRATION = timedelta(minutes=5)

    # Logging configuration
    LOG_LEVEL = get_env_variable("LOG_LEVEL", "INFO")
    LOG_FILE = get_env_variable("LOG_FILE", "")
