"""
WhatsApp webhook endpoints for Twilio integration.
Refactored to use service layer for business logic.
"""
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Depends
from fastapi.responses import PlainTextResponse
from typing import Dict, Any
from datetime import datetime
import logging

from ....core.logging import get_logger
from ..dependencies.services import get_whatsapp_service, get_ai_service
from ....services import WhatsAppService, AIService

logger = get_logger(__name__)
router = APIRouter(tags=["WhatsApp"])


@router.get("/health")
async def health_check():
    """Health check endpoint for WhatsApp webhook."""
    return {
        "status": "healthy",
        "service": "whatsapp_webhook",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    whatsapp_service: WhatsAppService = Depends(get_whatsapp_service),
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Handle incoming WhatsApp webhook from Twilio.
    Processes both incoming messages and status updates.
    """
    try:
        # Parse form data from Twilio
        form_data = await request.form()
        webhook_data = dict(form_data)

        logger.info(f"Received webhook data: {webhook_data}")

        # Determine webhook type
        if 'Body' in webhook_data:
            # Incoming message
            result = await whatsapp_service.process_incoming_message(webhook_data)

            # If a customer was identified, analyze sentiment in background
            if result.get('customer_id'):
                background_tasks.add_task(
                    analyze_message_sentiment,
                    webhook_data.get('Body', ''),
                    result['customer_id'],
                    ai_service
                )

            return PlainTextResponse("Message processed successfully")

        elif 'MessageStatus' in webhook_data:
            # Status update
            await whatsapp_service.process_status_update(webhook_data)
            return PlainTextResponse("Status update processed")

        else:
            logger.warning(f"Unknown webhook type: {webhook_data}")
            return PlainTextResponse("Webhook received")

    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        # Return success to prevent Twilio retries for non-critical errors
        return PlainTextResponse("Error processed")


@router.post("/send")
async def send_whatsapp_message(
    to_number: str,
    message_body: str,
    whatsapp_service: WhatsAppService = Depends(get_whatsapp_service)
):
    """Send a WhatsApp message to a phone number."""
    try:
        message = await whatsapp_service.send_message(
            to_number=to_number,
            message_body=message_body
        )

        return {
            "status": "sent",
            "message_id": str(message.id),
            "to": to_number
        }

    except Exception as e:
        logger.error(f"Failed to send WhatsApp message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to send message"
        )


@router.post("/send-bulk")
async def send_bulk_messages(
    customer_ids: list[str],
    message_template: str,
    personalize: bool = True,
    whatsapp_service: WhatsAppService = Depends(get_whatsapp_service)
):
    """Send bulk WhatsApp messages to multiple customers."""
    try:
        # Convert string IDs to UUIDs
        from uuid import UUID
        customer_uuids = [UUID(id) for id in customer_ids]

        results = await whatsapp_service.send_bulk_messages(
            customer_ids=customer_uuids,
            message_template=message_template,
            personalize=personalize
        )

        return results

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail="Invalid customer ID format"
        )
    except Exception as e:
        logger.error(f"Failed to send bulk messages: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to send bulk messages"
        )


@router.get("/conversation/{customer_id}")
async def get_conversation_history(
    customer_id: str,
    limit: int = 50,
    whatsapp_service: WhatsAppService = Depends(get_whatsapp_service)
):
    """Get WhatsApp conversation history for a customer."""
    try:
        from uuid import UUID
        customer_uuid = UUID(customer_id)

        messages = await whatsapp_service.get_conversation_history(
            customer_id=customer_uuid,
            limit=limit
        )

        return {
            "customer_id": customer_id,
            "total_messages": len(messages),
            "messages": [
                {
                    "id": str(msg.id),
                    "direction": msg.direction,
                    "message_body": msg.message_body,
                    "status": msg.status,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in messages
            ]
        }

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid customer ID format"
        )
    except Exception as e:
        logger.error(f"Failed to get conversation history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve conversation history"
        )


# Background task functions
async def analyze_message_sentiment(
    message_text: str,
    customer_id: str,
    ai_service: AIService
):
    """Background task to analyze message sentiment."""
    try:
        sentiment_result = await ai_service.analyze_sentiment(
            text=message_text,
            context={"customer_id": customer_id}
        )

        logger.info(f"Sentiment analysis complete for customer {customer_id}: {sentiment_result}")

    except Exception as e:
        logger.error(f"Failed to analyze sentiment: {str(e)}")