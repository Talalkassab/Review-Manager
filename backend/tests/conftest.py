"""
Pytest configuration and shared fixtures.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

# Configure asyncio for pytest
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def mock_user():
    """Mock user for testing."""
    from app.models.user import User

    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "test@example.com"
    user.restaurant_id = uuid4()
    user.is_active = True
    user.is_superuser = False
    user.can_manage_customers = True
    user.can_view_analytics = True
    return user


@pytest.fixture
def mock_customer():
    """Mock customer for testing."""
    from app.models.customer import Customer

    customer = MagicMock(spec=Customer)
    customer.id = uuid4()
    customer.name = "Test Customer"
    customer.phone_number = "+1234567890"
    customer.email = "customer@example.com"
    customer.restaurant_id = uuid4()
    customer.status = "pending"
    customer.is_deleted = False
    return customer


@pytest.fixture
def mock_whatsapp_message():
    """Mock WhatsApp message for testing."""
    from app.models.whatsapp_message import WhatsAppMessage

    message = MagicMock(spec=WhatsAppMessage)
    message.id = uuid4()
    message.twilio_sid = "SM123456789"
    message.from_number = "+1234567890"
    message.to_number = "+14155238886"
    message.body = "Test message"
    message.status = "sent"
    return message


# Mock external services
@pytest.fixture(autouse=True)
def mock_external_services():
    """Automatically mock external services for all tests."""
    with pytest.MonkeyPatch().context() as m:
        # Mock Twilio
        mock_twilio = MagicMock()
        m.setattr("app.services.twilio_whatsapp.Client", mock_twilio)

        # Mock OpenRouter
        mock_openrouter = MagicMock()
        m.setattr("app.services.openrouter_service.httpx.AsyncClient", mock_openrouter)

        yield


@pytest.fixture
def sample_webhook_data():
    """Sample webhook data for testing."""
    return {
        "From": "whatsapp:+1234567890",
        "To": "whatsapp:+14155238886",
        "Body": "Hello, test message",
        "MessageSid": "SM123456789",
        "AccountSid": "AC123456789",
        "NumMedia": "0"
    }


@pytest.fixture
def sample_customer_data():
    """Sample customer creation data."""
    return {
        "name": "John Doe",
        "phone_number": "+1234567890",
        "email": "john@example.com",
        "restaurant_id": str(uuid4()),
        "visit_date": "2024-01-01T12:00:00Z"
    }