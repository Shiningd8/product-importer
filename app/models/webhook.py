from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, text
from sqlalchemy.sql import func
from app.database import Base


class Webhook(Base):
    """
    Webhook model - the messenger that delivers product event updates to external systems.
    Like a postal service for your product events!
    """
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(500), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)  # e.g., "product.created", "product.updated", "product.deleted"
    enabled = Column(Boolean, default=True, nullable=False)
    secret = Column(String(255), nullable=True)  # Optional secret for webhook authentication
    description = Column(Text, nullable=True)  # Optional description of what this webhook does
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'))

