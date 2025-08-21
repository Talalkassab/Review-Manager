"""Campaign management services."""

from .execution import CampaignExecutionService, CampaignWebSocketManager
from .analytics import CampaignAnalyticsService
from .segmentation import CustomerSegmentationService
from .ab_testing import ABTestingService
# from .timing import TimingOptimizationService  # TODO: Implement timing optimization
from .personalization import PersonalizationEngine

# Stub class for missing module
class TimingOptimizationService:
    """Stub for timing optimization service - to be implemented."""
    pass

__all__ = [
    "CampaignExecutionService",
    "CampaignAnalyticsService", 
    "CustomerSegmentationService",
    "ABTestingService",
    "TimingOptimizationService",
    "PersonalizationEngine",
    "CampaignWebSocketManager"
]