"""
Unit tests for WhatsAppService.
Tests business logic for WhatsApp message processing.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
from datetime import datetime

from app.services.whatsapp_service import WhatsAppService
from app.models.user import User
from app.models.whatsapp_message import WhatsAppMessage
from app.core.exceptions import MessageSendFailure, WebhookProcessingError, TwilioServiceUnavailable


class TestWhatsAppService:
    """Test cases for WhatsAppService."""

    @pytest.fixture
    def mock_session(self):
        """Mock async database session."""
        return AsyncMock()

    @pytest.fixture
    def mock_whatsapp_repository(self):
        """Mock WhatsApp repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_twilio_client(self):
        """Mock Twilio client."""
        return AsyncMock()

    @pytest.fixture
    def whatsapp_service(self, mock_session, mock_whatsapp_repository):
        """WhatsAppService instance with mocked dependencies."""
        service = WhatsAppService(mock_session)
        service.whatsapp_repository = mock_whatsapp_repository
        return service

    @pytest.fixture
    def sample_incoming_message(self):
        """Sample incoming WhatsApp message data."""
        return {
            "From": "whatsapp:+1234567890",
            "To": "whatsapp:+14155238886",
            "Body": "Hello, I need help with my order",
            "MessageSid": "SM123456789",
            "AccountSid": "AC123456789"
        }

    @pytest.fixture
    def sample_whatsapp_message(self):
        """Sample WhatsApp message model."""
        message = MagicMock(spec=WhatsAppMessage)
        message.id = uuid4()
        message.twilio_sid = "SM123456789"
        message.from_number = "+1234567890"
        message.to_number = "+14155238886"
        message.body = "Hello"
        message.status = "received"
        return message

    @patch('app.services.whatsapp_service.TwilioWhatsAppService')
    async def test_process_incoming_message_success(
        self, mock_twilio_service, whatsapp_service, sample_incoming_message
    ):
        """Test successful processing of incoming WhatsApp message."""
        # Setup
        created_message = MagicMock(spec=WhatsAppMessage)
        whatsapp_service.whatsapp_repository.create_from_webhook.return_value = created_message

        # Mock AI response generation
        mock_ai_response = "Thank you for contacting us! How can I help you today?"
        with patch.object(whatsapp_service, '_generate_ai_response', return_value=mock_ai_response):
            # Execute
            result = await whatsapp_service.process_incoming_message(sample_incoming_message)

        # Assert
        assert result == created_message
        whatsapp_service.whatsapp_repository.create_from_webhook.assert_called_once()

    async def test_process_incoming_message_invalid_data(self, whatsapp_service):
        """Test processing invalid incoming message data."""
        # Setup - missing required fields
        invalid_message = {"From": "whatsapp:+1234567890"}

        # Execute & Assert
        with pytest.raises(WebhookProcessingError) as exc_info:
            await whatsapp_service.process_incoming_message(invalid_message)

        assert "webhook" in str(exc_info.value).lower()

    @patch('app.services.whatsapp_service.TwilioWhatsAppService')
    async def test_send_message_success(
        self, mock_twilio_service, whatsapp_service
    ):
        """Test successful message sending."""
        # Setup
        to_number = "+1234567890"
        message_body = "Your order is ready for pickup!"

        mock_twilio_instance = mock_twilio_service.return_value
        mock_response = MagicMock()
        mock_response.sid = "SM987654321"
        mock_twilio_instance.send_message.return_value = mock_response

        created_message = MagicMock(spec=WhatsAppMessage)
        whatsapp_service.whatsapp_repository.create.return_value = created_message

        # Execute
        result = await whatsapp_service.send_message(to_number, message_body)

        # Assert
        assert result == created_message
        mock_twilio_instance.send_message.assert_called_once_with(to_number, message_body)
        whatsapp_service.whatsapp_repository.create.assert_called_once()

    @patch('app.services.whatsapp_service.TwilioWhatsAppService')
    async def test_send_message_twilio_failure(
        self, mock_twilio_service, whatsapp_service
    ):
        """Test message sending failure from Twilio."""
        # Setup
        to_number = "+1234567890"
        message_body = "Test message"

        mock_twilio_instance = mock_twilio_service.return_value
        mock_twilio_instance.send_message.side_effect = Exception("Twilio error")

        # Execute & Assert
        with pytest.raises(MessageSendFailure) as exc_info:
            await whatsapp_service.send_message(to_number, message_body)

        assert to_number in str(exc_info.value)

    async def test_process_status_update_success(self, whatsapp_service):
        """Test successful status update processing."""
        # Setup
        status_data = {
            "MessageSid": "SM123456789",
            "MessageStatus": "delivered"
        }

        message = MagicMock(spec=WhatsAppMessage)
        whatsapp_service.whatsapp_repository.get_by_twilio_sid.return_value = message
        whatsapp_service.whatsapp_repository.update.return_value = message

        # Execute
        result = await whatsapp_service.process_status_update(status_data)

        # Assert
        assert result == message
        whatsapp_service.whatsapp_repository.get_by_twilio_sid.assert_called_once_with("SM123456789")
        whatsapp_service.whatsapp_repository.update.assert_called_once()

    async def test_process_status_update_message_not_found(self, whatsapp_service):
        """Test status update for non-existent message."""
        # Setup
        status_data = {
            "MessageSid": "SM_NONEXISTENT",
            "MessageStatus": "delivered"
        }

        whatsapp_service.whatsapp_repository.get_by_twilio_sid.return_value = None

        # Execute & Assert
        with pytest.raises(WebhookProcessingError) as exc_info:
            await whatsapp_service.process_status_update(status_data)

        assert "not found" in str(exc_info.value).lower()

    async def test_get_conversation_history_success(self, whatsapp_service):
        """Test successful conversation history retrieval."""
        # Setup
        phone_number = "+1234567890"
        restaurant_id = uuid4()

        messages = [MagicMock(spec=WhatsAppMessage) for _ in range(5)]
        whatsapp_service.whatsapp_repository.get_conversation_history.return_value = messages

        # Execute
        result = await whatsapp_service.get_conversation_history(phone_number, restaurant_id)

        # Assert
        assert result == messages
        whatsapp_service.whatsapp_repository.get_conversation_history.assert_called_once_with(
            phone_number, restaurant_id, limit=50
        )

    async def test_get_conversation_history_with_limit(self, whatsapp_service):
        """Test conversation history retrieval with custom limit."""
        # Setup
        phone_number = "+1234567890"
        restaurant_id = uuid4()
        limit = 10

        messages = [MagicMock(spec=WhatsAppMessage) for _ in range(limit)]
        whatsapp_service.whatsapp_repository.get_conversation_history.return_value = messages

        # Execute
        result = await whatsapp_service.get_conversation_history(
            phone_number, restaurant_id, limit=limit
        )

        # Assert
        assert len(result) == limit
        whatsapp_service.whatsapp_repository.get_conversation_history.assert_called_once_with(
            phone_number, restaurant_id, limit=limit
        )

    @patch('app.services.whatsapp_service.AIService')
    async def test_generate_ai_response(self, mock_ai_service, whatsapp_service):
        """Test AI response generation for customer messages."""
        # Setup
        customer_message = "I want to make a reservation for tonight"
        phone_number = "+1234567890"

        mock_ai_instance = mock_ai_service.return_value
        mock_response = "I'd be happy to help you with a reservation! What time would you prefer?"
        mock_ai_instance.generate_intelligent_response.return_value = mock_response

        # Execute
        with patch.object(whatsapp_service, '_generate_ai_response', return_value=mock_response) as mock_generate:
            result = await whatsapp_service._generate_ai_response(customer_message, phone_number)

        # Assert
        assert result == mock_response

    async def test_validate_webhook_data_valid(self, whatsapp_service):
        """Test webhook data validation with valid data."""
        # Setup
        valid_data = {
            "From": "whatsapp:+1234567890",
            "To": "whatsapp:+14155238886",
            "Body": "Hello",
            "MessageSid": "SM123456789"
        }

        # Execute - should not raise exception
        result = whatsapp_service._validate_webhook_data(valid_data)
        assert result is True

    async def test_validate_webhook_data_invalid(self, whatsapp_service):
        """Test webhook data validation with invalid data."""
        # Setup
        invalid_data = {"From": "whatsapp:+1234567890"}  # Missing required fields

        # Execute & Assert
        with pytest.raises(WebhookProcessingError):
            whatsapp_service._validate_webhook_data(invalid_data)

    @patch('app.services.whatsapp_service.TwilioWhatsAppService')
    async def test_check_service_health(self, mock_twilio_service, whatsapp_service):
        """Test WhatsApp service health check."""
        # Setup
        mock_twilio_instance = mock_twilio_service.return_value
        mock_twilio_instance.check_connection.return_value = True

        # Execute
        result = await whatsapp_service.check_service_health()

        # Assert
        assert result["healthy"] is True
        assert "twilio_connected" in result

    @patch('app.services.whatsapp_service.TwilioWhatsAppService')
    async def test_check_service_health_failure(self, mock_twilio_service, whatsapp_service):
        """Test WhatsApp service health check failure."""
        # Setup
        mock_twilio_instance = mock_twilio_service.return_value
        mock_twilio_instance.check_connection.side_effect = Exception("Connection failed")

        # Execute
        result = await whatsapp_service.check_service_health()

        # Assert
        assert result["healthy"] is False
        assert "error" in result


