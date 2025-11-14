from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.webhook import Webhook
from app.schemas.webhook import (
    WebhookCreate,
    WebhookUpdate,
    WebhookResponse,
    WebhookTestResponse
)
from app.services.webhook_service import WebhookDispatcher

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.get("", response_model=List[WebhookResponse])
def get_all_webhooks(db: Session = Depends(get_db)):
    """Get all webhooks - see who's listening to your product events."""
    webhooks = db.query(Webhook).all()
    return webhooks


@router.get("/{webhook_id}", response_model=WebhookResponse)
def get_webhook_by_id(webhook_id: int, db: Session = Depends(get_db)):
    """Get a specific webhook by ID - find that one special listener."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return webhook


@router.post("", response_model=WebhookResponse, status_code=201)
def create_webhook(webhook_data: WebhookCreate, db: Session = Depends(get_db)):
    """
    Create a new webhook - add a new listener to your product event party.
    Valid event types: product.created, product.updated, product.deleted
    """
    # Validate event type
    valid_event_types = ["product.created", "product.updated", "product.deleted"]
    if webhook_data.event_type not in valid_event_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid event type. Must be one of: {', '.join(valid_event_types)}"
        )
    
    new_webhook = Webhook(**webhook_data.model_dump())
    db.add(new_webhook)
    db.commit()
    db.refresh(new_webhook)
    return new_webhook


@router.put("/{webhook_id}", response_model=WebhookResponse)
def update_webhook(
    webhook_id: int,
    webhook_update: WebhookUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a webhook - give it a makeover with new settings.
    Only provided fields will be updated.
    """
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # Validate event type if being updated
    if webhook_update.event_type:
        valid_event_types = ["product.created", "product.updated", "product.deleted"]
        if webhook_update.event_type not in valid_event_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid event type. Must be one of: {', '.join(valid_event_types)}"
            )
    
    # Update only provided fields
    update_data = webhook_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(webhook, field, value)
    
    db.commit()
    db.refresh(webhook)
    return webhook


@router.delete("/{webhook_id}", status_code=204)
def delete_webhook(webhook_id: int, db: Session = Depends(get_db)):
    """Delete a webhook - remove a listener from the party."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    db.delete(webhook)
    db.commit()
    return None


@router.post("/{webhook_id}/test", response_model=WebhookTestResponse)
async def test_webhook(webhook_id: int, db: Session = Depends(get_db)):
    """
    Test a webhook by sending a sample payload.
    The dress rehearsal - see if your webhook is ready for the real show!
    """
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    dispatcher = WebhookDispatcher(db)
    test_result = await dispatcher.test_webhook_delivery(webhook.url, webhook.secret)
    
    return test_result

