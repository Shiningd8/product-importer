from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from app.database import get_db
from app.models.product import Product
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse
)
from app.services.webhook_service import WebhookDispatcher

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=ProductListResponse)
def get_products(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    sku: Optional[str] = Query(None, description="Filter by SKU (case-insensitive)"),
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    description: Optional[str] = Query(None, description="Filter by description (partial match)"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """
    Get a paginated list of products with optional filtering.
    Because browsing through 500,000 products needs some organization!
    """
    query = db.query(Product)
    
    # Apply filters - the search party begins here
    if sku:
        query = query.filter(func.lower(Product.sku).contains(func.lower(sku)))
    if name:
        query = query.filter(Product.name.ilike(f"%{name}%"))
    if description:
        query = query.filter(Product.description.ilike(f"%{description}%"))
    if active is not None:
        query = query.filter(Product.active == active)
    
    # Counting the total before pagination
    total = query.count()
    
    # Applying pagination - slice and dice
    offset = (page - 1) * page_size
    products = query.offset(offset).limit(page_size).all()
    
    # Calculating the total pages
    total_pages = (total + page_size - 1) // page_size
    
    return ProductListResponse(
        items=products,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get a single product by ID - because sometimes you need to find that one special product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(
    product: ProductCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create a new product.
    SKU must be unique (case-insensitive) - we check this before creating.
    """
    # Check for duplicate SKU (case-insensitive)
    existing = db.query(Product).filter(
        func.lower(Product.sku) == func.lower(product.sku)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Product with SKU '{product.sku}' already exists"
        )
    
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    # Trigger webhooks in background
    async def trigger_webhooks():
        dispatcher = WebhookDispatcher(db)
        product_data = {
            "id": db_product.id,
            "sku": db_product.sku,
            "name": db_product.name,
            "description": db_product.description,
            "active": db_product.active
        }
        await dispatcher.trigger_webhooks_for_event("product.created", product_data)
    
    background_tasks.add_task(trigger_webhooks)
    
    return db_product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Update an existing product.
    Only provided fields will be updated - partial updates are welcome here!
    """
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check SKU uniqueness if SKU is being updated
    if product_update.sku:
        existing = db.query(Product).filter(
            func.lower(Product.sku) == func.lower(product_update.sku),
            Product.id != product_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Product with SKU '{product_update.sku}' already exists"
            )
    
    # Update only provided fields
    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)
    
    db.commit()
    db.refresh(db_product)
    
    # Trigger webhooks in background
    async def trigger_webhooks():
        dispatcher = WebhookDispatcher(db)
        product_data = {
            "id": db_product.id,
            "sku": db_product.sku,
            "name": db_product.name,
            "description": db_product.description,
            "active": db_product.active
        }
        await dispatcher.trigger_webhooks_for_event("product.updated", product_data)
    
    background_tasks.add_task(trigger_webhooks)
    
    return db_product


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Delete a product - handle with care, this action is permanent!"""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Store product data before deletion for webhook
    product_data = {
        "id": db_product.id,
        "sku": db_product.sku,
        "name": db_product.name,
        "description": db_product.description,
        "active": db_product.active
    }
    
    db.delete(db_product)
    db.commit()
    
    # Trigger webhooks in background
    async def trigger_webhooks():
        dispatcher = WebhookDispatcher(db)
        await dispatcher.trigger_webhooks_for_event("product.deleted", product_data)
    
    background_tasks.add_task(trigger_webhooks)
    
    return None


@router.delete("/bulk/all", status_code=200)
def delete_all_products(db: Session = Depends(get_db)):
    """
    Delete ALL products - the nuclear option!
    This requires careful consideration and should be protected in production.
    """
    deleted_count = db.query(Product).delete()
    db.commit()
    return {"message": f"Deleted {deleted_count} products", "deleted_count": deleted_count}

