from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional


class WebhookBase(BaseModel):
    """The foundation for all webhook schemas - the blueprint for webhook configurations."""
    url: str = Field(..., description="The destination URL where webhook events will be delivered")
    event_type: str = Field(..., description="Event type to listen for (e.g., 'product.created', 'product.updated', 'product.deleted')")
    enabled: bool = Field(True, description="Whether this webhook is active and ready to fire")
    secret: Optional[str] = Field(None, description="Optional secret key for webhook authentication")
    description: Optional[str] = Field(None, description="Human-readable description of what this webhook does")


class WebhookCreate(WebhookBase):
    """When you want to create a new webhook - giving birth to a new event messenger."""
    pass


class WebhookUpdate(BaseModel):
    """For updating webhook settings - because even webhooks need a makeover sometimes."""
    url: Optional[str] = None
    event_type: Optional[str] = None
    enabled: Optional[bool] = None
    secret: Optional[str] = None
    description: Optional[str] = None


class WebhookResponse(WebhookBase):
    """The complete webhook story - includes all the database secrets."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebhookTestResponse(BaseModel):
    """Response from testing a webhook - the report card for your webhook delivery."""
    success: bool
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    message: str
    error: Optional[str] = None