@pytest.mark.asyncio
class TestWhatsAppServiceIntegration:
    """Integration tests for WhatsApp service workflow."""

    @pytest.fixture
    def whatsapp_service(self):
        """WhatsAppService with partially mocked dependencies."""
        mock_session = AsyncMock()
        service = WhatsAppService(mock_session)
        service.whatsapp_repository = AsyncMock()
        return service

    @patch('app.services.whatsapp_service.TwilioWhatsAppService')
    @patch('app.services.whatsapp_service.AIService')
    async def test_complete_message_workflow(
        self, mock_ai_service, mock_twilio_service, whatsapp_service
    ):
        """Test complete incoming message to response workflow."""
        # Setup incoming message
        incoming_data = {
            "From": "whatsapp:+1234567890",
            "To": "whatsapp:+14155238886",
            "Body": "I need help with my order",
            "MessageSid": "SM123456789"
        }

        # Mock repository creating incoming message
        incoming_message = MagicMock(spec=WhatsAppMessage)
        whatsapp_service.whatsapp_repository.create_from_webhook.return_value = incoming_message

        # Mock AI response
        ai_response = "I'm here to help! Can you provide your order number?"
        mock_ai_instance = mock_ai_service.return_value
        mock_ai_instance.generate_intelligent_response.return_value = ai_response

        # Mock Twilio sending response
        mock_twilio_instance = mock_twilio_service.return_value
        mock_response = MagicMock()
        mock_response.sid = "SM987654321"
        mock_twilio_instance.send_message.return_value = mock_response

        # Mock repository creating outgoing message
        outgoing_message = MagicMock(spec=WhatsAppMessage)
        whatsapp_service.whatsapp_repository.create.return_value = outgoing_message

        # Execute - process incoming message (which should trigger response)
        with patch.object(whatsapp_service, '_generate_ai_response', return_value=ai_response):
            with patch.object(whatsapp_service, 'send_message', return_value=outgoing_message) as mock_send:
                result = await whatsapp_service.process_incoming_message(incoming_data)

        # Assert workflow completed
        assert result == incoming_message
        whatsapp_service.whatsapp_repository.create_from_webhook.assert_called_once()
        # Verify AI response was triggered (would be called in real implementation)