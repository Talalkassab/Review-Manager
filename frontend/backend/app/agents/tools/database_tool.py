"""
Database operations tool for agent interactions with customer data
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from .base_tool import BaseAgentTool, ToolResult


class DatabaseTool(BaseAgentTool):
    """Tool for database operations including customer data management"""
    
    name: str = "database_operations"
    description: str = (
        "Perform database operations including customer queries, updates, "
        "and analytics data retrieval for restaurant AI agents."
    )
    
    def _validate_input(self, **kwargs) -> bool:
        """Validate database operation parameters"""
        operation = kwargs.get('operation')
        if not operation:
            self.logger.error("Operation parameter is required")
            return False
        
        valid_operations = [
            'get_customer', 'update_customer', 'get_customers',
            'get_visits', 'get_orders', 'get_messages',
            'get_feedback', 'get_analytics'
        ]
        
        if operation not in valid_operations:
            self.logger.error(f"Invalid operation: {operation}")
            return False
            
        return True
    
    def _execute(self, **kwargs) -> Dict[str, Any]:
        """Execute database operation"""
        operation = kwargs.get('operation')
        
        try:
            if operation == 'get_customer':
                return self._get_customer(kwargs.get('customer_id'))
            elif operation == 'get_customers':
                return self._get_customers(kwargs.get('filters', {}))
            elif operation == 'update_customer':
                return self._update_customer(
                    kwargs.get('customer_id'),
                    kwargs.get('data', {})
                )
            elif operation == 'get_visits':
                return self._get_visits(kwargs.get('customer_id'))
            elif operation == 'get_orders':
                return self._get_orders(kwargs.get('customer_id'))
            elif operation == 'get_messages':
                return self._get_messages(kwargs.get('customer_id'))
            elif operation == 'get_feedback':
                return self._get_feedback(kwargs.get('filters', {}))
            elif operation == 'get_analytics':
                return self._get_analytics(kwargs.get('metric'))
            else:
                raise ValueError(f"Unsupported operation: {operation}")
                
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Database operation failed: {str(e)}"
            ).dict()
    
    def _get_customer(self, customer_id: str) -> Dict[str, Any]:
        """Get customer data by ID"""
        # Mock implementation - in production would query actual database
        mock_customer = {
            "id": customer_id,
            "name": "Ahmed Al-Rahman",
            "phone": "+966501234567",
            "email": "ahmed@example.com",
            "preferred_language": "ar",
            "first_visit_date": "2024-01-15T19:30:00",
            "last_visit_date": "2024-08-10T20:15:00",
            "visit_count": 12,
            "total_spent": 2400.0,
            "average_order_value": 200.0,
            "favorite_dish": "Kabsa",
            "dietary_restrictions": [],
            "special_occasions": ["birthday"],
            "tier": "gold",
            "sentiment_history": ["positive", "positive", "neutral"],
            "response_rate": 0.8
        }
        
        return ToolResult(
            success=True,
            data=mock_customer,
            metadata={"source": "customer_database"}
        ).dict()
    
    def _get_customers(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get customers based on filters"""
        # Mock implementation
        mock_customers = [
            {
                "id": "cust_001",
                "name": "Ahmed Al-Rahman",
                "last_visit_days_ago": 3,
                "visit_count": 12,
                "sentiment": "positive"
            },
            {
                "id": "cust_002", 
                "name": "Fatima Al-Zahra",
                "last_visit_days_ago": 15,
                "visit_count": 6,
                "sentiment": "neutral"
            },
            {
                "id": "cust_003",
                "name": "Omar Hassan",
                "last_visit_days_ago": 45,
                "visit_count": 20,
                "sentiment": "negative"
            }
        ]
        
        # Apply filters (simplified)
        filtered_customers = mock_customers
        
        if filters.get('min_visits'):
            filtered_customers = [c for c in filtered_customers 
                                if c['visit_count'] >= filters['min_visits']]
        
        if filters.get('sentiment'):
            filtered_customers = [c for c in filtered_customers 
                                if c['sentiment'] == filters['sentiment']]
        
        return ToolResult(
            success=True,
            data={"customers": filtered_customers, "total": len(filtered_customers)},
            metadata={"filters_applied": filters}
        ).dict()
    
    def _update_customer(self, customer_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update customer data"""
        # Mock implementation
        updated_fields = list(data.keys())
        
        return ToolResult(
            success=True,
            data={"customer_id": customer_id, "updated_fields": updated_fields},
            metadata={"update_timestamp": datetime.now().isoformat()}
        ).dict()
    
    def _get_visits(self, customer_id: str) -> Dict[str, Any]:
        """Get customer visit history"""
        # Mock implementation
        mock_visits = [
            {
                "id": "visit_001",
                "date": "2024-08-10T20:15:00",
                "duration_minutes": 75,
                "party_size": 4,
                "table_number": 12,
                "total_spent": 280.0,
                "occasion": "family_dinner"
            },
            {
                "id": "visit_002",
                "date": "2024-08-01T19:30:00", 
                "duration_minutes": 60,
                "party_size": 2,
                "table_number": 8,
                "total_spent": 150.0,
                "occasion": "date_night"
            }
        ]
        
        return ToolResult(
            success=True,
            data={"visits": mock_visits, "total_visits": len(mock_visits)},
            metadata={"customer_id": customer_id}
        ).dict()
    
    def _get_orders(self, customer_id: str) -> Dict[str, Any]:
        """Get customer order history"""
        # Mock implementation
        mock_orders = [
            {
                "id": "order_001",
                "date": "2024-08-10T20:15:00",
                "items": [
                    {"name": "Kabsa", "price": 85.0, "quantity": 2},
                    {"name": "Hummus", "price": 25.0, "quantity": 1},
                    {"name": "Arabic Coffee", "price": 15.0, "quantity": 4}
                ],
                "total": 280.0,
                "special_requests": ["extra spicy", "no onions"]
            }
        ]
        
        return ToolResult(
            success=True,
            data={"orders": mock_orders, "total_orders": len(mock_orders)},
            metadata={"customer_id": customer_id}
        ).dict()
    
    def _get_messages(self, customer_id: str) -> Dict[str, Any]:
        """Get message history with customer"""
        # Mock implementation
        mock_messages = [
            {
                "id": "msg_001",
                "timestamp": "2024-08-11T10:30:00",
                "direction": "outbound",
                "content": "شكراً لزيارتكم أمس، كيف كانت التجربة؟",
                "status": "delivered",
                "response_received": True
            },
            {
                "id": "msg_002", 
                "timestamp": "2024-08-11T14:20:00",
                "direction": "inbound",
                "content": "الطعام كان ممتاز والخدمة رائعة، شكراً لكم",
                "sentiment": "positive"
            }
        ]
        
        return ToolResult(
            success=True,
            data={"messages": mock_messages, "total_messages": len(mock_messages)},
            metadata={"customer_id": customer_id}
        ).dict()
    
    def _get_feedback(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get feedback data based on filters"""
        # Mock implementation
        mock_feedback = [
            {
                "id": "feedback_001",
                "customer_id": "cust_001",
                "date": "2024-08-11T14:20:00",
                "content": "الطعام كان ممتاز والخدمة رائعة",
                "sentiment": "positive",
                "rating": 5,
                "category": "food_service"
            },
            {
                "id": "feedback_002",
                "customer_id": "cust_003", 
                "date": "2024-08-09T21:45:00",
                "content": "الانتظار كان طويل والطعام بارد",
                "sentiment": "negative",
                "rating": 2,
                "category": "service_timing"
            }
        ]
        
        # Apply filters
        filtered_feedback = mock_feedback
        
        if filters.get('sentiment'):
            filtered_feedback = [f for f in filtered_feedback 
                               if f['sentiment'] == filters['sentiment']]
        
        if filters.get('date_from'):
            # Would filter by date in production
            pass
        
        return ToolResult(
            success=True,
            data={"feedback": filtered_feedback, "total": len(filtered_feedback)},
            metadata={"filters_applied": filters}
        ).dict()
    
    def _get_analytics(self, metric: str) -> Dict[str, Any]:
        """Get analytics metrics"""
        # Mock implementation
        analytics_data = {
            "customer_satisfaction": {
                "overall_score": 4.2,
                "positive_percentage": 75.0,
                "negative_percentage": 10.0,
                "neutral_percentage": 15.0,
                "total_responses": 150
            },
            "response_rates": {
                "overall_rate": 0.68,
                "arabic_customers": 0.75,
                "english_customers": 0.60,
                "by_customer_tier": {
                    "vip": 0.85,
                    "gold": 0.72,
                    "silver": 0.65,
                    "bronze": 0.58
                }
            },
            "visit_patterns": {
                "average_visits_per_month": 2.3,
                "peak_hours": ["19:00", "20:00", "21:00"],
                "popular_days": ["Friday", "Saturday", "Sunday"]
            }
        }
        
        data = analytics_data.get(metric, {})
        
        return ToolResult(
            success=True,
            data=data,
            metadata={"metric": metric, "generated_at": datetime.now().isoformat()}
        ).dict()