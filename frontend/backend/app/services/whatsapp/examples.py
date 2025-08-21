"""
WhatsApp Service Usage Examples

This file provides comprehensive examples of how to use the WhatsApp service
for various restaurant business scenarios.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.models.whatsapp import MessageType, Priority

from .service import WhatsAppService
from .bulk_messaging import (
    CampaignType, CampaignTarget, CampaignMessage, SegmentCriteria
)


async def basic_messaging_example(db: Session):
    """Basic message sending examples."""
    
    # Initialize WhatsApp service
    whatsapp_service = WhatsAppService(db)
    await whatsapp_service.initialize()
    
    try:
        # Get a customer from database
        customer = db.query(Customer).first()
        if not customer:
            print("No customers found in database")
            return
        
        # Send a welcome message
        print("Sending welcome message...")
        message = await whatsapp_service.send_welcome_message(
            customer=customer,
            restaurant_name="مطعم الأصالة"
        )
        print(f"Welcome message sent: {message}")
        
        # Send a text message
        print("Sending text message...")
        text_message = await whatsapp_service.send_text_message(
            phone_number=customer.phone,
            message="مرحباً! كيف يمكنني مساعدتك اليوم؟",
            customer_id=customer.id,
            priority=Priority.HIGH
        )
        print(f"Text message sent: {text_message}")
        
        # Send order confirmation
        print("Sending order confirmation...")
        order_items = [
            {"name": "برجر لحم", "quantity": 2, "price": 25.50},
            {"name": "بطاطس مقلية", "quantity": 1, "price": 12.00},
            {"name": "عصير برتقال", "quantity": 2, "price": 8.00}
        ]
        
        confirmation = await whatsapp_service.send_order_confirmation(
            customer=customer,
            order_number="ORD-2024-001",
            items=order_items,
            total_amount=71.00,
            currency="SAR"
        )
        print(f"Order confirmation sent: {confirmation}")
        
        # Send delivery update
        print("Sending delivery update...")
        delivery_update = await whatsapp_service.send_delivery_update(
            customer=customer,
            order_number="ORD-2024-001",
            status="جاري التحضير",
            estimated_time="20-25 دقيقة"
        )
        print(f"Delivery update sent: {delivery_update}")
        
    finally:
        await whatsapp_service.shutdown()


async def template_management_example(db: Session):
    """Template management examples."""
    
    whatsapp_service = WhatsAppService(db)
    await whatsapp_service.initialize()
    
    try:
        # Create a custom template
        template_data = {
            "name": "custom_promotion_ar",
            "language": "ar",
            "category": "MARKETING",
            "header_text": "عرض خاص! 🎉",
            "body_text": "مرحباً {{1}}!\n\nلدينا عرض خاص لك: {{2}}\n\nاستخدم كود الخصم: {{3}}\nساري حتى: {{4}}",
            "footer_text": "مطعم الأصالة - نقدم لك الأفضل دائماً",
            "parameters": [
                {"name": "customer_name", "type": "TEXT", "example": "أحمد", "component": "BODY", "index": 1},
                {"name": "offer_details", "type": "TEXT", "example": "خصم 20% على جميع الوجبات", "component": "BODY", "index": 2},
                {"name": "promo_code", "type": "TEXT", "example": "SAVE20", "component": "BODY", "index": 3},
                {"name": "expiry_date", "type": "TEXT", "example": "31 ديسمبر 2024", "component": "BODY", "index": 4}
            ]
        }
        
        template = await whatsapp_service.create_template(template_data)
        print(f"Template created: {template.name}")
        
        # List available templates
        templates = await whatsapp_service.list_templates(language="ar")
        print(f"Available Arabic templates: {len(templates)}")
        for template in templates[:5]:  # Show first 5
            print(f"  - {template.name} ({template.status})")
        
        # Sync templates from WhatsApp
        sync_results = await whatsapp_service.sync_templates_from_whatsapp()
        print(f"Template sync results: {sync_results}")
        
    finally:
        await whatsapp_service.shutdown()


async def media_handling_example(db: Session):
    """Media handling examples."""
    
    whatsapp_service = WhatsAppService(db)
    await whatsapp_service.initialize()
    
    try:
        # Upload menu image
        print("Uploading menu image...")
        # Note: You need to have an actual image file for this to work
        # upload_result = await whatsapp_service.upload_media(
        #     file_path="path/to/menu.jpg",
        #     media_type="image/jpeg",
        #     optimize=True
        # )
        # print(f"Media uploaded: {upload_result}")
        
        # Send media message (using a placeholder URL)
        customer = db.query(Customer).first()
        if customer:
            media_message = await whatsapp_service.send_media_message(
                phone_number=customer.phone,
                media_url="https://example.com/menu.jpg",
                media_type=MessageType.IMAGE,
                customer_id=customer.id,
                caption="قائمة طعامنا الجديدة! 🍽️"
            )
            print(f"Media message sent: {media_message}")
        
    finally:
        await whatsapp_service.shutdown()


async def bulk_messaging_example(db: Session):
    """Bulk messaging and campaign examples."""
    
    whatsapp_service = WhatsAppService(db)
    await whatsapp_service.initialize()
    
    try:
        # Create campaign targeting configuration
        target = CampaignTarget(
            segment_criteria=SegmentCriteria.LANGUAGE,
            include_filters={"languages": ["ar"]},
            max_recipients=100,
            test_recipients=["+966501234567"]  # Add test numbers
        )
        
        # Create campaign message
        message = CampaignMessage(
            message_type=MessageType.TEXT,
            content="عرض خاص! خصم 25% على جميع الوجبات اليوم فقط! 🎉\n\nاطلب الآن واستمتع بأشهى الأطباق بأفضل الأسعار.\n\nصالح حتى نهاية اليوم.",
            personalization_enabled=True
        )
        
        # Create promotional campaign
        campaign_id = await whatsapp_service.create_campaign(
            name="عرض خاص - خصم 25%",
            description="حملة ترويجية لعرض خصم 25% على جميع الوجبات",
            campaign_type=CampaignType.PROMOTIONAL,
            target=target,
            message=message,
            messages_per_minute=30,  # Conservative rate
            priority=Priority.NORMAL
        )
        
        print(f"Campaign created with ID: {campaign_id}")
        
        # Launch campaign in test mode
        launch_result = await whatsapp_service.launch_campaign(
            campaign_id, test_mode=True
        )
        print(f"Campaign launched: {launch_result}")
        
        # Monitor campaign progress
        await asyncio.sleep(5)  # Wait a bit
        status = await whatsapp_service.get_campaign_status(campaign_id)
        print(f"Campaign status: {status}")
        
    finally:
        await whatsapp_service.shutdown()


async def webhook_example():
    """Example of webhook processing setup."""
    from fastapi import FastAPI, Request, HTTPException
    
    app = FastAPI()
    
    # This would be initialized once per application
    whatsapp_service = None
    
    @app.on_event("startup")
    async def startup():
        global whatsapp_service
        # db = get_database_session()  # Your DB session factory
        # whatsapp_service = WhatsAppService(db)
        # await whatsapp_service.initialize()
        pass
    
    @app.on_event("shutdown")
    async def shutdown():
        if whatsapp_service:
            await whatsapp_service.shutdown()
    
    @app.get("/webhook")
    async def verify_webhook(
        hub_mode: str = None,
        hub_verify_token: str = None,
        hub_challenge: str = None
    ):
        """Webhook verification endpoint."""
        verify_token = "your_verify_token"
        
        if hub_mode == "subscribe" and hub_verify_token == verify_token:
            return int(hub_challenge)
        else:
            raise HTTPException(status_code=403, detail="Forbidden")
    
    @app.post("/webhook")
    async def process_webhook(request: Request):
        """Webhook processing endpoint."""
        if not whatsapp_service:
            raise HTTPException(status_code=500, detail="Service not initialized")
        
        try:
            result = await whatsapp_service.process_webhook(
                request, validate_signature=True
            )
            return {"status": "success", "result": result}
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    return app


def analytics_example(db: Session):
    """Analytics and reporting examples."""
    
    whatsapp_service = WhatsAppService(db)
    
    # Get message statistics for last 30 days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    stats = whatsapp_service.get_message_statistics(
        start_date=start_date,
        end_date=end_date,
        filters={"message_type": MessageType.TEXT}
    )
    
    print("Message Statistics (Last 30 Days):")
    print(f"Total Messages: {stats['totals']['total_messages']}")
    print(f"Delivery Rate: {stats['rates']['delivery_rate']:.2f}%")
    print(f"Read Rate: {stats['rates']['read_rate']:.2f}%")
    print(f"Failure Rate: {stats['rates']['failure_rate']:.2f}%")
    
    # Get service health
    health = whatsapp_service.get_service_health()
    print(f"\nService Health: {health['service_status']}")
    print(f"Components Status: {health['components']}")


async def advanced_features_example(db: Session):
    """Advanced features demonstration."""
    
    whatsapp_service = WhatsAppService(db)
    await whatsapp_service.initialize()
    
    try:
        # Custom webhook event handler
        def handle_message_read(event_data):
            message = event_data.get('message')
            print(f"Message {message.id} was read by customer")
        
        # Register custom event handler
        from .webhook import WebhookEventType
        whatsapp_service.register_webhook_handler(
            WebhookEventType.STATUS, handle_message_read
        )
        
        # Create interactive message with quick replies
        customer = db.query(Customer).first()
        if customer:
            # This would require implementing interactive message support
            # in the main client, which is already included in the client.py
            pass
        
        # Batch message sending with different priorities
        customers = db.query(Customer).limit(5).all()
        
        for i, customer in enumerate(customers):
            priority = Priority.HIGH if i < 2 else Priority.NORMAL
            
            await whatsapp_service.send_text_message(
                phone_number=customer.phone,
                message=f"رسالة اختبار رقم {i+1}",
                customer_id=customer.id,
                priority=priority,
                use_async=True  # Use async queue
            )
        
        print(f"Sent {len(customers)} messages to async queue")
        
    finally:
        await whatsapp_service.shutdown()


async def run_examples():
    """Run all examples (for demonstration purposes)."""
    
    # Note: You'll need to provide a proper database session
    # db = get_your_database_session()
    
    print("WhatsApp Service Examples")
    print("=" * 50)
    
    # Uncomment the examples you want to run:
    
    # print("\n1. Basic Messaging Example")
    # await basic_messaging_example(db)
    
    # print("\n2. Template Management Example")
    # await template_management_example(db)
    
    # print("\n3. Media Handling Example")  
    # await media_handling_example(db)
    
    # print("\n4. Bulk Messaging Example")
    # await bulk_messaging_example(db)
    
    # print("\n5. Analytics Example")
    # analytics_example(db)
    
    # print("\n6. Advanced Features Example")
    # await advanced_features_example(db)
    
    print("\nExamples completed!")


if __name__ == "__main__":
    # Run examples if script is executed directly
    asyncio.run(run_examples())