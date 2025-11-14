import httpx
import asyncio
import time
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.webhook import Webhook
from app.schemas.webhook import WebhookTestResponse


class WebhookDispatcher:
    """
    The webhook dispatcher - the messenger that delivers product events to external systems.
    Handles the heavy lifting of actually sending webhook payloads.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.timeout_seconds = 10  # How long to wait for webhook response
    
    async def _deliver_payload(
        self,
        webhook_url: str,
        payload: Dict,
        secret: Optional[str] = None
    ) -> WebhookTestResponse:
        """
        Actually send the webhook payload to the destination.
        Returns a test response with success status and timing info.
        """
        start_time = time.time()
        
        try:
            headers = {"Content-Type": "application/json"}
            if secret:
                headers["X-Webhook-Secret"] = secret
            
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers=headers
                )
                
                response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                
                return WebhookTestResponse(
                    success=response.is_success,
                    status_code=response.status_code,
                    response_time_ms=round(response_time, 2),
                    message=f"Webhook delivered successfully" if response.is_success else f"Webhook delivery failed with status {response.status_code}",
                    error=None if response.is_success else f"HTTP {response.status_code}"
                )
        
        except httpx.TimeoutException:
            response_time = (time.time() - start_time) * 1000
            return WebhookTestResponse(
                success=False,
                status_code=None,
                response_time_ms=round(response_time, 2),
                message="Webhook delivery timed out",
                error="Request timeout"
            )
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return WebhookTestResponse(
                success=False,
                status_code=None,
                response_time_ms=round(response_time, 2),
                message="Webhook delivery failed",
                error=str(e)
            )
    
    async def trigger_webhooks_for_event(
        self,
        event_type: str,
        event_data: Dict
    ) -> List[WebhookTestResponse]:
        """
        Find all enabled webhooks for an event type and trigger them.
        Like sending invitations to a party - but for webhooks!
        """
        # Find all active webhooks listening for this event
        active_webhooks = self.db.query(Webhook).filter(
            Webhook.event_type == event_type,
            Webhook.enabled == True
        ).all()
        
        if not active_webhooks:
            return []
        
        # Prepare the payload - the message we're sending
        webhook_payload = {
            "event": event_type,
            "data": event_data,
            "timestamp": time.time()
        }
        
        # Trigger all webhooks concurrently - because waiting is boring
        delivery_tasks = [
            self._deliver_payload(
                webhook.url,
                webhook_payload,
                webhook.secret
            )
            for webhook in active_webhooks
        ]
        
        results = await asyncio.gather(*delivery_tasks, return_exceptions=True)
        
        # Convert any exceptions to error responses
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append(WebhookTestResponse(
                    success=False,
                    message="Webhook delivery failed",
                    error=str(result)
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def test_webhook_delivery(
        self,
        webhook_url: str,
        secret: Optional[str] = None
    ) -> WebhookTestResponse:
        """
        Test a webhook by sending a sample payload.
        The dress rehearsal before the real performance!
        """
        test_payload = {
            "event": "webhook.test",
            "data": {"message": "This is a test webhook delivery"},
            "timestamp": time.time()
        }
        
        return await self._deliver_payload(webhook_url, test_payload, secret)

