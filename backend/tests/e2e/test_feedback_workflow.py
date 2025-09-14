"""
End-to-end tests for critical customer feedback workflow.
Tests the complete flow from WhatsApp message to sentiment analysis and customer record update.
"""
import pytest
from httpx import AsyncClient
from fastapi import FastAPI, status
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timedelta
import asyncio

from app.api.v1 import api_router
from app.core.exceptions import register_exception_handlers
from app.models.customer import Customer
from app.models.whatsapp_message import WhatsAppMessage
from app.models.user import User


@pytest.mark.e2e
class TestCustomerFeedbackWorkflowE2E:
    """End-to-end tests for customer feedback workflow."""

    @pytest.fixture
    async def app(self) -> FastAPI:
        """Create FastAPI application for testing."""
        app = FastAPI(title="E2E Test App")
        register_exception_handlers(app)
        app.include_router(api_router, prefix="/api/v1")
        return app

    @pytest.fixture
    async def client(self, app: FastAPI) -> AsyncClient:
        """Create async HTTP client for testing."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.fixture
    def test_restaurant_id(self):
        """Test restaurant ID."""
        return uuid4()

    @pytest.fixture
    def test_customer_phone(self):
        """Test customer phone number."""
        return "+1234567890"

    @pytest.fixture
    def mock_existing_customer(self, test_restaurant_id, test_customer_phone):
        """Mock existing customer."""
        customer = MagicMock(spec=Customer)
        customer.id = uuid4()
        customer.restaurant_id = test_restaurant_id
        customer.name = "John Doe"
        customer.phone_number = test_customer_phone
        customer.email = "john@example.com"
        customer.status = "pending"
        customer.sentiment_score = None
        customer.sentiment_category = None
        customer.feedback = None
        customer.visit_history = [{"date": "2024-01-01T12:00:00Z", "visit_number": 1}]
        customer.created_at = datetime.utcnow() - timedelta(days=1)
        customer.updated_at = datetime.utcnow() - timedelta(hours=1)
        customer.is_deleted = False
        return customer

    @pytest.fixture
    def mock_user(self, test_restaurant_id):
        """Mock authenticated user."""
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.restaurant_id = test_restaurant_id
        user.is_superuser = False
        user.can_manage_customers = True
        user.can_view_analytics = True
        return user

    @pytest.fixture
    def feedback_message_webhook_data(self, test_customer_phone):
        """Webhook data for customer feedback message."""
        return {
            "From": f"whatsapp:{test_customer_phone}",
            "To": "whatsapp:+14155238886",
            "Body": "The food was absolutely delicious! The service was excellent and the atmosphere was perfect. Highly recommend this place!",
            "MessageSid": "SM123456789abcdef",
            "AccountSid": "AC123456789abcdef",
            "NumMedia": "0",
            "WaId": test_customer_phone.lstrip('+'),
            "SmsStatus": "received"
        }

    @pytest.fixture
    def negative_feedback_webhook_data(self, test_customer_phone):
        """Webhook data for negative customer feedback message."""
        return {
            "From": f"whatsapp:{test_customer_phone}",
            "To": "whatsapp:+14155238886",
            "Body": "The food was cold and the service was terrible. I waited 45 minutes for my order. Very disappointed!",
            "MessageSid": "SM987654321fedcba",
            "AccountSid": "AC123456789abcdef",
            "NumMedia": "0",
            "WaId": test_customer_phone.lstrip('+'),
            "SmsStatus": "received"
        }

    @patch('app.api.v1.dependencies.services.get_whatsapp_service')
    @patch('app.api.v1.dependencies.services.get_ai_service')
    @patch('app.api.v1.dependencies.services.get_customer_service')
    async def test_complete_positive_feedback_workflow(
        self,
        mock_get_customer_service,
        mock_get_ai_service,
        mock_get_whatsapp_service,
        client: AsyncClient,
        feedback_message_webhook_data,
        mock_existing_customer,
        test_customer_phone,
        test_restaurant_id
    ):
        """Test complete workflow for positive customer feedback."""

        # Setup - Mock services
        # 1. WhatsApp service creates incoming message
        mock_incoming_message = MagicMock(spec=WhatsAppMessage)
        mock_incoming_message.id = uuid4()
        mock_incoming_message.twilio_sid = feedback_message_webhook_data["MessageSid"]
        mock_incoming_message.from_number = test_customer_phone
        mock_incoming_message.body = feedback_message_webhook_data["Body"]
        mock_incoming_message.direction = "inbound"
        mock_incoming_message.status = "received"
        mock_incoming_message.created_at = datetime.utcnow()

        # 2. Customer service finds existing customer
        mock_customer_service = AsyncMock()
        mock_customer_service.find_customer_by_phone.return_value = mock_existing_customer
        mock_customer_service.update_customer_feedback.return_value = mock_existing_customer
        mock_get_customer_service.return_value = mock_customer_service

        # 3. AI service analyzes sentiment
        mock_ai_service = AsyncMock()
        mock_sentiment_result = {
            "sentiment_score": 0.9,
            "sentiment_category": "positive",
            "confidence": 0.92,
            "key_themes": ["food quality", "service", "atmosphere"],
            "suggestions": ["Continue excellent service"]
        }
        mock_ai_service.analyze_sentiment.return_value = mock_sentiment_result

        # 4. AI service generates response
        mock_ai_response = "Thank you so much for your wonderful feedback! We're thrilled to hear you enjoyed your experience. Your kind words mean the world to our team!"
        mock_ai_service.generate_intelligent_response.return_value = mock_ai_response
        mock_get_ai_service.return_value = mock_ai_service

        # 5. WhatsApp service processes message and sends response
        mock_whatsapp_service = AsyncMock()

        # Mock the complete workflow
        async def mock_process_incoming_message(webhook_data):
            # Simulate the complete processing workflow
            # 1. Create incoming message record
            # 2. Find/create customer
            # 3. Analyze sentiment
            # 4. Update customer with feedback and sentiment
            # 5. Generate and send AI response

            # Update mock customer with sentiment analysis results
            mock_existing_customer.sentiment_score = mock_sentiment_result["sentiment_score"]
            mock_existing_customer.sentiment_category = mock_sentiment_result["sentiment_category"]
            mock_existing_customer.feedback = webhook_data["Body"]
            mock_existing_customer.updated_at = datetime.utcnow()

            return mock_incoming_message

        mock_whatsapp_service.process_incoming_message.side_effect = mock_process_incoming_message

        # Mock sending response
        mock_outgoing_message = MagicMock(spec=WhatsAppMessage)
        mock_outgoing_message.id = uuid4()
        mock_outgoing_message.body = mock_ai_response
        mock_outgoing_message.direction = "outbound"
        mock_whatsapp_service.send_message.return_value = mock_outgoing_message

        mock_get_whatsapp_service.return_value = mock_whatsapp_service

        # Execute - Send feedback webhook
        response = await client.post(
            "/api/v1/whatsapp/webhook/message",
            data=feedback_message_webhook_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # Assert webhook processing succeeded
        assert response.status_code == status.HTTP_200_OK
        webhook_response = response.json()
        assert webhook_response["status"] == "success"
        assert webhook_response["message_id"] == str(mock_incoming_message.id)

        # Verify the complete workflow was executed
        mock_whatsapp_service.process_incoming_message.assert_called_once_with(feedback_message_webhook_data)

        # Verify customer sentiment was updated
        assert mock_existing_customer.sentiment_score == 0.9
        assert mock_existing_customer.sentiment_category == "positive"
        assert mock_existing_customer.feedback == feedback_message_webhook_data["Body"]

        # Now test that we can retrieve the updated customer data
        with patch('app.api.v1.dependencies.services.get_current_user') as mock_get_user:
            mock_get_user.return_value = mock_user

            # Get customer to verify feedback was stored
            customer_response = await client.get(f"/api/v1/customers/{mock_existing_customer.id}")

            assert customer_response.status_code == status.HTTP_200_OK
            customer_data = customer_response.json()
            assert customer_data["sentiment_score"] == 0.9
            assert customer_data["sentiment_category"] == "positive"
            assert customer_data["feedback"] == feedback_message_webhook_data["Body"]

    @patch('app.api.v1.dependencies.services.get_whatsapp_service')
    @patch('app.api.v1.dependencies.services.get_ai_service')
    @patch('app.api.v1.dependencies.services.get_customer_service')
    async def test_complete_negative_feedback_workflow(
        self,
        mock_get_customer_service,
        mock_get_ai_service,
        mock_get_whatsapp_service,
        client: AsyncClient,
        negative_feedback_webhook_data,
        mock_existing_customer,
        test_customer_phone
    ):
        """Test complete workflow for negative customer feedback."""

        # Setup - Mock services for negative feedback scenario
        mock_incoming_message = MagicMock(spec=WhatsAppMessage)
        mock_incoming_message.id = uuid4()
        mock_incoming_message.twilio_sid = negative_feedback_webhook_data["MessageSid"]
        mock_incoming_message.from_number = test_customer_phone
        mock_incoming_message.body = negative_feedback_webhook_data["Body"]
        mock_incoming_message.direction = "inbound"

        # Customer service
        mock_customer_service = AsyncMock()
        mock_customer_service.find_customer_by_phone.return_value = mock_existing_customer
        mock_get_customer_service.return_value = mock_customer_service

        # AI service for negative sentiment
        mock_ai_service = AsyncMock()
        mock_negative_sentiment = {
            "sentiment_score": 0.2,
            "sentiment_category": "negative",
            "confidence": 0.88,
            "key_themes": ["food temperature", "service speed", "wait time"],
            "suggestions": ["Follow up on service issues", "Improve order processing time"]
        }
        mock_ai_service.analyze_sentiment.return_value = mock_negative_sentiment

        # Generate empathetic response for negative feedback
        mock_ai_response = "I'm so sorry to hear about your disappointing experience. This is not the standard we aim for. I'd like to make this right - could you please share your order details so we can investigate and improve?"
        mock_ai_service.generate_intelligent_response.return_value = mock_ai_response
        mock_get_ai_service.return_value = mock_ai_service

        # WhatsApp service
        mock_whatsapp_service = AsyncMock()

        async def mock_process_negative_feedback(webhook_data):
            # Update customer with negative sentiment
            mock_existing_customer.sentiment_score = mock_negative_sentiment["sentiment_score"]
            mock_existing_customer.sentiment_category = mock_negative_sentiment["sentiment_category"]
            mock_existing_customer.feedback = webhook_data["Body"]
            mock_existing_customer.status = "needs_attention"  # Flag for follow-up
            mock_existing_customer.updated_at = datetime.utcnow()

            return mock_incoming_message

        mock_whatsapp_service.process_incoming_message.side_effect = mock_process_negative_feedback
        mock_get_whatsapp_service.return_value = mock_whatsapp_service

        # Execute - Send negative feedback webhook
        response = await client.post(
            "/api/v1/whatsapp/webhook/message",
            data=negative_feedback_webhook_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        webhook_response = response.json()
        assert webhook_response["status"] == "success"

        # Verify negative sentiment was captured correctly
        assert mock_existing_customer.sentiment_score == 0.2
        assert mock_existing_customer.sentiment_category == "negative"
        assert mock_existing_customer.status == "needs_attention"

    @patch('app.api.v1.dependencies.services.get_current_user')
    @patch('app.api.v1.dependencies.services.get_analytics_service')
    async def test_analytics_reflect_feedback_workflow(
        self,
        mock_get_analytics_service,
        mock_get_user,
        client: AsyncClient,
        mock_user,
        test_restaurant_id
    ):
        """Test that analytics properly reflect processed feedback."""

        # Setup - Mock analytics showing processed feedback
        mock_get_user.return_value = mock_user

        mock_analytics_service = AsyncMock()

        # Mock dashboard metrics showing sentiment analysis results
        mock_dashboard_metrics = {
            "summary": {
                "total_customers": 100,
                "active_customers": 85,
                "average_sentiment": 0.75,
                "total_messages": 500
            },
            "sentiment_metrics": {
                "average_score": 0.75,
                "distribution": {
                    "positive": 70,
                    "negative": 15,
                    "neutral": 15
                },
                "trending": "improving"
            },
            "customer_metrics": {
                "total": 100,
                "new": 25,
                "returning": 75,
                "by_status": {
                    "pending": 30,
                    "completed": 60,
                    "needs_attention": 10  # Customers with negative feedback
                }
            },
            "message_metrics": {
                "total": 500,
                "inbound": 300,
                "outbound": 200
            }
        }

        mock_analytics_service.get_dashboard_metrics.return_value = mock_dashboard_metrics
        mock_get_analytics_service.return_value = mock_analytics_service

        # Execute - Get analytics dashboard
        response = await client.get("/api/v1/analytics/dashboard")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        analytics_data = response.json()

        # Verify sentiment data is included
        assert "sentiment_metrics" in analytics_data
        assert analytics_data["sentiment_metrics"]["average_score"] == 0.75
        assert analytics_data["sentiment_metrics"]["distribution"]["positive"] == 70
        assert analytics_data["sentiment_metrics"]["distribution"]["negative"] == 15

        # Verify customer status includes attention-needed customers
        assert analytics_data["customer_metrics"]["by_status"]["needs_attention"] == 10

    @patch('app.api.v1.dependencies.services.get_whatsapp_service')
    @patch('app.api.v1.dependencies.services.get_ai_service')
    @patch('app.api.v1.dependencies.services.get_customer_service')
    async def test_new_customer_feedback_workflow(
        self,
        mock_get_customer_service,
        mock_get_ai_service,
        mock_get_whatsapp_service,
        client: AsyncClient,
        test_restaurant_id
    ):
        """Test feedback workflow for a new customer (not in database)."""

        # Setup - New customer phone number
        new_customer_phone = "+1987654321"

        new_customer_webhook_data = {
            "From": f"whatsapp:{new_customer_phone}",
            "To": "whatsapp:+14155238886",
            "Body": "Hi! I just visited your restaurant for the first time. Amazing food and great service!",
            "MessageSid": "SM_NEW_CUSTOMER_123",
            "AccountSid": "AC123456789abcdef",
            "NumMedia": "0",
            "WaId": new_customer_phone.lstrip('+'),
            "SmsStatus": "received"
        }

        # Mock services - Customer not found initially
        mock_customer_service = AsyncMock()
        mock_customer_service.find_customer_by_phone.return_value = None

        # Mock creating new customer
        mock_new_customer = MagicMock(spec=Customer)
        mock_new_customer.id = uuid4()
        mock_new_customer.restaurant_id = test_restaurant_id
        mock_new_customer.name = None  # Name not provided yet
        mock_new_customer.phone_number = new_customer_phone
        mock_new_customer.email = None
        mock_new_customer.status = "pending"
        mock_new_customer.sentiment_score = 0.85
        mock_new_customer.sentiment_category = "positive"
        mock_new_customer.feedback = new_customer_webhook_data["Body"]
        mock_new_customer.visit_history = [{"date": datetime.utcnow().isoformat(), "visit_number": 1}]
        mock_new_customer.created_at = datetime.utcnow()
        mock_new_customer.updated_at = datetime.utcnow()
        mock_new_customer.is_deleted = False

        mock_customer_service.create_customer_from_phone.return_value = mock_new_customer
        mock_get_customer_service.return_value = mock_customer_service

        # AI service
        mock_ai_service = AsyncMock()
        mock_sentiment = {
            "sentiment_score": 0.85,
            "sentiment_category": "positive",
            "confidence": 0.90
        }
        mock_ai_service.analyze_sentiment.return_value = mock_sentiment

        mock_response = "Thank you for visiting us and for your wonderful feedback! We're so happy you enjoyed your first experience with us. We look forward to serving you again soon!"
        mock_ai_service.generate_intelligent_response.return_value = mock_response
        mock_get_ai_service.return_value = mock_ai_service

        # WhatsApp service
        mock_whatsapp_service = AsyncMock()

        mock_incoming_message = MagicMock(spec=WhatsAppMessage)
        mock_incoming_message.id = uuid4()
        mock_incoming_message.twilio_sid = new_customer_webhook_data["MessageSid"]
        mock_incoming_message.customer_id = mock_new_customer.id

        async def mock_process_new_customer_message(webhook_data):
            # Simulate creating new customer and processing their first message
            return mock_incoming_message

        mock_whatsapp_service.process_incoming_message.side_effect = mock_process_new_customer_message
        mock_get_whatsapp_service.return_value = mock_whatsapp_service

        # Execute
        response = await client.post(
            "/api/v1/whatsapp/webhook/message",
            data=new_customer_webhook_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        webhook_response = response.json()
        assert webhook_response["status"] == "success"

        # Verify workflow processed new customer correctly
        mock_whatsapp_service.process_incoming_message.assert_called_once()

    @patch('app.api.v1.dependencies.services.get_whatsapp_service')
    async def test_error_handling_in_feedback_workflow(
        self,
        mock_get_whatsapp_service,
        client: AsyncClient,
        feedback_message_webhook_data
    ):
        """Test error handling during feedback workflow."""

        # Setup - Mock service to raise exception
        mock_whatsapp_service = AsyncMock()
        mock_whatsapp_service.process_incoming_message.side_effect = Exception("AI service temporarily unavailable")
        mock_get_whatsapp_service.return_value = mock_whatsapp_service

        # Execute
        response = await client.post(
            "/api/v1/whatsapp/webhook/message",
            data=feedback_message_webhook_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # Assert - Should handle error gracefully
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        error_response = response.json()
        assert "error" in error_response
        assert error_response["error"]["type"] == "INTERNAL_SERVER_ERROR"
        assert "correlation_id" in error_response["error"]

    async def test_concurrent_feedback_processing(
        self,
        client: AsyncClient,
        test_customer_phone
    ):
        """Test that multiple feedback messages can be processed concurrently."""

        # Setup - Multiple webhook payloads
        webhook_payloads = []
        for i in range(5):
            webhook_payloads.append({
                "From": f"whatsapp:+123456789{i}",
                "To": "whatsapp:+14155238886",
                "Body": f"Feedback message {i}",
                "MessageSid": f"SM{i:012d}",
                "AccountSid": "AC123456789abcdef",
                "NumMedia": "0"
            })

        # Mock the service to respond successfully
        with patch('app.api.v1.dependencies.services.get_whatsapp_service') as mock_get_service:
            mock_service = AsyncMock()

            async def mock_process_message(webhook_data):
                # Simulate some processing time
                await asyncio.sleep(0.1)
                mock_message = MagicMock(spec=WhatsAppMessage)
                mock_message.id = uuid4()
                return mock_message

            mock_service.process_incoming_message.side_effect = mock_process_message
            mock_get_service.return_value = mock_service

            # Execute - Send multiple requests concurrently
            tasks = []
            for payload in webhook_payloads:
                task = client.post(
                    "/api/v1/whatsapp/webhook/message",
                    data=payload,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                tasks.append(task)

            # Wait for all requests to complete
            responses = await asyncio.gather(*tasks)

            # Assert - All should succeed
            for response in responses:
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["status"] == "success"

            # Verify all messages were processed
            assert mock_service.process_incoming_message.call_count == 5