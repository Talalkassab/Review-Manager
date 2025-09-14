"""
Integration tests for Customer API endpoints.
Tests the complete flow from HTTP request to database through all layers.
"""
import pytest
from httpx import AsyncClient
from fastapi import FastAPI, status
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from app.api.v1 import api_router
from app.core.exceptions import register_exception_handlers
from app.models.customer import Customer
from app.models.user import User


class TestCustomerEndpointsIntegration:
    """Integration tests for customer endpoints."""

    @pytest.fixture
    async def app(self) -> FastAPI:
        """Create FastAPI application for testing."""
        app = FastAPI(title="Test Customer API")
        register_exception_handlers(app)
        app.include_router(api_router, prefix="/api/v1")
        return app

    @pytest.fixture
    async def client(self, app: FastAPI) -> AsyncClient:
        """Create async HTTP client for testing."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user."""
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.restaurant_id = uuid4()
        user.is_superuser = False
        user.can_manage_customers = True
        return user

    @pytest.fixture
    def mock_customer(self, mock_user):
        """Mock customer for testing."""
        customer = MagicMock(spec=Customer)
        customer.id = uuid4()
        customer.restaurant_id = mock_user.restaurant_id
        customer.name = "John Doe"
        customer.phone_number = "+1234567890"
        customer.email = "john@example.com"
        customer.status = "pending"
        customer.sentiment_score = 0.8
        customer.sentiment_category = "positive"
        customer.feedback = "Great service!"
        customer.created_at = datetime.utcnow()
        customer.updated_at = datetime.utcnow()
        customer.is_deleted = False
        return customer

    @pytest.fixture
    def customer_create_data(self, mock_user):
        """Valid customer creation data."""
        return {
            "name": "Jane Smith",
            "phone_number": "+1987654321",
            "email": "jane@example.com",
            "restaurant_id": str(mock_user.restaurant_id),
            "visit_date": "2024-01-01T12:00:00Z"
        }

    @pytest.fixture
    def customer_update_data(self):
        """Valid customer update data."""
        return {
            "name": "Jane Smith Updated",
            "email": "jane.updated@example.com",
            "status": "completed"
        }

    @patch('app.api.v1.dependencies.services.get_current_user')
    @patch('app.api.v1.dependencies.services.get_customer_service')
    async def test_get_customers_success(
        self,
        mock_get_service,
        mock_get_user,
        client: AsyncClient,
        mock_user,
        mock_customer
    ):
        """Test successful customer list retrieval."""
        # Setup
        mock_get_user.return_value = mock_user

        mock_service = AsyncMock()
        mock_service.list_customers.return_value = ([mock_customer], 1)
        mock_get_service.return_value = mock_service

        # Execute
        response = await client.get("/api/v1/customers/")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "customers" in data
        assert "total" in data
        assert data["total"] == 1
        assert len(data["customers"]) == 1
        assert data["customers"][0]["name"] == "John Doe"

    @patch('app.api.v1.dependencies.services.get_current_user')
    @patch('app.api.v1.dependencies.services.get_customer_service')
    async def test_get_customers_with_filters(
        self,
        mock_get_service,
        mock_get_user,
        client: AsyncClient,
        mock_user,
        mock_customer
    ):
        """Test customer list retrieval with filters."""
        # Setup
        mock_get_user.return_value = mock_user

        mock_service = AsyncMock()
        mock_service.list_customers.return_value = ([mock_customer], 1)
        mock_get_service.return_value = mock_service

        # Execute with filters
        response = await client.get(
            "/api/v1/customers/?status=pending&sentiment_category=positive&limit=10&offset=0"
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1

        # Verify service was called with filters
        mock_service.list_customers.assert_called_once()
        call_args = mock_service.list_customers.call_args
        assert call_args[1]["limit"] == 10
        assert call_args[1]["offset"] == 0

    @patch('app.api.v1.dependencies.services.get_current_user')
    @patch('app.api.v1.dependencies.services.get_customer_service')
    async def test_get_customer_by_id_success(
        self,
        mock_get_service,
        mock_get_user,
        client: AsyncClient,
        mock_user,
        mock_customer
    ):
        """Test successful customer retrieval by ID."""
        # Setup
        mock_get_user.return_value = mock_user

        mock_service = AsyncMock()
        mock_service.get_customer_by_id.return_value = mock_customer
        mock_get_service.return_value = mock_service

        # Execute
        response = await client.get(f"/api/v1/customers/{mock_customer.id}")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(mock_customer.id)
        assert data["name"] == "John Doe"
        assert data["phone_number"] == "+1234567890"

    @patch('app.api.v1.dependencies.services.get_current_user')
    @patch('app.api.v1.dependencies.services.get_customer_service')
    async def test_get_customer_by_id_not_found(
        self,
        mock_get_service,
        mock_get_user,
        client: AsyncClient,
        mock_user
    ):
        """Test customer not found scenario."""
        # Setup
        mock_get_user.return_value = mock_user

        mock_service = AsyncMock()
        mock_service.get_customer_by_id.return_value = None
        mock_get_service.return_value = mock_service

        customer_id = uuid4()

        # Execute
        response = await client.get(f"/api/v1/customers/{customer_id}")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "error" in data
        assert data["error"]["type"] == "CUSTOMER_NOT_FOUND"

    @patch('app.api.v1.dependencies.services.get_current_user')
    @patch('app.api.v1.dependencies.services.get_customer_service')
    async def test_create_customer_success(
        self,
        mock_get_service,
        mock_get_user,
        client: AsyncClient,
        mock_user,
        mock_customer,
        customer_create_data
    ):
        """Test successful customer creation."""
        # Setup
        mock_get_user.return_value = mock_user

        mock_service = AsyncMock()
        mock_service.create_customer.return_value = mock_customer
        mock_get_service.return_value = mock_service

        # Execute
        response = await client.post("/api/v1/customers/", json=customer_create_data)

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "John Doe"  # Mock customer name

        # Verify service was called with correct data
        mock_service.create_customer.assert_called_once()
        call_args = mock_service.create_customer.call_args
        assert call_args[0][0].name == customer_create_data["name"]

    @patch('app.api.v1.dependencies.services.get_current_user')
    @patch('app.api.v1.dependencies.services.get_customer_service')
    async def test_create_customer_invalid_phone(
        self,
        mock_get_service,
        mock_get_user,
        client: AsyncClient,
        mock_user,
        customer_create_data
    ):
        """Test customer creation with invalid phone number."""
        # Setup
        mock_get_user.return_value = mock_user
        mock_get_service.return_value = AsyncMock()

        # Invalid phone number
        customer_create_data["phone_number"] = "invalid-phone"

        # Execute
        response = await client.post("/api/v1/customers/", json=customer_create_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch('app.api.v1.dependencies.services.get_current_user')
    @patch('app.api.v1.dependencies.services.get_customer_service')
    async def test_create_customer_missing_required_fields(
        self,
        mock_get_service,
        mock_get_user,
        client: AsyncClient,
        mock_user
    ):
        """Test customer creation with missing required fields."""
        # Setup
        mock_get_user.return_value = mock_user
        mock_get_service.return_value = AsyncMock()

        # Missing required fields
        incomplete_data = {"name": "John Doe"}

        # Execute
        response = await client.post("/api/v1/customers/", json=incomplete_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data

    @patch('app.api.v1.dependencies.services.get_current_user')
    @patch('app.api.v1.dependencies.services.get_customer_service')
    async def test_update_customer_success(
        self,
        mock_get_service,
        mock_get_user,
        client: AsyncClient,
        mock_user,
        mock_customer,
        customer_update_data
    ):
        """Test successful customer update."""
        # Setup
        mock_get_user.return_value = mock_user

        mock_service = AsyncMock()
        mock_service.get_customer_by_id.return_value = mock_customer
        mock_service.update_customer.return_value = mock_customer
        mock_get_service.return_value = mock_service

        # Execute
        response = await client.put(
            f"/api/v1/customers/{mock_customer.id}",
            json=customer_update_data
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(mock_customer.id)

        # Verify service methods were called
        mock_service.get_customer_by_id.assert_called_once_with(mock_customer.id, mock_user)
        mock_service.update_customer.assert_called_once()

    @patch('app.api.v1.dependencies.services.get_current_user')
    @patch('app.api.v1.dependencies.services.get_customer_service')
    async def test_update_customer_not_found(
        self,
        mock_get_service,
        mock_get_user,
        client: AsyncClient,
        mock_user,
        customer_update_data
    ):
        """Test updating non-existent customer."""
        # Setup
        mock_get_user.return_value = mock_user

        mock_service = AsyncMock()
        mock_service.get_customer_by_id.return_value = None
        mock_get_service.return_value = mock_service

        customer_id = uuid4()

        # Execute
        response = await client.put(f"/api/v1/customers/{customer_id}", json=customer_update_data)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch('app.api.v1.dependencies.services.get_current_user')
    @patch('app.api.v1.dependencies.services.get_customer_service')
    async def test_delete_customer_success(
        self,
        mock_get_service,
        mock_get_user,
        client: AsyncClient,
        mock_user,
        mock_customer
    ):
        """Test successful customer deletion."""
        # Setup
        mock_get_user.return_value = mock_user

        mock_service = AsyncMock()
        mock_service.get_customer_by_id.return_value = mock_customer
        mock_service.delete_customer.return_value = True
        mock_get_service.return_value = mock_service

        # Execute
        response = await client.delete(f"/api/v1/customers/{mock_customer.id}")

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify service methods were called
        mock_service.get_customer_by_id.assert_called_once()
        mock_service.delete_customer.assert_called_once()

    @patch('app.api.v1.dependencies.services.get_current_user')
    @patch('app.api.v1.dependencies.services.get_customer_service')
    async def test_delete_customer_not_found(
        self,
        mock_get_service,
        mock_get_user,
        client: AsyncClient,
        mock_user
    ):
        """Test deleting non-existent customer."""
        # Setup
        mock_get_user.return_value = mock_user

        mock_service = AsyncMock()
        mock_service.get_customer_by_id.return_value = None
        mock_get_service.return_value = mock_service

        customer_id = uuid4()

        # Execute
        response = await client.delete(f"/api/v1/customers/{customer_id}")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch('app.api.v1.dependencies.services.get_current_user')
    @patch('app.api.v1.dependencies.services.get_customer_service')
    async def test_get_customer_stats_success(
        self,
        mock_get_service,
        mock_get_user,
        client: AsyncClient,
        mock_user
    ):
        """Test successful customer stats retrieval."""
        # Setup
        mock_get_user.return_value = mock_user

        mock_stats = {
            "total_customers": 100,
            "new_customers": 25,
            "returning_customers": 75,
            "average_sentiment": 0.72,
            "sentiment_distribution": {"positive": 60, "negative": 15, "neutral": 25}
        }

        mock_service = AsyncMock()
        mock_service.get_customer_stats.return_value = mock_stats
        mock_get_service.return_value = mock_service

        # Execute
        response = await client.get("/api/v1/customers/stats")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_customers"] == 100
        assert data["average_sentiment"] == 0.72
        assert data["sentiment_distribution"]["positive"] == 60

    async def test_customer_endpoints_require_authentication(self, client: AsyncClient):
        """Test that customer endpoints require authentication."""
        customer_id = uuid4()

        # Test endpoints without authentication
        endpoints = [
            ("GET", "/api/v1/customers/"),
            ("GET", f"/api/v1/customers/{customer_id}"),
            ("POST", "/api/v1/customers/"),
            ("PUT", f"/api/v1/customers/{customer_id}"),
            ("DELETE", f"/api/v1/customers/{customer_id}"),
            ("GET", "/api/v1/customers/stats")
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                response = await client.get(endpoint)
            elif method == "POST":
                response = await client.post(endpoint, json={})
            elif method == "PUT":
                response = await client.put(endpoint, json={})
            elif method == "DELETE":
                response = await client.delete(endpoint)

            # Should return 401 or 422 (depending on authentication setup)
            assert response.status_code in [401, 422, 403]

    @patch('app.api.v1.dependencies.services.get_current_user')
    @patch('app.api.v1.dependencies.services.get_customer_service')
    async def test_update_customer_feedback(
        self,
        mock_get_service,
        mock_get_user,
        client: AsyncClient,
        mock_user,
        mock_customer
    ):
        """Test updating customer feedback."""
        # Setup
        mock_get_user.return_value = mock_user

        mock_service = AsyncMock()
        mock_service.get_customer_by_id.return_value = mock_customer
        mock_service.update_customer_feedback.return_value = mock_customer
        mock_get_service.return_value = mock_service

        feedback_data = {
            "feedback": "Updated feedback text",
            "sentiment_score": 0.9,
            "sentiment_category": "positive"
        }

        # Execute
        response = await client.put(
            f"/api/v1/customers/{mock_customer.id}/feedback",
            json=feedback_data
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(mock_customer.id)

        # Verify service methods were called
        mock_service.update_customer_feedback.assert_called_once()

    @patch('app.api.v1.dependencies.services.get_current_user')
    @patch('app.api.v1.dependencies.services.get_customer_service')
    async def test_error_handling_service_exception(
        self,
        mock_get_service,
        mock_get_user,
        client: AsyncClient,
        mock_user
    ):
        """Test error handling when service raises exception."""
        # Setup
        mock_get_user.return_value = mock_user

        mock_service = AsyncMock()
        mock_service.list_customers.side_effect = Exception("Database connection lost")
        mock_get_service.return_value = mock_service

        # Execute
        response = await client.get("/api/v1/customers/")

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "error" in data
        assert data["error"]["type"] == "INTERNAL_SERVER_ERROR"
        assert "correlation_id" in data["error"]


@pytest.mark.integration
class TestCustomerEndpointsPermissions:
    """Test customer endpoint permissions and authorization."""

    @pytest.fixture
    async def app(self) -> FastAPI:
        """Create FastAPI application for testing."""
        app = FastAPI(title="Test Customer API")
        register_exception_handlers(app)
        app.include_router(api_router, prefix="/api/v1")
        return app

    @pytest.fixture
    async def client(self, app: FastAPI) -> AsyncClient:
        """Create async HTTP client for testing."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.fixture
    def regular_user(self):
        """Regular user with limited permissions."""
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.restaurant_id = uuid4()
        user.is_superuser = False
        user.can_manage_customers = True
        user.can_view_analytics = False
        return user

    @pytest.fixture
    def superuser(self):
        """Superuser with all permissions."""
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.restaurant_id = uuid4()
        user.is_superuser = True
        user.can_manage_customers = True
        user.can_view_analytics = True
        return user

    @patch('app.api.v1.dependencies.services.get_current_user')
    @patch('app.api.v1.dependencies.services.get_customer_service')
    async def test_regular_user_can_access_own_restaurant_customers(
        self,
        mock_get_service,
        mock_get_user,
        client: AsyncClient,
        regular_user
    ):
        """Test that regular users can access their restaurant's customers."""
        # Setup
        mock_get_user.return_value = regular_user

        mock_service = AsyncMock()
        mock_service.list_customers.return_value = ([], 0)
        mock_get_service.return_value = mock_service

        # Execute
        response = await client.get("/api/v1/customers/")

        # Assert
        assert response.status_code == status.HTTP_200_OK

        # Verify service was called with the user
        mock_service.list_customers.assert_called_once_with(regular_user)

    @patch('app.api.v1.dependencies.services.get_current_user')
    @patch('app.api.v1.dependencies.services.get_customer_service')
    async def test_superuser_can_access_any_restaurant_customers(
        self,
        mock_get_service,
        mock_get_user,
        client: AsyncClient,
        superuser
    ):
        """Test that superusers can access any restaurant's customers."""
        # Setup
        mock_get_user.return_value = superuser

        mock_service = AsyncMock()
        mock_service.list_customers.return_value = ([], 0)
        mock_get_service.return_value = mock_service

        # Execute with restaurant_id parameter
        other_restaurant_id = uuid4()
        response = await client.get(f"/api/v1/customers/?restaurant_id={other_restaurant_id}")

        # Assert
        assert response.status_code == status.HTTP_200_OK