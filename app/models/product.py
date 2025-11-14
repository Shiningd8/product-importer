from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index, text
from sqlalchemy.sql import func
from app.database import Base


class Product(Base):
    """
    The Product model - where all your inventory dreams come true!
    SKU is our unique identifier (case-insensitive, because we're friendly like that).
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(500), nullable=False)
    description = Column(String(2000), nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'))

    # Case-insensitive SKU index - because "ABC123" and "abc123" should be the same product
    __table_args__ = (
        Index('ix_products_sku_lower', func.lower(sku), unique=True),
    )

