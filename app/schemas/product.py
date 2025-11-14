from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ProductBase(BaseModel):
    """The foundation of all product schemas - like the blueprint for a product."""
    sku: str = Field(..., min_length=1, max_length=255, description="Unique product SKU (case-insensitive)")
    name: str = Field(..., min_length=1, max_length=500, description="Product name")
    description: Optional[str] = Field(None, max_length=2000, description="Product description")
    active: bool = Field(True, description="Whether the product is active")


class ProductCreate(ProductBase):
    """When you want to bring a new product into this world."""


class ProductUpdate(BaseModel):
    """For those moments when you need to change your mind - everything is optional here."""
    sku: Optional[str] = Field(None, min_length=1, max_length=255)
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    active: Optional[bool] = None


class ProductResponse(ProductBase):
    """The full product story - includes all the database secrets like when it was born and last updated."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """A paginated list of products - because showing 500,000 products at once would be chaos."""
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

