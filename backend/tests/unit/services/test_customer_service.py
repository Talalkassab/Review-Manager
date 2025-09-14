"""
Unit tests for CustomerService.
Tests business logic independently of database layer.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
from datetime import datetime
from typing import List, Tuple

from app.services.customer_service import CustomerService
from app.models.user import User
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerFeedbackUpdate, CustomerListFilter
from app.core.exceptions import CustomerNotFound, InvalidInput


class TestCustomerService:
    """Test cases for CustomerService."""

    @pytest.fixture
    def mock_session(self):
        """Mock async database session."""
        return AsyncMock()

    @pytest.fixture
    def mock_customer_repository(self):
        """Mock customer repository."""
        return AsyncMock()

    @pytest.fixture
    def customer_service(self, mock_session, mock_customer_repository):
        """CustomerService instance with mocked dependencies."""
        service = CustomerService(mock_session)
        service.customer_repository = mock_customer_repository
        return service

    @pytest.fixture
    def sample_user(self):
        """Sample user for testing."""
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.restaurant_id = uuid4()
        user.is_superuser = False
        return user

    @pytest.fixture
    def sample_customer(self):
        """Sample customer for testing."""
        customer = MagicMock(spec=Customer)
        customer.id = uuid4()
        customer.restaurant_id = uuid4()
        customer.name = "John Doe"
        customer.phone_number = "+1234567890"
        customer.email = "john@example.com"
        customer.status = "pending"
        return customer

    @pytest.fixture
    def customer_create_data(self, sample_user):
        """Sample customer creation data."""
        return CustomerCreate(
            customer_number="CUST-001",
            first_name="Jane",
            last_name="Smith",
            phone_number="+1987654321",
            restaurant_id=sample_user.restaurant_id,
            email="jane@example.com"
        )

    @pytest.mark.asyncio
    async def test_get_customer_by_id_success(self, customer_service, sample_user, sample_customer):
        """Test successful customer retrieval by ID."""
        # Setup
        customer_service.customer_repository.get_by_id.return_value = sample_customer
        sample_customer.restaurant_id = sample_user.restaurant_id

        # Execute
        result = await customer_service.get_customer_by_id(
            sample_customer.id, sample_user
        )

        # Assert
        assert result == sample_customer
        customer_service.customer_repository.get_by_id.assert_called_once_with(sample_customer.id)

    async def test_get_customer_by_id_not_found(self, customer_service, sample_user):
        """Test customer not found scenario."""
        # Setup
        customer_service.customer_repository.get_by_id.return_value = None
        customer_id = uuid4()

        # Execute
        result = await customer_service.get_customer_by_id(customer_id, sample_user)

        # Assert
        assert result is None

    async def test_get_customer_by_id_different_restaurant(self, customer_service, sample_user, sample_customer):
        """Test customer access denied for different restaurant."""
        # Setup
        customer_service.customer_repository.get_by_id.return_value = sample_customer
        sample_customer.restaurant_id = uuid4()  # Different restaurant

        # Execute
        result = await customer_service.get_customer_by_id(
            sample_customer.id, sample_user
        )

        # Assert
        assert result is None

    async def test_get_customer_by_id_superuser_access(self, customer_service, sample_user, sample_customer):
        """Test superuser can access any customer."""
        # Setup
        sample_user.is_superuser = True
        customer_service.customer_repository.get_by_id.return_value = sample_customer
        sample_customer.restaurant_id = uuid4()  # Different restaurant

        # Execute
        result = await customer_service.get_customer_by_id(
            sample_customer.id, sample_user
        )

        # Assert
        assert result == sample_customer

    async def test_create_customer_new(self, customer_service, sample_user, customer_create_data, sample_customer):
        """Test creating a new customer."""
        # Setup
        customer_service.customer_repository.find_by_phone_and_restaurant.return_value = None
        customer_service.customer_repository.create.return_value = sample_customer
        sample_customer.update_visit_history = MagicMock()

        # Execute
        result = await customer_service.create_customer(customer_create_data, sample_user)

        # Assert
        assert result == sample_customer
        customer_service.customer_repository.find_by_phone_and_restaurant.assert_called_once()
        customer_service.customer_repository.create.assert_called_once()
        sample_customer.update_visit_history.assert_called_once()

    async def test_create_customer_existing_update_visit(self, customer_service, sample_user, customer_create_data, sample_customer):
        """Test updating existing customer with new visit."""
        # Setup
        existing_customer = sample_customer
        customer_service.customer_repository.find_by_phone_and_restaurant.return_value = existing_customer
        customer_service.customer_repository.update.return_value = existing_customer
        existing_customer.update_visit_history = MagicMock()

        # Execute
        result = await customer_service.create_customer(customer_create_data, sample_user)

        # Assert
        assert result == existing_customer
        customer_service.customer_repository.update.assert_called_once()
        existing_customer.update_visit_history.assert_called_once()

    async def test_create_customer_invalid_restaurant(self, customer_service, sample_user, customer_create_data):
        """Test creating customer for different restaurant (non-superuser)."""
        # Setup
        customer_create_data.restaurant_id = uuid4()  # Different restaurant

        # Execute & Assert
        with pytest.raises(InvalidInput) as exc_info:
            await customer_service.create_customer(customer_create_data, sample_user)

        assert "Cannot create customer for different restaurant" in str(exc_info.value)

    async def test_update_customer_success(self, customer_service, sample_user, sample_customer):
        """Test successful customer update."""
        # Setup
        update_data = CustomerUpdate(first_name="Updated Name", email="updated@example.com")
        updated_customer = sample_customer
        customer_service.customer_repository.update.return_value = updated_customer

        # Execute
        result = await customer_service.update_customer(sample_customer, update_data, sample_user)

        # Assert
        assert result == updated_customer
        customer_service.customer_repository.update.assert_called_once()

    async def test_update_customer_not_found(self, customer_service, sample_user, sample_customer):
        """Test customer update when customer not found."""
        # Setup
        update_data = CustomerUpdate(first_name="Updated Name")
        customer_service.customer_repository.update.return_value = None

        # Execute & Assert
        with pytest.raises(CustomerNotFound):
            await customer_service.update_customer(sample_customer, update_data, sample_user)

    async def test_delete_customer_success(self, customer_service, sample_user, sample_customer):
        """Test successful customer soft delete."""
        # Setup
        customer_service.customer_repository.delete.return_value = True
        customer_service.customer_repository.update.return_value = sample_customer

        # Execute
        result = await customer_service.delete_customer(sample_customer, sample_user)

        # Assert
        assert result is True
        customer_service.customer_repository.delete.assert_called_once_with(
            sample_customer.id, soft_delete=True
        )

    async def test_list_customers_regular_user(self, customer_service, sample_user):
        """Test listing customers for regular user."""
        # Setup
        customers = [MagicMock(spec=Customer) for _ in range(3)]
        total = 3
        customer_service.customer_repository.get_by_restaurant.return_value = (customers, total)

        # Execute
        result_customers, result_total = await customer_service.list_customers(sample_user)

        # Assert
        assert result_customers == customers
        assert result_total == total
        customer_service.customer_repository.get_by_restaurant.assert_called_once()

    async def test_list_customers_with_filters(self, customer_service, sample_user):
        """Test listing customers with filters."""
        # Setup
        filters = CustomerListFilter(status="pending", sentiment_category="positive")
        customers = [MagicMock(spec=Customer)]
        total = 1
        customer_service.customer_repository.get_by_restaurant.return_value = (customers, total)

        # Execute
        result_customers, result_total = await customer_service.list_customers(
            sample_user, filters=filters
        )

        # Assert
        assert result_customers == customers
        assert result_total == total

    async def test_update_customer_feedback(self, customer_service, sample_user, sample_customer):
        """Test updating customer feedback."""
        # Setup
        feedback_data = CustomerFeedbackUpdate(
            feedback="Great service!",
            sentiment_score=0.9,
            sentiment_category="positive"
        )
        customer_service.customer_repository.update.return_value = sample_customer

        # Execute
        result = await customer_service.update_customer_feedback(
            sample_customer, feedback_data, sample_user
        )

        # Assert
        assert result == sample_customer
        customer_service.customer_repository.update.assert_called_once()

    async def test_get_customer_stats_regular_user(self, customer_service, sample_user):
        """Test getting customer stats for regular user."""
        # Setup
        expected_stats = {
            'total_customers': 10,
            'status_breakdown': {'pending': 5, 'completed': 5},
            'sentiment_breakdown': {'positive': 8, 'negative': 2},
            'average_sentiment': 0.7
        }
        customer_service.customer_repository.get_customer_stats.return_value = expected_stats

        # Execute
        result = await customer_service.get_customer_stats(sample_user)

        # Assert
        assert result == expected_stats
        customer_service.customer_repository.get_customer_stats.assert_called_once_with(
            sample_user.restaurant_id
        )

    async def test_get_customer_stats_superuser(self, customer_service, sample_user):
        """Test getting customer stats for superuser with specific restaurant."""
        # Setup
        sample_user.is_superuser = True
        target_restaurant_id = uuid4()
        expected_stats = {'total_customers': 20}
        customer_service.customer_repository.get_customer_stats.return_value = expected_stats

        # Execute
        result = await customer_service.get_customer_stats(sample_user, target_restaurant_id)

        # Assert
        assert result == expected_stats
        customer_service.customer_repository.get_customer_stats.assert_called_once_with(
            target_restaurant_id
        )


@pytest.mark.asyncio
class TestCustomerServiceIntegration:
    """Integration-style tests that verify service behavior with more realistic scenarios."""

    @pytest.fixture
    def customer_service(self):
        """CustomerService with partially mocked dependencies."""
        mock_session = AsyncMock()
        service = CustomerService(mock_session)
        service.customer_repository = AsyncMock()
        return service

    async def test_create_customer_workflow(self, customer_service):
        """Test the complete customer creation workflow."""
        # Setup
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.restaurant_id = uuid4()
        user.is_superuser = False

        customer_data = CustomerCreate(
            customer_number="TEST-001",
            first_name="Test",
            last_name="Customer",
            phone_number="+1234567890",
            restaurant_id=user.restaurant_id,
            email="test@example.com"
        )

        new_customer = MagicMock(spec=Customer)
        new_customer.id = uuid4()
        new_customer.update_visit_history = MagicMock()

        # No existing customer found
        customer_service.customer_repository.find_by_phone_and_restaurant.return_value = None
        customer_service.customer_repository.create.return_value = new_customer

        # Execute
        result = await customer_service.create_customer(customer_data, user)

        # Assert complete workflow
        assert result == new_customer
        customer_service.customer_repository.find_by_phone_and_restaurant.assert_called_once_with(
            phone_number=customer_data.phone_number,
            restaurant_id=customer_data.restaurant_id
        )
        customer_service.customer_repository.create.assert_called_once()
        new_customer.update_visit_history.assert_called_once()

    async def test_business_logic_validation(self, customer_service):
        """Test that business logic validation is properly applied."""
        # Setup user trying to create customer for different restaurant
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.restaurant_id = uuid4()
        user.is_superuser = False

        customer_data = CustomerCreate(
            customer_number="TEST-002",
            first_name="Test",
            last_name="Customer",
            phone_number="+1234567890",
            restaurant_id=uuid4(),  # Different restaurant
            email="test@example.com"
        )

        # Execute & Assert
        with pytest.raises(InvalidInput) as exc_info:
            await customer_service.create_customer(customer_data, user)

        assert "restaurant" in str(exc_info.value).lower()
        # Repository should not be called for invalid business logic
        customer_service.customer_repository.find_by_phone_and_restaurant.assert_not_called()