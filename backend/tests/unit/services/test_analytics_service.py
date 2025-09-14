"""
Unit tests for AnalyticsService.
Tests business logic for analytics and reporting.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
from datetime import datetime, timedelta

from app.services.analytics_service import AnalyticsService, TimeRange
from app.models.customer import Customer
from app.models.whatsapp_message import WhatsAppMessage


class TestAnalyticsService:
    """Test cases for AnalyticsService."""

    @pytest.fixture
    def mock_session(self):
        """Mock async database session."""
        return AsyncMock()

    @pytest.fixture
    def analytics_service(self, mock_session):
        """AnalyticsService instance with mocked dependencies."""
        return AnalyticsService(mock_session)

    @pytest.fixture
    def sample_restaurant_id(self):
        """Sample restaurant ID for testing."""
        return uuid4()

    @pytest.fixture
    def sample_customer_data(self):
        """Sample customer data for testing."""
        return {
            "id": uuid4(),
            "name": "John Doe",
            "sentiment_score": 0.8,
            "sentiment_category": "positive",
            "created_at": datetime.utcnow() - timedelta(days=5),
            "updated_at": datetime.utcnow() - timedelta(days=1)
        }

    async def test_calculate_date_range_today(self, analytics_service):
        """Test date range calculation for today."""
        start_date, end_date = analytics_service._calculate_date_range(TimeRange.TODAY)

        # Start should be beginning of today
        assert start_date.time() == datetime.min.time()
        # End should be current time (approximately)
        assert (end_date - datetime.utcnow()).total_seconds() < 5

    async def test_calculate_date_range_week(self, analytics_service):
        """Test date range calculation for week."""
        start_date, end_date = analytics_service._calculate_date_range(TimeRange.WEEK)

        expected_days = (end_date - start_date).days
        assert expected_days == 7

    async def test_calculate_date_range_month(self, analytics_service):
        """Test date range calculation for month."""
        start_date, end_date = analytics_service._calculate_date_range(TimeRange.MONTH)

        expected_days = (end_date - start_date).days
        assert expected_days == 30

    async def test_calculate_date_range_custom(self, analytics_service):
        """Test date range calculation for custom range."""
        custom_start = datetime.utcnow() - timedelta(days=10)
        custom_end = datetime.utcnow() - timedelta(days=1)

        start_date, end_date = analytics_service._calculate_date_range(
            TimeRange.CUSTOM, custom_start, custom_end
        )

        assert start_date == custom_start
        assert end_date == custom_end

    async def test_build_base_filters_with_restaurant_id(self, analytics_service, sample_restaurant_id):
        """Test base filters with restaurant ID."""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        filters = analytics_service._build_base_filters(sample_restaurant_id, start_date, end_date)

        assert len(filters) == 4  # is_deleted, created_at >= start, created_at <= end, restaurant_id
        # Test that restaurant filter is included
        assert any("restaurant_id" in str(filter) for filter in filters)

    async def test_build_base_filters_without_restaurant_id(self, analytics_service):
        """Test base filters without restaurant ID."""
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        filters = analytics_service._build_base_filters(None, start_date, end_date)

        assert len(filters) == 3  # is_deleted, created_at >= start, created_at <= end

    async def test_count_customers_success(self, analytics_service):
        """Test counting customers with filters."""
        # Setup
        mock_result = MagicMock()
        mock_result.scalar.return_value = 25
        analytics_service.session.execute.return_value = mock_result

        filters = [Customer.is_deleted == False]

        # Execute
        result = await analytics_service._count_customers(filters)

        # Assert
        assert result == 25
        analytics_service.session.execute.assert_called_once()

    async def test_count_customers_none_result(self, analytics_service):
        """Test counting customers when result is None."""
        # Setup
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        analytics_service.session.execute.return_value = mock_result

        filters = [Customer.is_deleted == False]

        # Execute
        result = await analytics_service._count_customers(filters)

        # Assert
        assert result == 0

    async def test_calculate_average_sentiment_success(self, analytics_service):
        """Test calculating average sentiment."""
        # Setup
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0.75
        analytics_service.session.execute.return_value = mock_result

        filters = [Customer.is_deleted == False]

        # Execute
        result = await analytics_service._calculate_average_sentiment(filters)

        # Assert
        assert result == 0.75

    async def test_calculate_average_sentiment_no_data(self, analytics_service):
        """Test calculating average sentiment with no data."""
        # Setup
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        analytics_service.session.execute.return_value = mock_result

        filters = [Customer.is_deleted == False]

        # Execute
        result = await analytics_service._calculate_average_sentiment(filters)

        # Assert
        assert result == 0.5  # Default value when no data

    async def test_get_sentiment_distribution_success(self, analytics_service):
        """Test getting sentiment distribution."""
        # Setup
        mock_result = MagicMock()
        mock_result.all.return_value = [
            ("positive", 15),
            ("negative", 5),
            ("neutral", 10)
        ]
        analytics_service.session.execute.return_value = mock_result

        filters = [Customer.is_deleted == False]

        # Execute
        result = await analytics_service._get_sentiment_distribution(filters)

        # Assert
        assert result == {"positive": 15, "negative": 5, "neutral": 10}

    async def test_get_customers_by_status_success(self, analytics_service):
        """Test getting customers by status."""
        # Setup
        mock_result = MagicMock()
        mock_result.all.return_value = [
            ("pending", 20),
            ("completed", 15),
            ("active", 10)
        ]
        analytics_service.session.execute.return_value = mock_result

        filters = [Customer.is_deleted == False]

        # Execute
        result = await analytics_service._get_customers_by_status(filters)

        # Assert
        assert result == {"pending": 20, "completed": 15, "active": 10}

    async def test_count_new_customers_success(self, analytics_service):
        """Test counting new customers (single visit)."""
        # Setup
        mock_result = MagicMock()
        mock_result.scalar.return_value = 8
        analytics_service.session.execute.return_value = mock_result

        filters = [Customer.is_deleted == False]

        # Execute
        result = await analytics_service._count_new_customers(filters)

        # Assert
        assert result == 8

    async def test_count_returning_customers_success(self, analytics_service):
        """Test counting returning customers (multiple visits)."""
        # Setup
        mock_result = MagicMock()
        mock_result.scalar.return_value = 12
        analytics_service.session.execute.return_value = mock_result

        filters = [Customer.is_deleted == False]

        # Execute
        result = await analytics_service._count_returning_customers(filters)

        # Assert
        assert result == 12

    async def test_count_total_messages_success(self, analytics_service):
        """Test counting total messages."""
        # Setup
        mock_result = MagicMock()
        mock_result.scalar.return_value = 150
        analytics_service.session.execute.return_value = mock_result

        filters = [Customer.is_deleted == False]

        # Execute
        result = await analytics_service._count_total_messages(filters)

        # Assert
        assert result == 150

    async def test_count_inbound_messages_success(self, analytics_service):
        """Test counting inbound messages."""
        # Setup
        mock_result = MagicMock()
        mock_result.scalar.return_value = 90
        analytics_service.session.execute.return_value = mock_result

        filters = [Customer.is_deleted == False]

        # Execute
        result = await analytics_service._count_inbound_messages(filters)

        # Assert
        assert result == 90

    async def test_count_outbound_messages_success(self, analytics_service):
        """Test counting outbound messages."""
        # Setup
        mock_result = MagicMock()
        mock_result.scalar.return_value = 60
        analytics_service.session.execute.return_value = mock_result

        filters = [Customer.is_deleted == False]

        # Execute
        result = await analytics_service._count_outbound_messages(filters)

        # Assert
        assert result == 60

    async def test_get_messages_by_hour_success(self, analytics_service):
        """Test getting message distribution by hour."""
        # Setup
        mock_result = MagicMock()
        mock_result.all.return_value = [
            (9, 25),   # 9 AM: 25 messages
            (14, 30),  # 2 PM: 30 messages
            (18, 15)   # 6 PM: 15 messages
        ]
        analytics_service.session.execute.return_value = mock_result

        filters = [Customer.is_deleted == False]

        # Execute
        result = await analytics_service._get_messages_by_hour(filters)

        # Assert
        assert result == {9: 25, 14: 30, 18: 15}

    async def test_get_messages_by_day_success(self, analytics_service):
        """Test getting message distribution by day of week."""
        # Setup
        mock_result = MagicMock()
        mock_result.all.return_value = [
            (1, 20),  # Monday
            (2, 25),  # Tuesday
            (5, 30)   # Friday
        ]
        analytics_service.session.execute.return_value = mock_result

        filters = [Customer.is_deleted == False]

        # Execute
        result = await analytics_service._get_messages_by_day(filters)

        # Assert
        expected = {
            'Monday': 20,
            'Tuesday': 25,
            'Friday': 30
        }
        assert result == expected

    async def test_calculate_response_rate_success(self, analytics_service):
        """Test calculating response rate."""
        # Setup - Mock two separate execute calls
        inbound_result = MagicMock()
        inbound_result.scalar.return_value = 50

        responded_result = MagicMock()
        responded_result.scalar.return_value = 40

        analytics_service.session.execute.side_effect = [inbound_result, responded_result]

        filters = [Customer.is_deleted == False]

        # Execute
        result = await analytics_service._calculate_response_rate(filters)

        # Assert
        expected_rate = min(40 / 50, 1.0)  # 0.8
        assert result == expected_rate

    async def test_calculate_response_rate_no_inbound_messages(self, analytics_service):
        """Test calculating response rate with no inbound messages."""
        # Setup
        inbound_result = MagicMock()
        inbound_result.scalar.return_value = 0
        analytics_service.session.execute.return_value = inbound_result

        filters = [Customer.is_deleted == False]

        # Execute
        result = await analytics_service._calculate_response_rate(filters)

        # Assert
        assert result == 0.0

    async def test_calculate_response_rate_exception(self, analytics_service):
        """Test calculating response rate with exception."""
        # Setup
        analytics_service.session.execute.side_effect = Exception("Database error")

        filters = [Customer.is_deleted == False]

        # Execute
        result = await analytics_service._calculate_response_rate(filters)

        # Assert
        assert result == 0.0

    async def test_count_conversations_success(self, analytics_service):
        """Test counting unique conversations."""
        # Setup
        mock_result = MagicMock()
        mock_result.scalar.return_value = 35
        analytics_service.session.execute.return_value = mock_result

        filters = [Customer.is_deleted == False]

        # Execute
        result = await analytics_service._count_conversations(filters)

        # Assert
        assert result == 35

    async def test_calculate_avg_messages_per_conversation_success(self, analytics_service):
        """Test calculating average messages per conversation."""
        # Setup - Mock the methods that get called
        with patch.object(analytics_service, '_count_total_messages', return_value=100) as mock_total:
            with patch.object(analytics_service, '_count_conversations', return_value=20) as mock_conversations:
                filters = [Customer.is_deleted == False]

                # Execute
                result = await analytics_service._calculate_avg_messages_per_conversation(filters)

                # Assert
                assert result == 5.0
                mock_total.assert_called_once_with(filters)
                mock_conversations.assert_called_once_with(filters)

    async def test_calculate_avg_messages_per_conversation_no_conversations(self, analytics_service):
        """Test calculating average messages per conversation with no conversations."""
        # Setup
        with patch.object(analytics_service, '_count_total_messages', return_value=100):
            with patch.object(analytics_service, '_count_conversations', return_value=0):
                filters = [Customer.is_deleted == False]

                # Execute
                result = await analytics_service._calculate_avg_messages_per_conversation(filters)

                # Assert
                assert result == 0.0

    async def test_calculate_growth_rate_success(self, analytics_service):
        """Test calculating growth rate."""
        # Setup - Mock sequential calls to _count_customers
        with patch.object(analytics_service, '_count_customers', side_effect=[120, 100]) as mock_count:
            filters = [Customer.is_deleted == False]

            # Execute
            result = await analytics_service._calculate_growth_rate(filters)

            # Assert
            expected_growth = ((120 - 100) / 100) * 100  # 20%
            assert result == expected_growth

    async def test_calculate_growth_rate_no_previous_customers(self, analytics_service):
        """Test calculating growth rate with no previous customers."""
        # Setup
        with patch.object(analytics_service, '_count_customers', side_effect=[50, 0]):
            filters = [Customer.is_deleted == False]

            # Execute
            result = await analytics_service._calculate_growth_rate(filters)

            # Assert
            assert result == 100.0  # 100% growth from 0

    async def test_calculate_growth_rate_no_current_customers(self, analytics_service):
        """Test calculating growth rate with no current customers."""
        # Setup
        with patch.object(analytics_service, '_count_customers', side_effect=[0, 10]):
            filters = [Customer.is_deleted == False]

            # Execute
            result = await analytics_service._calculate_growth_rate(filters)

            # Assert
            assert result == -100.0  # -100% (lost all customers)

    async def test_count_vip_customers_success(self, analytics_service):
        """Test counting VIP customers."""
        # Setup
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        analytics_service.session.execute.return_value = mock_result

        filters = [Customer.is_deleted == False]

        # Execute
        result = await analytics_service._count_vip_customers(filters)

        # Assert
        assert result == 5

    async def test_count_regular_customers_success(self, analytics_service):
        """Test counting regular customers."""
        # Setup
        mock_result = MagicMock()
        mock_result.scalar.return_value = 15
        analytics_service.session.execute.return_value = mock_result

        filters = [Customer.is_deleted == False]

        # Execute
        result = await analytics_service._count_regular_customers(filters)

        # Assert
        assert result == 15

    async def test_count_at_risk_customers_success(self, analytics_service):
        """Test counting at-risk customers."""
        # Setup
        mock_result = MagicMock()
        mock_result.scalar.return_value = 3
        analytics_service.session.execute.return_value = mock_result

        filters = [Customer.is_deleted == False]

        # Execute
        result = await analytics_service._count_at_risk_customers(filters)

        # Assert
        assert result == 3

    async def test_count_lost_customers_success(self, analytics_service):
        """Test counting lost customers."""
        # Setup
        mock_result = MagicMock()
        mock_result.scalar.return_value = 2
        analytics_service.session.execute.return_value = mock_result

        filters = [Customer.is_deleted == False]

        # Execute
        result = await analytics_service._count_lost_customers(filters)

        # Assert
        assert result == 2

    async def test_analyze_peak_hours_with_data(self, analytics_service):
        """Test analyzing peak hours with message data."""
        # Setup
        with patch.object(analytics_service, '_get_messages_by_hour',
                         return_value={9: 10, 14: 25, 18: 15}) as mock_messages:
            filters = [Customer.is_deleted == False]

            # Execute
            result = await analytics_service._analyze_peak_hours(filters)

            # Assert
            assert result["peak_hour"] == 14  # 2 PM had most messages (25)
            assert result["message_count"] == 25
            assert result["distribution"] == {9: 10, 14: 25, 18: 15}

    async def test_analyze_peak_hours_no_data(self, analytics_service):
        """Test analyzing peak hours with no message data."""
        # Setup
        with patch.object(analytics_service, '_get_messages_by_hour', return_value={}):
            filters = [Customer.is_deleted == False]

            # Execute
            result = await analytics_service._analyze_peak_hours(filters)

            # Assert
            assert result["peak_hour"] is None
            assert result["message_count"] == 0
            assert result["distribution"] == {}


@pytest.mark.asyncio
class TestAnalyticsServiceIntegration:
    """Integration tests for analytics service workflows."""

    @pytest.fixture
    def analytics_service(self):
        """AnalyticsService with partially mocked dependencies."""
        mock_session = AsyncMock()
        return AnalyticsService(mock_session)

    async def test_get_customer_segments_workflow(self, analytics_service):
        """Test complete customer segmentation workflow."""
        # Setup - Mock all segment counting methods
        with patch.object(analytics_service, '_count_vip_customers', return_value=5):
            with patch.object(analytics_service, '_count_regular_customers', return_value=15):
                with patch.object(analytics_service, '_count_at_risk_customers', return_value=3):
                    with patch.object(analytics_service, '_count_lost_customers', return_value=2):
                        filters = [Customer.is_deleted == False]

                        # Execute
                        result = await analytics_service._get_customer_segments(filters)

                        # Assert
                        assert result == {
                            "vip": 5,
                            "regular": 15,
                            "at_risk": 3,
                            "lost": 2
                        }

    async def test_get_summary_metrics_workflow(self, analytics_service):
        """Test getting summary metrics workflow."""
        # Setup - Mock all the helper methods
        with patch.object(analytics_service, '_count_customers', side_effect=[100, 75]):  # total, then active
            with patch.object(analytics_service, '_calculate_average_sentiment', return_value=0.72):
                with patch.object(analytics_service, '_count_total_messages', return_value=500):
                    filters = [Customer.is_deleted == False]

                    # Execute
                    result = await analytics_service._get_summary_metrics(filters)

                    # Assert
                    assert result["total_customers"] == 100
                    assert result["active_customers"] == 75
                    assert result["average_sentiment"] == 0.72
                    assert result["total_messages"] == 500
                    assert result["engagement_rate"] == 75.0  # 75/100 * 100

    async def test_get_customer_metrics_workflow(self, analytics_service):
        """Test getting customer metrics workflow."""
        # Setup
        with patch.object(analytics_service, '_count_customers', return_value=100):
            with patch.object(analytics_service, '_count_new_customers', return_value=25):
                with patch.object(analytics_service, '_count_returning_customers', return_value=75):
                    with patch.object(analytics_service, '_get_customers_by_status',
                                    return_value={"pending": 30, "active": 70}):
                        with patch.object(analytics_service, '_calculate_growth_rate', return_value=15.5):
                            filters = [Customer.is_deleted == False]

                            # Execute
                            result = await analytics_service._get_customer_metrics(filters)

                            # Assert
                            assert result["total"] == 100
                            assert result["new"] == 25
                            assert result["returning"] == 75
                            assert result["by_status"]["pending"] == 30
                            assert result["by_status"]["active"] == 70
                            assert result["growth_rate"] == 15.5

    async def test_get_engagement_metrics_workflow(self, analytics_service):
        """Test getting engagement metrics workflow."""
        # Setup
        with patch.object(analytics_service, '_count_conversations', return_value=50):
            with patch.object(analytics_service, '_calculate_avg_messages_per_conversation', return_value=4.5):
                with patch.object(analytics_service, '_calculate_response_rate', return_value=0.85):
                    with patch.object(analytics_service, '_calculate_avg_response_time', return_value=6.2):
                        filters = [Customer.is_deleted == False]

                        # Execute
                        result = await analytics_service._get_engagement_metrics(filters)

                        # Assert
                        assert result["total_conversations"] == 50
                        assert result["avg_messages_per_conversation"] == 4.5
                        assert result["response_rate"] == 0.85
                        assert result["avg_response_time"] == 6.2

    async def test_error_handling_in_trend_calculation(self, analytics_service):
        """Test error handling in trend calculation methods."""
        # Setup - Mock database to raise exception
        analytics_service.session.execute.side_effect = Exception("Database connection lost")

        filters = [Customer.is_deleted == False]

        # Execute
        result = await analytics_service._get_customer_trend(filters, "day")

        # Assert - Should return empty list on error
        assert result == []

    async def test_time_range_granularity_selection(self, analytics_service):
        """Test that proper granularity is selected for different time ranges."""
        filters = [Customer.is_deleted == False]

        # Mock the trend methods to track calls
        with patch.object(analytics_service, '_get_customer_trend', return_value=[]) as mock_customer:
            with patch.object(analytics_service, '_get_message_trend', return_value=[]) as mock_message:
                with patch.object(analytics_service, '_get_sentiment_trend', return_value=[]) as mock_sentiment:

                    # Test TODAY -> hour granularity
                    await analytics_service._get_trend_data(filters, TimeRange.TODAY)
                    mock_customer.assert_called_with(filters, "hour")
                    mock_message.assert_called_with(filters, "hour")
                    mock_sentiment.assert_called_with(filters, "hour")

                    # Reset mocks
                    mock_customer.reset_mock()
                    mock_message.reset_mock()
                    mock_sentiment.reset_mock()

                    # Test MONTH -> day granularity
                    await analytics_service._get_trend_data(filters, TimeRange.MONTH)
                    mock_customer.assert_called_with(filters, "day")
                    mock_message.assert_called_with(filters, "day")
                    mock_sentiment.assert_called_with(filters, "day")