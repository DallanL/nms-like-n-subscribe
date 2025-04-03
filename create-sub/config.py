import re


class Config:
    # Default settings
    DEFAULT_MODEL = "presence"
    VALID_MODELS = [
        "call",
        "call_origid",
        "subscriber",
        "presence",
        "auditlog",
        "message",
        "agent",
    ]
    DEFAULT_POST_URL = "<post_url>"
    DEFAULT_DOMAIN_PATTERN = r"^\d{10}\.com$"
    DEFAULT_EXPIRES = 1

    # URL to post the data
    POST_HOST = "http://localhost:8001/create-subscription"

    @staticmethod
    def is_valid_domain(domain: str) -> bool:
        """Validate domain using regex"""
        return bool(re.match(Config.DEFAULT_DOMAIN_PATTERN, domain))
