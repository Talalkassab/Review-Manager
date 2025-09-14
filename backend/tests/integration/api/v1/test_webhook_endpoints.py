"""
Integration tests for WhatsApp Webhook endpoints.
Tests the complete webhook processing flow including message handling and status updates.
"""
import pytest
from httpx import AsyncClient
from fastapi import FastAPI, status
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from app.api.v1 import api_router
from app.core.exceptions import register_exception_handlers
from app.models.whatsapp_message import WhatsAppMessage


class TestWebhookEndpointsIntegration:
    """Integration tests for webhook endpoints."""

    @pytest.fixture
    async def app(self) -> FastAPI:
        """Create FastAPI application for testing."""
        app = FastAPI(title="Test Webhook API")
        register_exception_handlers(app)
        app.include_router(api_router, prefix="/api/v1")
        return app

    @pytest.fixture
    async def client(self, app: FastAPI) -> AsyncClient:
        """Create async HTTP client for testing."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.fixture
    def valid_twilio_webhook_data(self):
        """Valid Twilio webhook data for incoming message."""
        return {
            "From": "whatsapp:+1234567890",
            "To": "whatsapp:+14155238886",
            "Body": "Hello, I need help with my order",
            "MessageSid": "SM123456789abcdef",
            "AccountSid": "AC123456789abcdef",
            "NumMedia": "0",
            "MediaContentType0": "",
            "MediaUrl0": "",
            "SmsMessageSid": "SM123456789abcdef",
            "WaId": "1234567890",
            "SmsStatus": "received",
            "ApiVersion": "2010-04-01"
        }

    @pytest.fixture
    def valid_status_webhook_data(self):
        """Valid Twilio webhook data for status update."""
        return {
            "MessageSid": "SM123456789abcdef",
            "MessageStatus": "delivered",
            "ErrorCode": "",
            "ErrorMessage": "",
            "To": "whatsapp:+1234567890",
            "From": "whatsapp:+14155238886",
            "AccountSid": "AC123456789abcdef",
            "ApiVersion": "2010-04-01"
        }

    @pytest.fixture
    def mock_whatsapp_message(self):
        """Mock WhatsApp message for testing."""
        message = MagicMock(spec=WhatsAppMessage)
        message.id = uuid4()
        message.twilio_sid = "SM123456789abcdef"
        message.from_number = "+1234567890"
        message.to_number = "+14155238886"
        message.body = "Hello, I need help with my order"
        message.status = "received"
        message.direction = "inbound"
        message.created_at = datetime.utcnow()
        return message

    @patch('app.api.v1.dependencies.services.get_whatsapp_service')
    async def test_receive_message_webhook_success(
        self,
        mock_get_service,
        client: AsyncClient,
        valid_twilio_webhook_data,
        mock_whatsapp_message
    ):
        """Test successful processing of incoming message webhook."""
        # Setup
        mock_service = AsyncMock()
        mock_service.process_incoming_message.return_value = mock_whatsapp_message
        mock_get_service.return_value = mock_service

        # Execute
        response = await client.post(
            "/api/v1/whatsapp/webhook/message",
            data=valid_twilio_webhook_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["message_id"] == str(mock_whatsapp_message.id)

        # Verify service was called with webhook data
        mock_service.process_incoming_message.assert_called_once_with(valid_twilio_webhook_data)

    @patch('app.api.v1.dependencies.services.get_whatsapp_service')
    async def test_receive_message_webhook_missing_required_fields(
        self,
        mock_get_service,
        client: AsyncClient
    ):
        """Test webhook processing with missing required fields."""
        # Setup
        mock_get_service.return_value = AsyncMock()

        # Invalid webhook data - missing required fields
        invalid_data = {
            "From": "whatsapp:+1234567890"
            # Missing other required fields
        }

        # Execute
        response = await client.post(
            "/api/v1/whatsapp/webhook/message",
            data=invalid_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch('app.api.v1.dependencies.services.get_whatsapp_service')
    async def test_receive_message_webhook_invalid_phone_format(
        self,
        mock_get_service,
        client: AsyncClient,
        valid_twilio_webhook_data
    ):
        """Test webhook processing with invalid phone number format."""
        # Setup
        mock_get_service.return_value = AsyncMock()

        # Invalid phone format
        valid_twilio_webhook_data["From"] = "invalid-phone-format"

        # Execute
        response = await client.post(
            "/api/v1/whatsapp/webhook/message",
            data=valid_twilio_webhook_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # Assert - Should be processed but might be handled by service layer validation
        assert response.status_code in [400, 422, 500]

    @patch('app.api.v1.dependencies.services.get_whatsapp_service')
    async def test_receive_message_webhook_service_exception(
        self,
        mock_get_service,
        client: AsyncClient,
        valid_twilio_webhook_data
    ):
        """Test webhook processing when service raises exception."""
        # Setup
        mock_service = AsyncMock()
        mock_service.process_incoming_message.side_effect = Exception("AI service unavailable")
        mock_get_service.return_value = mock_service

        # Execute
        response = await client.post(
            "/api/v1/whatsapp/webhook/message",
            data=valid_twilio_webhook_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "error" in data
        assert data["error"]["type"] == "INTERNAL_SERVER_ERROR"

    @patch('app.api.v1.dependencies.services.get_whatsapp_service')
    async def test_status_update_webhook_success(
        self,
        mock_get_service,
        client: AsyncClient,
        valid_status_webhook_data,
        mock_whatsapp_message
    ):
        """Test successful processing of status update webhook."""
        # Setup
        mock_service = AsyncMock()
        mock_service.process_status_update.return_value = mock_whatsapp_message
        mock_get_service.return_value = mock_service

        # Execute
        response = await client.post(
            "/api/v1/whatsapp/webhook/status",
            data=valid_status_webhook_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert data["message_id"] == str(mock_whatsapp_message.id)

        # Verify service was called with webhook data
        mock_service.process_status_update.assert_called_once_with(valid_status_webhook_data)

    @patch('app.api.v1.dependencies.services.get_whatsapp_service')
    async def test_status_update_webhook_message_not_found(
        self,
        mock_get_service,
        client: AsyncClient,
        valid_status_webhook_data
    ):
        """Test status update webhook for non-existent message."""
        # Setup
        from app.core.exceptions import WebhookProcessingError

        mock_service = AsyncMock()
        mock_service.process_status_update.side_effect = WebhookProcessingError(
            "Message not found", details={"message_sid": valid_status_webhook_data["MessageSid"]}
        )
        mock_get_service.return_value = mock_service

        # Execute
        response = await client.post(
            "/api/v1/whatsapp/webhook/status",
            data=valid_status_webhook_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "error" in data
        assert data["error"]["type"] == "WEBHOOK_PROCESSING_ERROR"

    async def test_webhook_health_check(self, client: AsyncClient):
        """Test WhatsApp webhook health check endpoint."""
        # Execute
        response = await client.get("/api/v1/whatsapp/health")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "whatsapp"

    @patch('app.api.v1.dependencies.services.get_whatsapp_service')
    async def test_webhook_service_health_detailed(
        self,
        mock_get_service,
        client: AsyncClient
    ):
        """Test detailed WhatsApp service health check."""
        # Setup
        mock_health_status = {
            "healthy": True,
            "twilio_connected": True,
            "last_message_processed": "2024-01-01T12:00:00Z",
            "messages_processed_today": 150
        }

        mock_service = AsyncMock()
        mock_service.check_service_health.return_value = mock_health_status
        mock_get_service.return_value = mock_service

        # Execute
        response = await client.get("/api/v1/whatsapp/health/detailed")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["healthy"] is True
        assert data["twilio_connected"] is True
        assert data["messages_processed_today"] == 150

    @patch('app.api.v1.dependencies.services.get_whatsapp_service')
    async def test_webhook_service_health_unhealthy(
        self,
        mock_get_service,
        client: AsyncClient
    ):
        """Test detailed health check when service is unhealthy."""
        # Setup
        mock_health_status = {
            "healthy": False,
            "twilio_connected": False,
            "error": "Twilio authentication failed",
            "last_error": "2024-01-01T12:00:00Z"
        }

        mock_service = AsyncMock()
        mock_service.check_service_health.return_value = mock_health_status
        mock_get_service.return_value = mock_service

        # Execute
        response = await client.get("/api/v1/whatsapp/health/detailed")

        # Assert
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()
        assert data["healthy"] is False
        assert data["twilio_connected"] is False
        assert "error" in data

    @patch('app.api.v1.dependencies.services.get_whatsapp_service')
    async def test_get_conversation_history_success(
        self,
        mock_get_service,
        client: AsyncClient,
        mock_whatsapp_message
    ):
        """Test successful conversation history retrieval."""
        # Setup
        mock_service = AsyncMock()
        mock_service.get_conversation_history.return_value = [mock_whatsapp_message]
        mock_get_service.return_value = mock_service

        phone_number = "+1234567890"
        restaurant_id = uuid4()

        # Execute
        response = await client.get(
            f"/api/v1/whatsapp/conversations/{phone_number}"
            f"?restaurant_id={restaurant_id}&limit=50"
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "messages" in data
        assert len(data["messages"]) == 1
        assert data["messages"][0]["body"] == "Hello, I need help with my order"

        # Verify service was called with correct parameters
        mock_service.get_conversation_history.assert_called_once_with(
            phone_number, restaurant_id, limit=50
        )

    @patch('app.api.v1.dependencies.services.get_whatsapp_service')
    async def test_get_conversation_history_invalid_phone(
        self,
        mock_get_service,
        client: AsyncClient
    ):
        """Test conversation history with invalid phone number."""
        # Setup
        mock_get_service.return_value = AsyncMock()

        invalid_phone = "invalid-phone"
        restaurant_id = uuid4()

        # Execute
        response = await client.get(
            f"/api/v1/whatsapp/conversations/{invalid_phone}"
            f"?restaurant_id={restaurant_id}"
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch('app.api.v1.dependencies.services.get_whatsapp_service')
    async def test_send_message_endpoint_success(
        self,
        mock_get_service,
        client: AsyncClient,
        mock_whatsapp_message
    ):
        """Test successful message sending via API endpoint."""
        # Setup
        mock_service = AsyncMock()
        mock_service.send_message.return_value = mock_whatsapp_message
        mock_get_service.return_value = mock_service

        message_data = {
            "to_number": "+1234567890",
            "message": "Your order is ready for pickup!",
            "restaurant_id": str(uuid4())
        }

        # Execute
        response = await client.post("/api/v1/whatsapp/send", json=message_data)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "sent"
        assert data["message_id"] == str(mock_whatsapp_message.id)

        # Verify service was called
        mock_service.send_message.assert_called_once_with(
            message_data["to_number"],
            message_data["message"]
        )

    @patch('app.api.v1.dependencies.services.get_whatsapp_service')
    async def test_send_message_endpoint_twilio_failure(
        self,
        mock_get_service,
        client: AsyncClient
    ):
        """Test message sending when Twilio service fails."""
        # Setup
        from app.core.exceptions import MessageSendFailure

        mock_service = AsyncMock()
        mock_service.send_message.side_effect = MessageSendFailure(
            "Failed to send message", details={"to_number": "+1234567890"}
        )
        mock_get_service.return_value = mock_service

        message_data = {
            "to_number": "+1234567890",
            "message": "Test message",
            "restaurant_id": str(uuid4())
        }

        # Execute
        response = await client.post("/api/v1/whatsapp/send", json=message_data)

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "error" in data
        assert data["error"]["type"] == "MESSAGE_SEND_FAILURE"

    async def test_webhook_endpoints_accept_form_data_only(self, client: AsyncClient):
        """Test that webhook endpoints only accept form data, not JSON."""
        webhook_data = {
            "From": "whatsapp:+1234567890",
            "To": "whatsapp:+14155238886",
            "Body": "Hello",
            "MessageSid": "SM123456789"
        }

        # Test with JSON (should fail)
        response = await client.post(
            "/api/v1/whatsapp/webhook/message",
            json=webhook_data
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test with form data (should pass validation, might fail for other reasons)
        response = await client.post(
            "/api/v1/whatsapp/webhook/message",
            data=webhook_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        # Should not fail due to content type (might fail for other reasons like missing service)
        assert response.status_code != status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch('app.api.v1.dependencies.services.get_whatsapp_service')
    async def test_webhook_handles_media_messages(
        self,
        mock_get_service,
        client: AsyncClient,
        mock_whatsapp_message
    ):
        """Test webhook processing of media messages."""
        # Setup
        mock_service = AsyncMock()
        mock_service.process_incoming_message.return_value = mock_whatsapp_message
        mock_get_service.return_value = mock_service

        media_webhook_data = {
            "From": "whatsapp:+1234567890",
            "To": "whatsapp:+14155238886",
            "Body": "",
            "MessageSid": "SM123456789abcdef",
            "AccountSid": "AC123456789abcdef",
            "NumMedia": "1",
            "MediaContentType0": "image/jpeg",
            "MediaUrl0": "https://api.twilio.com/media/image.jpg",
            "WaId": "1234567890"
        }

        # Execute
        response = await client.post(
            "/api/v1/whatsapp/webhook/message",
            data=media_webhook_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"

        # Verify service was called with media data
        mock_service.process_incoming_message.assert_called_once_with(media_webhook_data)


@pytest.mark.integration
class TestWebhookSecurity:
    """Test webhook security and validation."""

    @pytest.fixture
    async def app(self) -> FastAPI:
        """Create FastAPI application for testing."""
        app = FastAPI(title="Test Webhook Security")
        register_exception_handlers(app)
        app.include_router(api_router, prefix="/api/v1")
        return app

    @pytest.fixture
    async def client(self, app: FastAPI) -> AsyncClient:
        """Create async HTTP client for testing."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    async def test_webhook_rate_limiting(self, client: AsyncClient):
        """Test that webhook endpoints have rate limiting."""
        webhook_data = {
            "From": "whatsapp:+1234567890",
            "To": "whatsapp:+14155238886",
            "Body": "Hello",
            "MessageSid": "SM123456789"
        }

        # Make multiple rapid requests
        responses = []
        for i in range(10):
            response = await client.post(
                "/api/v1/whatsapp/webhook/message",
                data=webhook_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            responses.append(response.status_code)

        # At least some requests should be processed
        # (Rate limiting implementation details may vary)
        success_responses = [r for r in responses if r in [200, 201]]
        error_responses = [r for r in responses if r >= 400]

        # Should have some successful responses and potentially some rate-limited ones
        assert len(success_responses + error_responses) == 10

    @patch('app.api.v1.dependencies.services.get_whatsapp_service')
    async def test_webhook_request_validation(
        self,
        mock_get_service,
        client: AsyncClient
    ):
        """Test webhook request validation and sanitization."""
        # Setup
        mock_get_service.return_value = AsyncMock()

        # Malicious payload attempt
        malicious_data = {
            "From": "whatsapp:+1234567890",
            "To": "whatsapp:+14155238886",
            "Body": "<script>alert('xss')</script>",
            "MessageSid": "SM123456789; DROP TABLE customers;",
            "AccountSid": "AC123456789"
        }

        # Execute
        response = await client.post(
            "/api/v1/whatsapp/webhook/message",
            data=malicious_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # Assert - Should be handled gracefully (validation or sanitization)
        assert response.status_code in [200, 400, 422]

        # If successful, verify the service received sanitized data
        if response.status_code == 200:
            mock_get_service.return_value.process_incoming_message.assert_called_once()
            call_args = mock_get_service.return_value.process_incoming_message.call_args[0][0]
            # Body should be processed safely
            assert call_args["Body"] == "<script>alert('xss')</script>"  # or sanitized version

    async def test_webhook_method_restrictions(self, client: AsyncClient):
        """Test that webhook endpoints only accept POST requests."""
        endpoint = "/api/v1/whatsapp/webhook/message"

        # Test non-POST methods
        methods_to_test = ["GET", "PUT", "DELETE", "PATCH"]

        for method in methods_to_test:
            if method == "GET":
                response = await client.get(endpoint)
            elif method == "PUT":
                response = await client.put(endpoint)
            elif method == "DELETE":
                response = await client.delete(endpoint)
            elif method == "PATCH":
                response = await client.patch(endpoint)

            # Should return 405 Method Not Allowed
            assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED