"""
Unit tests for AIService.
Tests business logic for AI operations including sentiment analysis.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.ai_service import AIService
from app.models.customer import Customer
from app.core.exceptions import SentimentAnalysisFailure, AIModelUnavailable, ResponseGenerationFailure


class TestAIService:
    """Test cases for AIService."""

    @pytest.fixture
    def mock_session(self):
        """Mock async database session."""
        return AsyncMock()

    @pytest.fixture
    def ai_service(self, mock_session):
        """AIService instance with mocked dependencies."""
        return AIService(mock_session)

    @pytest.fixture
    def sample_customer(self):
        """Sample customer for testing."""
        customer = MagicMock(spec=Customer)
        customer.id = uuid4()
        customer.name = "John Doe"
        customer.feedback = "Great service!"
        return customer

    @patch('app.services.ai_service.OpenRouterService')
    async def test_analyze_sentiment_positive(self, mock_openrouter, ai_service):
        """Test sentiment analysis for positive feedback."""
        # Setup
        feedback_text = "The food was absolutely delicious! Great service!"

        mock_openrouter_instance = mock_openrouter.return_value
        mock_response = {
            "sentiment_score": 0.85,
            "sentiment_category": "positive",
            "confidence": 0.92
        }
        mock_openrouter_instance.analyze_sentiment.return_value = mock_response

        # Execute
        result = await ai_service.analyze_sentiment(feedback_text)

        # Assert
        assert result["sentiment_score"] == 0.85
        assert result["sentiment_category"] == "positive"
        assert result["confidence"] == 0.92
        mock_openrouter_instance.analyze_sentiment.assert_called_once_with(feedback_text)

    @patch('app.services.ai_service.OpenRouterService')
    async def test_analyze_sentiment_negative(self, mock_openrouter, ai_service):
        """Test sentiment analysis for negative feedback."""
        # Setup
        feedback_text = "The food was cold and the service was terrible!"

        mock_openrouter_instance = mock_openrouter.return_value
        mock_response = {
            "sentiment_score": 0.15,
            "sentiment_category": "negative",
            "confidence": 0.88
        }
        mock_openrouter_instance.analyze_sentiment.return_value = mock_response

        # Execute
        result = await ai_service.analyze_sentiment(feedback_text)

        # Assert
        assert result["sentiment_score"] == 0.15
        assert result["sentiment_category"] == "negative"
        assert result["confidence"] == 0.88

    @patch('app.services.ai_service.OpenRouterService')
    async def test_analyze_sentiment_neutral(self, mock_openrouter, ai_service):
        """Test sentiment analysis for neutral feedback."""
        # Setup
        feedback_text = "The restaurant is located downtown."

        mock_openrouter_instance = mock_openrouter.return_value
        mock_response = {
            "sentiment_score": 0.5,
            "sentiment_category": "neutral",
            "confidence": 0.75
        }
        mock_openrouter_instance.analyze_sentiment.return_value = mock_response

        # Execute
        result = await ai_service.analyze_sentiment(feedback_text)

        # Assert
        assert result["sentiment_score"] == 0.5
        assert result["sentiment_category"] == "neutral"

    @patch('app.services.ai_service.OpenRouterService')
    async def test_analyze_sentiment_api_failure(self, mock_openrouter, ai_service):
        """Test sentiment analysis API failure."""
        # Setup
        feedback_text = "Some feedback text"

        mock_openrouter_instance = mock_openrouter.return_value
        mock_openrouter_instance.analyze_sentiment.side_effect = Exception("API Error")

        # Execute & Assert
        with pytest.raises(SentimentAnalysisFailure) as exc_info:
            await ai_service.analyze_sentiment(feedback_text)

        assert "API Error" in str(exc_info.value)

    async def test_analyze_sentiment_empty_text(self, ai_service):
        """Test sentiment analysis with empty text."""
        # Execute & Assert
        with pytest.raises(SentimentAnalysisFailure) as exc_info:
            await ai_service.analyze_sentiment("")

        assert "empty" in str(exc_info.value).lower()

    @patch('app.services.ai_service.RestaurantAIAgent')
    async def test_generate_intelligent_response_reservation(self, mock_restaurant_ai, ai_service):
        """Test intelligent response generation for reservation request."""
        # Setup
        customer_message = "I'd like to make a reservation for 4 people tonight at 7pm"
        customer_phone = "+1234567890"

        mock_ai_instance = mock_restaurant_ai.return_value
        mock_response = {
            "response": "I'd be happy to help you with a reservation for 4 people at 7pm tonight! Let me check our availability and get back to you.",
            "intent": "reservation",
            "confidence": 0.95
        }
        mock_ai_instance.generate_response.return_value = mock_response

        # Execute
        result = await ai_service.generate_intelligent_response(customer_message, customer_phone)

        # Assert
        assert "reservation" in result.lower()
        assert "4 people" in result
        mock_ai_instance.generate_response.assert_called_once()

    @patch('app.services.ai_service.RestaurantAIAgent')
    async def test_generate_intelligent_response_order_inquiry(self, mock_restaurant_ai, ai_service):
        """Test intelligent response generation for order inquiry."""
        # Setup
        customer_message = "Where is my order? I placed it an hour ago."
        customer_phone = "+1234567890"

        mock_ai_instance = mock_restaurant_ai.return_value
        mock_response = {
            "response": "I apologize for the delay! Let me check on your order status right away. Can you please provide your order number?",
            "intent": "order_status",
            "confidence": 0.90
        }
        mock_ai_instance.generate_response.return_value = mock_response

        # Execute
        result = await ai_service.generate_intelligent_response(customer_message, customer_phone)

        # Assert
        assert "order" in result.lower()
        assert "apologize" in result.lower()

    @patch('app.services.ai_service.RestaurantAIAgent')
    async def test_generate_intelligent_response_failure(self, mock_restaurant_ai, ai_service):
        """Test intelligent response generation failure."""
        # Setup
        customer_message = "Hello"
        customer_phone = "+1234567890"

        mock_ai_instance = mock_restaurant_ai.return_value
        mock_ai_instance.generate_response.side_effect = Exception("AI Service Down")

        # Execute & Assert
        with pytest.raises(ResponseGenerationFailure) as exc_info:
            await ai_service.generate_intelligent_response(customer_message, customer_phone)

        assert "AI Service Down" in str(exc_info.value)

    @patch('app.services.ai_service.OpenRouterService')
    async def test_analyze_customer_feedback_complete(self, mock_openrouter, ai_service, sample_customer):
        """Test complete customer feedback analysis."""
        # Setup
        mock_openrouter_instance = mock_openrouter.return_value
        mock_sentiment_response = {
            "sentiment_score": 0.8,
            "sentiment_category": "positive",
            "confidence": 0.9
        }
        mock_openrouter_instance.analyze_sentiment.return_value = mock_sentiment_response

        mock_analysis_response = {
            "key_themes": ["service", "food quality"],
            "suggestions": ["Continue excellent service"],
            "priority": "medium"
        }
        mock_openrouter_instance.analyze_feedback.return_value = mock_analysis_response

        # Execute
        result = await ai_service.analyze_customer_feedback(sample_customer.feedback)

        # Assert
        assert result["sentiment_score"] == 0.8
        assert result["sentiment_category"] == "positive"
        assert result["key_themes"] == ["service", "food quality"]
        assert result["suggestions"] == ["Continue excellent service"]

    async def test_check_model_availability_success(self, ai_service):
        """Test checking AI model availability."""
        # Setup
        with patch('app.services.ai_service.OpenRouterService') as mock_openrouter:
            mock_openrouter_instance = mock_openrouter.return_value
            mock_openrouter_instance.check_model_availability.return_value = True

            # Execute
            result = await ai_service.check_model_availability("anthropic/claude-3.5-haiku")

            # Assert
            assert result is True

    async def test_check_model_availability_failure(self, ai_service):
        """Test AI model unavailability."""
        # Setup
        with patch('app.services.ai_service.OpenRouterService') as mock_openrouter:
            mock_openrouter_instance = mock_openrouter.return_value
            mock_openrouter_instance.check_model_availability.return_value = False

            # Execute & Assert
            result = await ai_service.check_model_availability("invalid-model")
            assert result is False

    async def test_get_conversation_context(self, ai_service):
        """Test getting conversation context for AI responses."""
        # Setup
        phone_number = "+1234567890"
        restaurant_id = uuid4()

        with patch.object(ai_service, '_get_recent_messages') as mock_get_messages:
            mock_messages = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi! How can I help you?"},
                {"role": "user", "content": "I want to make a reservation"}
            ]
            mock_get_messages.return_value = mock_messages

            # Execute
            result = await ai_service.get_conversation_context(phone_number, restaurant_id)

            # Assert
            assert len(result) == 3
            assert result[-1]["content"] == "I want to make a reservation"

    @patch('app.services.ai_service.OpenRouterService')
    async def test_extract_customer_intent(self, mock_openrouter, ai_service):
        """Test extracting customer intent from message."""
        # Setup
        message = "I want to cancel my reservation for tonight"

        mock_openrouter_instance = mock_openrouter.return_value
        mock_response = {
            "intent": "cancel_reservation",
            "confidence": 0.92,
            "entities": {
                "time": "tonight",
                "action": "cancel"
            }
        }
        mock_openrouter_instance.extract_intent.return_value = mock_response

        # Execute
        result = await ai_service.extract_customer_intent(message)

        # Assert
        assert result["intent"] == "cancel_reservation"
        assert result["confidence"] == 0.92
        assert result["entities"]["action"] == "cancel"

    async def test_fallback_response(self, ai_service):
        """Test fallback response when AI services are unavailable."""
        # Execute
        result = ai_service.get_fallback_response("general")

        # Assert
        assert isinstance(result, str)
        assert len(result) > 0
        assert "help" in result.lower() or "assist" in result.lower()

    async def test_fallback_response_specific_intent(self, ai_service):
        """Test fallback response for specific intent."""
        # Execute
        result = ai_service.get_fallback_response("reservation")

        # Assert
        assert isinstance(result, str)
        assert "reservation" in result.lower() or "booking" in result.lower()


@pytest.mark.asyncio
class TestAIServiceIntegration:
    """Integration tests for AI service workflows."""

    @pytest.fixture
    def ai_service(self):
        """AIService with partially mocked dependencies."""
        mock_session = AsyncMock()
        return AIService(mock_session)

    @patch('app.services.ai_service.OpenRouterService')
    @patch('app.services.ai_service.RestaurantAIAgent')
    async def test_complete_customer_interaction_workflow(
        self, mock_restaurant_ai, mock_openrouter, ai_service
    ):
        """Test complete workflow from message to intelligent response."""
        # Setup customer message
        customer_message = "The food was great but service was slow"
        customer_phone = "+1234567890"

        # Mock sentiment analysis
        mock_openrouter_instance = mock_openrouter.return_value
        mock_sentiment = {
            "sentiment_score": 0.6,
            "sentiment_category": "mixed",
            "confidence": 0.8
        }
        mock_openrouter_instance.analyze_sentiment.return_value = mock_sentiment

        # Mock intelligent response
        mock_restaurant_ai_instance = mock_restaurant_ai.return_value
        mock_response = {
            "response": "Thank you for the feedback! We're glad you enjoyed the food. I'll make sure our team knows about the service timing so we can improve.",
            "intent": "feedback",
            "confidence": 0.85
        }
        mock_restaurant_ai_instance.generate_response.return_value = mock_response

        # Execute sentiment analysis
        sentiment_result = await ai_service.analyze_sentiment(customer_message)

        # Execute response generation
        response_result = await ai_service.generate_intelligent_response(
            customer_message, customer_phone
        )

        # Assert complete workflow
        assert sentiment_result["sentiment_category"] == "mixed"
        assert "feedback" in response_result.lower()
        assert "improve" in response_result.lower()

        # Verify both services were called
        mock_openrouter_instance.analyze_sentiment.assert_called_once()
        mock_restaurant_ai_instance.generate_response.assert_called_once()