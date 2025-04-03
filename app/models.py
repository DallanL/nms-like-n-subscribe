from datetime import datetime
from sqlalchemy import Integer, String, DateTime, text
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from pydantic import BaseModel, Field

Base = declarative_base()


class Subscriptions(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )
    last_updated: Mapped[str | None] = mapped_column(String(30))
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    expires: Mapped[str] = mapped_column(String(255), nullable=False)
    subscription_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )
    post_url: Mapped[str] = mapped_column(String(255), nullable=False)
    user: Mapped[str] = mapped_column(String(255), nullable=False)
    oauth_token: Mapped[str] = mapped_column(String(255), nullable=False)
    refresh_token: Mapped[str] = mapped_column(String(255), nullable=False)


class SubscriptionRequest(BaseModel):
    domain: str = Field(..., json_schema_extra={"example": "example.com"})
    model: str = Field(..., json_schema_extra={"example": "premium"})
    post_url: str = Field(
        ..., json_schema_extra={"example": "https://example.com/callback"}
    )
    user: str = Field(..., json_schema_extra={"example": "user@example.com"})
    username: str = Field(..., json_schema_extra={"example": "apiuser"})
    password: str = Field(..., json_schema_extra={"example": "strongpassword"})
