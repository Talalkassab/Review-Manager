"""
Base tool class for all agent tools with error handling and logging.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from crewai_tools import BaseTool
from pydantic import BaseModel, Field

from ...core.config import settings
from ...core.logging import get_agent_logger


class BaseAgentTool(BaseTool, ABC):
    """Base class for all agent tools with standardized error handling and logging."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = get_agent_logger(self.__class__.__name__)
        self.max_retries = 3
        self.retry_delay = 1.0
    
    def _handle_error(self, error: Exception, operation: str) -> Dict[str, Any]:
        """Standardized error handling for all tools."""
        self.logger.error(f"Error in {operation}: {str(error)}")
        return {
            "success": False,
            "error": str(error),
            "operation": operation,
            "tool": self.__class__.__name__
        }
    
    def _log_success(self, operation: str, result: Any = None) -> None:
        """Log successful operations."""
        msg = f"Successfully completed {operation}"
        if result and isinstance(result, (str, int, float)):
            msg += f" | Result: {result}"
        self.logger.info(msg)
    
    def _validate_input(self, **kwargs) -> bool:
        """Override in subclasses to validate input parameters."""
        return True
    
    @abstractmethod
    def _execute(self, **kwargs) -> Dict[str, Any]:
        """Override in subclasses to implement the main tool logic."""
        pass
    
    def run(self, **kwargs) -> Dict[str, Any]:
        """Main execution method with error handling and logging."""
        operation = f"{self.__class__.__name__}.run"
        
        try:
            # Validate inputs
            if not self._validate_input(**kwargs):
                return self._handle_error(
                    ValueError("Invalid input parameters"), 
                    operation
                )
            
            # Execute the main logic
            result = self._execute(**kwargs)
            
            # Log success
            self._log_success(operation, result.get('data'))
            
            return result
            
        except Exception as e:
            return self._handle_error(e, operation)


class ToolResult(BaseModel):
    """Standardized tool result format."""
    success: bool = Field(description="Whether the operation was successful")
    data: Optional[Any] = Field(default=None, description="The result data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")