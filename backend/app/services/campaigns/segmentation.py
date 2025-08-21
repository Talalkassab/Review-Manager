"""
Customer segmentation service for campaign targeting.
Provides advanced customer segmentation based on behavior, demographics, and preferences.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text

from ...core.logging import get_logger
from ...models import Customer, Campaign, CampaignRecipient, WhatsAppMessage

logger = get_logger(__name__)


class CustomerSegmentationService:
    """Service for advanced customer segmentation and targeting."""
    
    def __init__(self):
        self.segment_definitions = {
            "new_customers": {
                "description": "First-time customers",
                "criteria": {"visit_count_max": 1}
            },
            "loyal_customers": {
                "description": "Customers with multiple visits",
                "criteria": {"visit_count_min": 3}
            },
            "high_value": {
                "description": "Customers with high order values",
                "criteria": {"order_total_min": 200}
            },
            "medium_value": {
                "description": "Customers with medium order values", 
                "criteria": {"order_total_min": 100, "order_total_max": 200}
            },
            "low_value": {
                "description": "Customers with low order values",
                "criteria": {"order_total_max": 100}
            },
            "recent_visitors": {
                "description": "Customers who visited recently",
                "criteria": {"visit_days_ago_max": 7}
            },
            "inactive_customers": {
                "description": "Customers who haven't visited recently",
                "criteria": {"visit_days_ago_min": 30}
            },
            "large_parties": {
                "description": "Customers with large party sizes",
                "criteria": {"party_size_min": 5}
            },
            "responsive_customers": {
                "description": "Customers who typically respond to messages",
                "criteria": {"response_rate_min": 50}
            },
            "unresponsive_customers": {
                "description": "Customers who rarely respond",
                "criteria": {"response_rate_max": 10}
            }
        }
    
    async def segment_customers(
        self,
        customers: List[Customer],
        targeting_config: Dict[str, Any],
        session: AsyncSession
    ) -> List[Customer]:
        """Segment customers based on targeting configuration."""
        try:
            # Start with all provided customers
            filtered_customers = customers.copy()
            
            # Apply demographic filters
            filtered_customers = await self._apply_demographic_filters(
                filtered_customers, targeting_config, session
            )
            
            # Apply behavioral filters
            filtered_customers = await self._apply_behavioral_filters(
                filtered_customers, targeting_config, session
            )
            
            # Apply geographic filters
            filtered_customers = await self._apply_geographic_filters(
                filtered_customers, targeting_config, session
            )
            
            # Apply engagement filters
            filtered_customers = await self._apply_engagement_filters(
                filtered_customers, targeting_config, session
            )
            
            # Apply custom segment filters
            filtered_customers = await self._apply_custom_segments(
                filtered_customers, targeting_config, session
            )
            
            logger.info(f"Segmented {len(customers)} customers down to {len(filtered_customers)} based on targeting config")
            
            return filtered_customers
            
        except Exception as e:
            logger.error(f"Customer segmentation failed: {str(e)}")
            return customers  # Return original list on error
    
    async def _apply_demographic_filters(
        self,
        customers: List[Customer],
        targeting_config: Dict[str, Any],
        session: AsyncSession
    ) -> List[Customer]:
        """Apply demographic filters."""
        filtered_customers = []
        
        # Language filter
        preferred_languages = targeting_config.get("preferred_language", [])
        if preferred_languages:
            filtered_customers = [
                c for c in customers 
                if c.preferred_language in preferred_languages
            ]
        else:
            filtered_customers = customers.copy()
        
        # Party size filter
        party_size_min = targeting_config.get("party_size_min")
        party_size_max = targeting_config.get("party_size_max")
        
        if party_size_min is not None:
            filtered_customers = [
                c for c in filtered_customers
                if c.party_size >= party_size_min
            ]
        
        if party_size_max is not None:
            filtered_customers = [
                c for c in filtered_customers
                if c.party_size <= party_size_max
            ]
        
        return filtered_customers
    
    async def _apply_behavioral_filters(
        self,
        customers: List[Customer],
        targeting_config: Dict[str, Any],
        session: AsyncSession
    ) -> List[Customer]:
        """Apply behavioral filters based on visit and order history."""
        filtered_customers = customers.copy()
        
        # Order value filters
        order_total_min = targeting_config.get("order_total_min")
        order_total_max = targeting_config.get("order_total_max")
        
        if order_total_min is not None:
            filtered_customers = [
                c for c in filtered_customers
                if (c.order_total or 0) >= order_total_min
            ]
        
        if order_total_max is not None:
            filtered_customers = [
                c for c in filtered_customers
                if (c.order_total or 0) <= order_total_max
            ]
        
        # Visit recency filters
        visit_days_ago_min = targeting_config.get("visit_days_ago_min")
        visit_days_ago_max = targeting_config.get("visit_days_ago_max")
        
        if visit_days_ago_min is not None or visit_days_ago_max is not None:
            now = datetime.utcnow()
            
            if visit_days_ago_min is not None:
                cutoff_date_max = now - timedelta(days=visit_days_ago_min)
                filtered_customers = [
                    c for c in filtered_customers
                    if c.visit_date and c.visit_date <= cutoff_date_max
                ]
            
            if visit_days_ago_max is not None:
                cutoff_date_min = now - timedelta(days=visit_days_ago_max)
                filtered_customers = [
                    c for c in filtered_customers
                    if c.visit_date and c.visit_date >= cutoff_date_min
                ]
        
        # Special requests filter
        has_special_requests = targeting_config.get("has_special_requests")
        if has_special_requests is not None:
            if has_special_requests:
                filtered_customers = [
                    c for c in filtered_customers
                    if c.special_requests and c.special_requests.strip()
                ]
            else:
                filtered_customers = [
                    c for c in filtered_customers
                    if not c.special_requests or not c.special_requests.strip()
                ]
        
        return filtered_customers
    
    async def _apply_geographic_filters(
        self,
        customers: List[Customer],
        targeting_config: Dict[str, Any],
        session: AsyncSession
    ) -> List[Customer]:
        """Apply geographic filters (placeholder for future implementation)."""
        # For now, return customers as-is
        # Future implementation could include location-based filtering
        return customers
    
    async def _apply_engagement_filters(
        self,
        customers: List[Customer],
        targeting_config: Dict[str, Any],
        session: AsyncSession
    ) -> List[Customer]:
        """Apply engagement-based filters."""
        # WhatsApp opt-in filter
        whatsapp_opt_in = targeting_config.get("whatsapp_opt_in")
        if whatsapp_opt_in is not None:
            customers = [
                c for c in customers
                if c.whatsapp_opt_in == whatsapp_opt_in
            ]
        
        # Email opt-in filter
        email_opt_in = targeting_config.get("email_opt_in")
        if email_opt_in is not None:
            customers = [
                c for c in customers
                if c.email_opt_in == email_opt_in
            ]
        
        # Response rate filter (requires database query)
        response_rate_min = targeting_config.get("response_rate_min")
        response_rate_max = targeting_config.get("response_rate_max")
        
        if response_rate_min is not None or response_rate_max is not None:
            customers = await self._filter_by_response_rate(
                customers, response_rate_min, response_rate_max, session
            )
        
        return customers
    
    async def _filter_by_response_rate(
        self,
        customers: List[Customer],
        response_rate_min: Optional[float],
        response_rate_max: Optional[float],
        session: AsyncSession
    ) -> List[Customer]:
        """Filter customers by their historical response rate."""
        if not customers:
            return customers
        
        customer_ids = [c.id for c in customers]
        
        # Calculate response rates for each customer
        stmt = text("""
            SELECT 
                c.id,
                COUNT(wm.id) as total_messages,
                SUM(CASE WHEN cr.has_responded = true THEN 1 ELSE 0 END) as responses,
                CASE 
                    WHEN COUNT(wm.id) > 0 THEN 
                        (SUM(CASE WHEN cr.has_responded = true THEN 1 ELSE 0 END)::float / COUNT(wm.id) * 100)
                    ELSE 0 
                END as response_rate
            FROM customers c
            LEFT JOIN whatsapp_messages wm ON c.id = wm.customer_id
            LEFT JOIN campaign_recipients cr ON wm.id = cr.message_id
            WHERE c.id = ANY(:customer_ids)
            GROUP BY c.id
        """)
        
        result = await session.execute(stmt, {"customer_ids": customer_ids})
        response_rates = {row[0]: row[3] for row in result}
        
        # Filter customers based on response rate
        filtered_customers = []
        for customer in customers:
            customer_response_rate = response_rates.get(customer.id, 0)
            
            include_customer = True
            
            if response_rate_min is not None and customer_response_rate < response_rate_min:
                include_customer = False
            
            if response_rate_max is not None and customer_response_rate > response_rate_max:
                include_customer = False
            
            if include_customer:
                filtered_customers.append(customer)
        
        return filtered_customers
    
    async def _apply_custom_segments(
        self,
        customers: List[Customer],
        targeting_config: Dict[str, Any],
        session: AsyncSession
    ) -> List[Customer]:
        """Apply custom segment filters."""
        customer_segments = targeting_config.get("customer_segments", [])
        
        if not customer_segments:
            return customers
        
        # Apply each segment filter
        for segment_name in customer_segments:
            if segment_name in self.segment_definitions:
                customers = await self._apply_segment_criteria(
                    customers, self.segment_definitions[segment_name]["criteria"], session
                )
            else:
                logger.warning(f"Unknown customer segment: {segment_name}")
        
        return customers
    
    async def _apply_segment_criteria(
        self,
        customers: List[Customer],
        criteria: Dict[str, Any],
        session: AsyncSession
    ) -> List[Customer]:
        """Apply specific segment criteria to customers."""
        filtered_customers = customers.copy()
        
        # Visit count criteria (requires database query)
        visit_count_min = criteria.get("visit_count_min")
        visit_count_max = criteria.get("visit_count_max")
        
        if visit_count_min is not None or visit_count_max is not None:
            filtered_customers = await self._filter_by_visit_count(
                filtered_customers, visit_count_min, visit_count_max, session
            )
        
        # Order total criteria
        order_total_min = criteria.get("order_total_min")
        order_total_max = criteria.get("order_total_max")
        
        if order_total_min is not None:
            filtered_customers = [
                c for c in filtered_customers
                if (c.order_total or 0) >= order_total_min
            ]
        
        if order_total_max is not None:
            filtered_customers = [
                c for c in filtered_customers
                if (c.order_total or 0) <= order_total_max
            ]
        
        # Visit days ago criteria
        visit_days_ago_min = criteria.get("visit_days_ago_min")
        visit_days_ago_max = criteria.get("visit_days_ago_max")
        
        if visit_days_ago_min is not None or visit_days_ago_max is not None:
            now = datetime.utcnow()
            
            if visit_days_ago_min is not None:
                cutoff_date = now - timedelta(days=visit_days_ago_min)
                filtered_customers = [
                    c for c in filtered_customers
                    if c.visit_date and c.visit_date <= cutoff_date
                ]
            
            if visit_days_ago_max is not None:
                cutoff_date = now - timedelta(days=visit_days_ago_max)
                filtered_customers = [
                    c for c in filtered_customers
                    if c.visit_date and c.visit_date >= cutoff_date
                ]
        
        # Party size criteria
        party_size_min = criteria.get("party_size_min")
        if party_size_min is not None:
            filtered_customers = [
                c for c in filtered_customers
                if c.party_size >= party_size_min
            ]
        
        # Response rate criteria
        response_rate_min = criteria.get("response_rate_min")
        response_rate_max = criteria.get("response_rate_max")
        
        if response_rate_min is not None or response_rate_max is not None:
            filtered_customers = await self._filter_by_response_rate(
                filtered_customers, response_rate_min, response_rate_max, session
            )
        
        return filtered_customers
    
    async def _filter_by_visit_count(
        self,
        customers: List[Customer],
        visit_count_min: Optional[int],
        visit_count_max: Optional[int],
        session: AsyncSession
    ) -> List[Customer]:
        """Filter customers by visit count (simplified - assumes one visit per customer record)."""
        # In a real implementation, you'd have a separate visits table
        # For now, we'll use a simplified approach based on customer records
        
        if not customers:
            return customers
        
        customer_ids = [c.id for c in customers]
        
        # Query visit counts (simplified - using message counts as proxy)
        stmt = text("""
            SELECT 
                customer_id,
                COUNT(DISTINCT DATE(created_at)) as visit_days
            FROM whatsapp_messages
            WHERE customer_id = ANY(:customer_ids)
            AND direction = 'inbound'
            GROUP BY customer_id
        """)
        
        result = await session.execute(stmt, {"customer_ids": customer_ids})
        visit_counts = {row[0]: row[1] for row in result}
        
        filtered_customers = []
        for customer in customers:
            visit_count = visit_counts.get(customer.id, 1)  # Default to 1 if no messages
            
            include_customer = True
            
            if visit_count_min is not None and visit_count < visit_count_min:
                include_customer = False
            
            if visit_count_max is not None and visit_count > visit_count_max:
                include_customer = False
            
            if include_customer:
                filtered_customers.append(customer)
        
        return filtered_customers
    
    async def analyze_customer_segments(
        self,
        restaurant_id: UUID,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Analyze customer segments for a restaurant."""
        try:
            # Get all customers for the restaurant
            stmt = select(Customer).where(Customer.restaurant_id == restaurant_id)
            result = await session.execute(stmt)
            customers = result.scalars().all()
            
            if not customers:
                return {"message": "No customers found"}
            
            # Analyze each segment
            segment_analysis = {}
            
            for segment_name, segment_info in self.segment_definitions.items():
                # Apply segment criteria
                segment_customers = await self._apply_segment_criteria(
                    customers, segment_info["criteria"], session
                )
                
                # Calculate segment metrics
                segment_size = len(segment_customers)
                segment_percentage = (segment_size / len(customers)) * 100
                
                # Calculate average order value for segment
                avg_order_value = sum(c.order_total or 0 for c in segment_customers) / segment_size if segment_size > 0 else 0
                
                # Calculate response rate for segment
                response_rate = await self._calculate_segment_response_rate(
                    segment_customers, session
                )
                
                segment_analysis[segment_name] = {
                    "description": segment_info["description"],
                    "customer_count": segment_size,
                    "percentage_of_total": round(segment_percentage, 2),
                    "avg_order_value": round(avg_order_value, 2),
                    "avg_response_rate": round(response_rate, 2)
                }
            
            # Overall statistics
            total_customers = len(customers)
            overall_avg_order = sum(c.order_total or 0 for c in customers) / total_customers
            
            return {
                "total_customers": total_customers,
                "overall_avg_order_value": round(overall_avg_order, 2),
                "segments": segment_analysis,
                "top_segments_by_size": sorted(
                    segment_analysis.items(),
                    key=lambda x: x[1]["customer_count"],
                    reverse=True
                )[:5],
                "top_segments_by_value": sorted(
                    segment_analysis.items(),
                    key=lambda x: x[1]["avg_order_value"],
                    reverse=True
                )[:5]
            }
            
        except Exception as e:
            logger.error(f"Segment analysis failed: {str(e)}")
            return {"error": str(e)}
    
    async def _calculate_segment_response_rate(
        self,
        customers: List[Customer],
        session: AsyncSession
    ) -> float:
        """Calculate average response rate for a customer segment."""
        if not customers:
            return 0.0
        
        customer_ids = [c.id for c in customers]
        
        stmt = text("""
            SELECT 
                AVG(
                    CASE 
                        WHEN COUNT(wm.id) > 0 THEN 
                            (SUM(CASE WHEN cr.has_responded = true THEN 1 ELSE 0 END)::float / COUNT(wm.id) * 100)
                        ELSE 0 
                    END
                ) as avg_response_rate
            FROM customers c
            LEFT JOIN whatsapp_messages wm ON c.id = wm.customer_id
            LEFT JOIN campaign_recipients cr ON wm.id = cr.message_id
            WHERE c.id = ANY(:customer_ids)
            GROUP BY c.id
        """)
        
        result = await session.execute(stmt, {"customer_ids": customer_ids})
        row = result.fetchone()
        
        return row[0] or 0.0 if row else 0.0
    
    def get_segment_recommendations(
        self,
        campaign_type: str,
        historical_performance: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get segment recommendations for a campaign type."""
        recommendations = []
        
        # Campaign type specific recommendations
        if campaign_type == "feedback_survey":
            recommendations.extend([
                {
                    "segment": "recent_visitors",
                    "reason": "Recent visitors have fresh experience to provide feedback",
                    "priority": "high"
                },
                {
                    "segment": "high_value",
                    "reason": "High-value customers provide valuable feedback",
                    "priority": "high"
                },
                {
                    "segment": "responsive_customers",
                    "reason": "These customers are more likely to complete surveys",
                    "priority": "medium"
                }
            ])
        
        elif campaign_type == "promotion":
            recommendations.extend([
                {
                    "segment": "loyal_customers",
                    "reason": "Loyal customers appreciate exclusive offers",
                    "priority": "high"
                },
                {
                    "segment": "inactive_customers",
                    "reason": "Promotions can re-engage inactive customers",
                    "priority": "high"
                },
                {
                    "segment": "high_value",
                    "reason": "High-value customers are worth retaining",
                    "priority": "medium"
                }
            ])
        
        elif campaign_type == "welcome":
            recommendations.extend([
                {
                    "segment": "new_customers",
                    "reason": "Welcome new customers to build relationship",
                    "priority": "high"
                }
            ])
        
        else:
            # General recommendations
            recommendations.extend([
                {
                    "segment": "responsive_customers",
                    "reason": "Higher likelihood of engagement",
                    "priority": "medium"
                },
                {
                    "segment": "recent_visitors",
                    "reason": "Recent interaction increases relevance",
                    "priority": "medium"
                }
            ])
        
        return recommendations
    
    def create_custom_segment(
        self,
        name: str,
        description: str,
        criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a custom segment definition."""
        if name in self.segment_definitions:
            raise ValueError(f"Segment '{name}' already exists")
        
        custom_segment = {
            "description": description,
            "criteria": criteria,
            "is_custom": True,
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.segment_definitions[name] = custom_segment
        
        logger.info(f"Created custom segment: {name}")
        return custom_segment
    
    def get_available_segments(self) -> Dict[str, Any]:
        """Get all available customer segments."""
        return {
            "predefined_segments": {
                name: info for name, info in self.segment_definitions.items()
                if not info.get("is_custom", False)
            },
            "custom_segments": {
                name: info for name, info in self.segment_definitions.items()
                if info.get("is_custom", False)
            },
            "total_segments": len(self.segment_definitions)
        }