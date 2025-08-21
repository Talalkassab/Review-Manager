"""
Agent tools for the Restaurant AI Customer Feedback system.
"""

from .base_tool import BaseAgentTool, ToolResult
from .whatsapp_tool import WhatsAppTool
from .openrouter_tool import OpenRouterTool
from .database_tool import DatabaseTool
from .analytics_tool import AnalyticsTool
from .predictive_modeling_tool import PredictiveModelingTool
from .text_processing_tool import TextProcessingTool
from .template_engine import TemplateEngine

# Create simplified tool aliases for agent imports
TranslationTool = TextProcessingTool  # Alias for translation functionality
CulturalValidationTool = TextProcessingTool  # Alias for cultural validation
EmotionDetectionTool = TextProcessingTool  # Alias for emotion detection
PersonalizationTool = TemplateEngine  # Alias for personalization

# Legacy imports (kept for compatibility)
SentimentAnalysisTool = TextProcessingTool
CustomerDatabaseTool = DatabaseTool
CampaignExecutionTool = WhatsAppTool
PerformanceTrackingTool = AnalyticsTool

__all__ = [
    'BaseAgentTool',
    'ToolResult',
    'WhatsAppTool',
    'OpenRouterTool', 
    'DatabaseTool',
    'AnalyticsTool',
    'PredictiveModelingTool',
    'TextProcessingTool',
    'TemplateEngine',
    'TranslationTool',
    'CulturalValidationTool',
    'EmotionDetectionTool',
    'PersonalizationTool',
    # Legacy exports
    'SentimentAnalysisTool',
    'CustomerDatabaseTool',
    'CampaignExecutionTool',
    'PerformanceTrackingTool'
]