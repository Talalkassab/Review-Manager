"""
Campaign analytics and reporting service.
Provides comprehensive analytics, ROI calculation, and customer journey mapping.
"""
import json
import io
import csv
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, AsyncGenerator
from uuid import UUID
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
from sqlalchemy.orm import selectinload

from ...core.logging import get_logger
from ...models import Campaign, CampaignRecipient, Customer, WhatsAppMessage, Restaurant

logger = get_logger(__name__)


class CampaignAnalyticsService:
    """Service for campaign analytics and reporting."""
    
    def __init__(self):
        pass
    
    async def get_comprehensive_analytics(
        self,
        campaign: Campaign,
        session: AsyncSession,
        period: str = "24h"
    ) -> Dict[str, Any]:
        """Get comprehensive campaign analytics."""
        try:
            # Base analytics from campaign model
            base_metrics = campaign.get_performance_summary()
            
            # Time-based analytics
            time_analytics = await self._get_time_based_analytics(campaign, period, session)
            
            # Customer segment analytics
            segment_analytics = await self._get_segment_analytics(campaign, session)
            
            # ROI metrics
            roi_metrics = await self._calculate_roi_metrics(campaign, session)
            
            # Comparative analytics
            comparative_metrics = await self._get_comparative_metrics(campaign, session)
            
            # Predictive metrics
            predictive_metrics = await self._get_predictive_metrics(campaign, session)
            
            return {
                "period": period,
                "total_campaigns": 1,
                "active_campaigns": 1 if campaign.is_running else 0,
                "completed_campaigns": 1 if campaign.is_completed else 0,
                "cancelled_campaigns": 1 if campaign.status == "cancelled" else 0,
                "total_messages_sent": base_metrics["messages_sent"],
                "average_delivery_rate": base_metrics["delivery_rate"],
                "average_response_rate": base_metrics["response_rate"],
                "total_cost_usd": base_metrics["actual_cost_usd"],
                "roi_metrics": roi_metrics,
                "time_analytics": time_analytics,
                "segment_analytics": segment_analytics,
                "comparative_metrics": comparative_metrics,
                "predictive_metrics": predictive_metrics,
                "best_performing_types": await self._get_best_performing_types(session, campaign.restaurant_id),
                "optimal_send_times": await self._get_optimal_send_times(session, campaign.restaurant_id)
            }
            
        except Exception as e:
            logger.error(f"Analytics calculation failed: {str(e)}")
            raise
    
    async def _get_time_based_analytics(
        self,
        campaign: Campaign,
        period: str,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Get time-based performance analytics."""
        try:
            # Calculate period boundaries
            end_date = datetime.utcnow()
            if period == "1h":
                start_date = end_date - timedelta(hours=1)
                interval = "10 minutes"
            elif period == "24h":
                start_date = end_date - timedelta(days=1)
                interval = "1 hour"
            elif period == "7d":
                start_date = end_date - timedelta(days=7)
                interval = "1 day"
            elif period == "30d":
                start_date = end_date - timedelta(days=30)
                interval = "1 day"
            else:
                start_date = end_date - timedelta(days=1)
                interval = "1 hour"
            
            # Query hourly message sending performance
            stmt = text("""
                SELECT 
                    DATE_TRUNC(:interval, wm.sent_at) as time_bucket,
                    COUNT(*) as messages_sent,
                    SUM(CASE WHEN wm.status = 'delivered' THEN 1 ELSE 0 END) as delivered,
                    SUM(CASE WHEN wm.status = 'read' THEN 1 ELSE 0 END) as read,
                    SUM(CASE WHEN wm.status = 'failed' THEN 1 ELSE 0 END) as failed,
                    SUM(CASE WHEN cr.has_responded = true THEN 1 ELSE 0 END) as responded
                FROM whatsapp_messages wm
                LEFT JOIN campaign_recipients cr ON wm.id = cr.message_id
                WHERE wm.campaign_id = :campaign_id
                AND wm.sent_at BETWEEN :start_date AND :end_date
                GROUP BY DATE_TRUNC(:interval, wm.sent_at)
                ORDER BY time_bucket ASC
            """)
            
            result = await session.execute(stmt, {
                "campaign_id": campaign.id,
                "start_date": start_date,
                "end_date": end_date,
                "interval": interval
            })
            
            hourly_data = []
            for row in result:
                hourly_data.append({
                    "time": row[0].isoformat() if row[0] else None,
                    "sent": row[1] or 0,
                    "delivered": row[2] or 0,
                    "read": row[3] or 0,
                    "failed": row[4] or 0,
                    "responded": row[5] or 0,
                    "delivery_rate": (row[2] / row[1] * 100) if row[1] > 0 else 0,
                    "response_rate": (row[5] / row[2] * 100) if row[2] > 0 else 0
                })
            
            # Calculate trends
            if len(hourly_data) >= 2:
                recent_rate = hourly_data[-1]["delivery_rate"] if hourly_data[-1] else 0
                previous_rate = hourly_data[-2]["delivery_rate"] if len(hourly_data) > 1 else 0
                trend = "improving" if recent_rate > previous_rate else "declining" if recent_rate < previous_rate else "stable"
            else:
                trend = "insufficient_data"
            
            return {
                "period": period,
                "hourly_breakdown": hourly_data,
                "trend": trend,
                "peak_hour": max(hourly_data, key=lambda x: x["delivered"]) if hourly_data else None,
                "total_data_points": len(hourly_data)
            }
            
        except Exception as e:
            logger.error(f"Time-based analytics failed: {str(e)}")
            return {"error": str(e)}
    
    async def _get_segment_analytics(
        self,
        campaign: Campaign,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Get customer segment performance analytics."""
        try:
            # Query segment performance
            stmt = text("""
                SELECT 
                    c.preferred_language,
                    CASE 
                        WHEN c.order_total > 200 THEN 'high_value'
                        WHEN c.order_total > 100 THEN 'medium_value'
                        ELSE 'low_value'
                    END as value_segment,
                    c.party_size,
                    COUNT(cr.id) as recipient_count,
                    SUM(CASE WHEN cr.status = 'delivered' THEN 1 ELSE 0 END) as delivered_count,
                    SUM(CASE WHEN cr.has_responded = true THEN 1 ELSE 0 END) as response_count,
                    AVG(c.order_total) as avg_order_value
                FROM campaign_recipients cr
                JOIN customers c ON cr.customer_id = c.id
                WHERE cr.campaign_id = :campaign_id
                GROUP BY c.preferred_language, value_segment, c.party_size
                ORDER BY response_count DESC
            """)
            
            result = await session.execute(stmt, {"campaign_id": campaign.id})
            
            segments = []
            for row in result:
                segments.append({
                    "language": row[0],
                    "value_segment": row[1],
                    "party_size": row[2],
                    "recipient_count": row[3],
                    "delivered_count": row[4],
                    "response_count": row[5],
                    "avg_order_value": float(row[6]) if row[6] else 0.0,
                    "delivery_rate": (row[4] / row[3] * 100) if row[3] > 0 else 0,
                    "response_rate": (row[5] / row[4] * 100) if row[4] > 0 else 0
                })
            
            # Find best performing segments
            best_segments = sorted(segments, key=lambda x: x["response_rate"], reverse=True)[:3]
            
            return {
                "segments": segments,
                "best_performing_segments": best_segments,
                "total_segments": len(segments),
                "language_distribution": self._calculate_language_distribution(segments),
                "value_segment_distribution": self._calculate_value_segment_distribution(segments)
            }
            
        except Exception as e:
            logger.error(f"Segment analytics failed: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_language_distribution(self, segments: List[Dict]) -> Dict[str, Any]:
        """Calculate language distribution from segments."""
        language_stats = {}
        
        for segment in segments:
            lang = segment["language"]
            if lang not in language_stats:
                language_stats[lang] = {"count": 0, "responses": 0, "delivered": 0}
            
            language_stats[lang]["count"] += segment["recipient_count"]
            language_stats[lang]["responses"] += segment["response_count"]
            language_stats[lang]["delivered"] += segment["delivered_count"]
        
        # Calculate rates
        for lang in language_stats:
            stats = language_stats[lang]
            stats["response_rate"] = (stats["responses"] / stats["delivered"] * 100) if stats["delivered"] > 0 else 0
        
        return language_stats
    
    def _calculate_value_segment_distribution(self, segments: List[Dict]) -> Dict[str, Any]:
        """Calculate value segment distribution from segments."""
        value_stats = {}
        
        for segment in segments:
            value_seg = segment["value_segment"]
            if value_seg not in value_stats:
                value_stats[value_seg] = {"count": 0, "responses": 0, "delivered": 0, "total_value": 0}
            
            value_stats[value_seg]["count"] += segment["recipient_count"]
            value_stats[value_seg]["responses"] += segment["response_count"]
            value_stats[value_seg]["delivered"] += segment["delivered_count"]
            value_stats[value_seg]["total_value"] += segment["avg_order_value"] * segment["recipient_count"]
        
        # Calculate rates and averages
        for seg in value_stats:
            stats = value_stats[seg]
            stats["response_rate"] = (stats["responses"] / stats["delivered"] * 100) if stats["delivered"] > 0 else 0
            stats["avg_order_value"] = stats["total_value"] / stats["count"] if stats["count"] > 0 else 0
        
        return value_stats
    
    async def _calculate_roi_metrics(
        self,
        campaign: Campaign,
        session: AsyncSession
    ) -> Dict[str, float]:
        """Calculate ROI and revenue metrics."""
        try:
            # Get revenue attribution (simplified calculation)
            stmt = text("""
                SELECT 
                    COUNT(cr.id) as responded_customers,
                    AVG(c.order_total) as avg_order_value,
                    SUM(c.order_total) as total_attributed_revenue
                FROM campaign_recipients cr
                JOIN customers c ON cr.customer_id = c.id
                WHERE cr.campaign_id = :campaign_id
                AND cr.has_responded = true
                AND c.visit_date >= :campaign_start
            """)
            
            campaign_start = campaign.started_at or campaign.created_at
            result = await session.execute(stmt, {
                "campaign_id": campaign.id,
                "campaign_start": campaign_start
            })
            
            row = result.fetchone()
            if row:
                responded_customers = row[0] or 0
                avg_order_value = float(row[1] or 0)
                total_revenue = float(row[2] or 0)
            else:
                responded_customers = 0
                avg_order_value = 0.0
                total_revenue = 0.0
            
            # Calculate ROI metrics
            campaign_cost = campaign.actual_cost_usd or 0.0
            
            roi = ((total_revenue - campaign_cost) / campaign_cost * 100) if campaign_cost > 0 else 0
            roas = (total_revenue / campaign_cost) if campaign_cost > 0 else 0
            cost_per_response = (campaign_cost / responded_customers) if responded_customers > 0 else 0
            revenue_per_recipient = total_revenue / campaign.recipients_count if campaign.recipients_count > 0 else 0
            
            return {
                "roi_percentage": round(roi, 2),
                "roas": round(roas, 2),
                "total_attributed_revenue": round(total_revenue, 2),
                "cost_per_response": round(cost_per_response, 2),
                "revenue_per_recipient": round(revenue_per_recipient, 2),
                "avg_order_value": round(avg_order_value, 2),
                "responded_customers": responded_customers
            }
            
        except Exception as e:
            logger.error(f"ROI calculation failed: {str(e)}")
            return {"error": str(e)}
    
    async def _get_comparative_metrics(
        self,
        campaign: Campaign,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Get comparative metrics against historical campaigns."""
        try:
            # Get average performance of similar campaigns
            stmt = text("""
                SELECT 
                    AVG(messages_sent) as avg_sent,
                    AVG(messages_delivered) as avg_delivered,
                    AVG(messages_read) as avg_read,
                    AVG(responses_received) as avg_responses,
                    AVG(actual_cost_usd) as avg_cost,
                    COUNT(*) as campaign_count
                FROM campaigns 
                WHERE restaurant_id = :restaurant_id
                AND campaign_type = :campaign_type
                AND status = 'completed'
                AND id != :campaign_id
                AND created_at >= :start_date
            """)
            
            start_date = datetime.utcnow() - timedelta(days=90)  # Last 90 days
            result = await session.execute(stmt, {
                "restaurant_id": campaign.restaurant_id,
                "campaign_type": campaign.campaign_type,
                "campaign_id": campaign.id,
                "start_date": start_date
            })
            
            row = result.fetchone()
            if row and row[5] > 0:  # campaign_count > 0
                avg_delivery_rate = (row[1] / row[0] * 100) if row[0] > 0 else 0
                avg_response_rate = (row[3] / row[1] * 100) if row[1] > 0 else 0
                
                # Compare with current campaign
                current_delivery_rate = campaign.delivery_rate
                current_response_rate = campaign.response_rate
                
                delivery_comparison = current_delivery_rate - avg_delivery_rate
                response_comparison = current_response_rate - avg_response_rate
                cost_comparison = campaign.actual_cost_usd - (row[4] or 0)
                
                return {
                    "historical_campaigns_count": int(row[5]),
                    "avg_delivery_rate": round(avg_delivery_rate, 2),
                    "avg_response_rate": round(avg_response_rate, 2),
                    "avg_cost": round(row[4] or 0, 2),
                    "delivery_rate_diff": round(delivery_comparison, 2),
                    "response_rate_diff": round(response_comparison, 2),
                    "cost_diff": round(cost_comparison, 2),
                    "performance_vs_average": "above" if delivery_comparison > 0 else "below" if delivery_comparison < 0 else "average"
                }
            else:
                return {
                    "historical_campaigns_count": 0,
                    "message": "No historical campaigns for comparison"
                }
                
        except Exception as e:
            logger.error(f"Comparative metrics failed: {str(e)}")
            return {"error": str(e)}
    
    async def _get_predictive_metrics(
        self,
        campaign: Campaign,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Get predictive analytics and forecasting."""
        try:
            if not campaign.is_running:
                return {"message": "Predictions only available for running campaigns"}
            
            # Predict completion time based on current rate
            current_rate = campaign.messages_sent / max(1, (datetime.utcnow() - campaign.started_at).total_seconds() / 3600) if campaign.started_at else 0
            remaining_messages = campaign.recipients_count - campaign.messages_sent
            
            if current_rate > 0:
                hours_remaining = remaining_messages / current_rate
                estimated_completion = datetime.utcnow() + timedelta(hours=hours_remaining)
            else:
                estimated_completion = None
            
            # Predict final metrics based on current trends
            current_delivery_rate = campaign.delivery_rate / 100
            current_response_rate = campaign.response_rate / 100
            
            predicted_delivered = int(campaign.recipients_count * current_delivery_rate)
            predicted_responses = int(predicted_delivered * current_response_rate)
            
            # Cost prediction
            cost_per_message = campaign.actual_cost_usd / max(1, campaign.messages_sent)
            predicted_total_cost = cost_per_message * campaign.recipients_count
            
            return {
                "estimated_completion": estimated_completion.isoformat() if estimated_completion else None,
                "predicted_final_delivered": predicted_delivered,
                "predicted_final_responses": predicted_responses,
                "predicted_total_cost": round(predicted_total_cost, 2),
                "current_sending_rate_per_hour": round(current_rate, 1),
                "confidence_level": "medium" if campaign.messages_sent > 10 else "low"
            }
            
        except Exception as e:
            logger.error(f"Predictive metrics failed: {str(e)}")
            return {"error": str(e)}
    
    async def _get_best_performing_types(
        self,
        session: AsyncSession,
        restaurant_id: UUID
    ) -> List[Dict[str, Any]]:
        """Get best performing campaign types."""
        try:
            stmt = text("""
                SELECT 
                    campaign_type,
                    COUNT(*) as campaign_count,
                    AVG(messages_delivered::float / NULLIF(messages_sent, 0) * 100) as avg_delivery_rate,
                    AVG(responses_received::float / NULLIF(messages_delivered, 0) * 100) as avg_response_rate,
                    SUM(actual_cost_usd) as total_cost
                FROM campaigns
                WHERE restaurant_id = :restaurant_id
                AND status = 'completed'
                AND created_at >= :start_date
                GROUP BY campaign_type
                HAVING COUNT(*) >= 2
                ORDER BY avg_response_rate DESC
                LIMIT 5
            """)
            
            start_date = datetime.utcnow() - timedelta(days=90)
            result = await session.execute(stmt, {
                "restaurant_id": restaurant_id,
                "start_date": start_date
            })
            
            types = []
            for row in result:
                types.append({
                    "campaign_type": row[0],
                    "campaign_count": int(row[1]),
                    "avg_delivery_rate": round(row[2] or 0, 2),
                    "avg_response_rate": round(row[3] or 0, 2),
                    "total_cost": round(row[4] or 0, 2)
                })
            
            return types
            
        except Exception as e:
            logger.error(f"Best performing types query failed: {str(e)}")
            return []
    
    async def _get_optimal_send_times(
        self,
        session: AsyncSession,
        restaurant_id: UUID
    ) -> List[Dict[str, Any]]:
        """Get optimal send times based on historical data."""
        try:
            stmt = text("""
                SELECT 
                    EXTRACT(HOUR FROM sent_at) as send_hour,
                    EXTRACT(DOW FROM sent_at) as day_of_week,
                    COUNT(*) as message_count,
                    AVG(CASE WHEN status IN ('delivered', 'read') THEN 1.0 ELSE 0.0 END) as success_rate
                FROM whatsapp_messages
                WHERE restaurant_id = :restaurant_id
                AND sent_at IS NOT NULL
                AND sent_at >= :start_date
                GROUP BY EXTRACT(HOUR FROM sent_at), EXTRACT(DOW FROM sent_at)
                HAVING COUNT(*) >= 5
                ORDER BY success_rate DESC
                LIMIT 10
            """)
            
            start_date = datetime.utcnow() - timedelta(days=30)
            result = await session.execute(stmt, {
                "restaurant_id": restaurant_id,
                "start_date": start_date
            })
            
            times = []
            for row in result:
                day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
                times.append({
                    "hour": int(row[0]),
                    "day_of_week": int(row[1]),
                    "day_name": day_names[int(row[1])],
                    "message_count": int(row[2]),
                    "success_rate": round(row[3] * 100, 2)
                })
            
            return times
            
        except Exception as e:
            logger.error(f"Optimal send times query failed: {str(e)}")
            return []
    
    async def map_customer_journey(
        self,
        campaign: Campaign,
        session: AsyncSession,
        customer_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Map customer journey for campaign analysis."""
        try:
            if customer_id:
                # Individual customer journey
                journey = await self._map_individual_journey(campaign, customer_id, session)
            else:
                # Aggregate journey mapping
                journey = await self._map_aggregate_journey(campaign, session)
            
            return journey
            
        except Exception as e:
            logger.error(f"Customer journey mapping failed: {str(e)}")
            return {"error": str(e)}
    
    async def _map_individual_journey(
        self,
        campaign: Campaign,
        customer_id: UUID,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Map journey for individual customer."""
        # Get customer and recipient data
        stmt = select(CampaignRecipient).where(
            and_(
                CampaignRecipient.campaign_id == campaign.id,
                CampaignRecipient.customer_id == customer_id
            )
        ).options(selectinload(CampaignRecipient.customer))
        
        result = await session.execute(stmt)
        recipient = result.scalar_one_or_none()
        
        if not recipient:
            return {"error": "Customer not found in campaign"}
        
        # Build journey timeline
        timeline = []
        
        if recipient.scheduled_send_time:
            timeline.append({
                "event": "scheduled",
                "timestamp": recipient.scheduled_send_time.isoformat(),
                "details": "Message scheduled for delivery"
            })
        
        if recipient.sent_at:
            timeline.append({
                "event": "sent",
                "timestamp": recipient.sent_at.isoformat(),
                "details": "Message sent to customer"
            })
        
        if recipient.delivered_at:
            timeline.append({
                "event": "delivered",
                "timestamp": recipient.delivered_at.isoformat(),
                "details": "Message delivered to customer device"
            })
        
        if recipient.responded_at:
            timeline.append({
                "event": "responded",
                "timestamp": recipient.responded_at.isoformat(),
                "details": f"Customer responded: {recipient.response_text[:50]}..." if recipient.response_text else "Customer responded"
            })
        
        return {
            "customer_id": str(customer_id),
            "customer_name": recipient.customer.first_name,
            "variant_id": recipient.variant_id,
            "personalization_applied": bool(recipient.personalization_data),
            "journey_timeline": timeline,
            "final_status": recipient.status,
            "response_sentiment": recipient.response_sentiment
        }
    
    async def _map_aggregate_journey(
        self,
        campaign: Campaign,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Map aggregate customer journey for campaign."""
        # Get journey stage statistics
        stmt = text("""
            SELECT 
                status,
                COUNT(*) as customer_count,
                AVG(EXTRACT(EPOCH FROM (responded_at - sent_at))/3600) as avg_response_time_hours
            FROM campaign_recipients
            WHERE campaign_id = :campaign_id
            GROUP BY status
        """)
        
        result = await session.execute(stmt, {"campaign_id": campaign.id})
        
        journey_stages = []
        total_customers = 0
        
        for row in result:
            customer_count = int(row[1])
            total_customers += customer_count
            
            journey_stages.append({
                "stage": row[0],
                "customer_count": customer_count,
                "avg_response_time_hours": round(row[2] or 0, 2) if row[2] else None
            })
        
        # Calculate conversion funnel
        stage_order = ["pending", "sent", "delivered", "read", "responded"]
        funnel = []
        
        for stage in stage_order:
            stage_data = next((s for s in journey_stages if s["stage"] == stage), None)
            if stage_data:
                conversion_rate = (stage_data["customer_count"] / total_customers * 100) if total_customers > 0 else 0
                funnel.append({
                    "stage": stage,
                    "count": stage_data["customer_count"],
                    "conversion_rate": round(conversion_rate, 2)
                })
        
        return {
            "total_customers": total_customers,
            "journey_stages": journey_stages,
            "conversion_funnel": funnel,
            "drop_off_analysis": self._analyze_drop_offs(funnel)
        }
    
    def _analyze_drop_offs(self, funnel: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze drop-offs in the conversion funnel."""
        if len(funnel) < 2:
            return {"message": "Insufficient data for drop-off analysis"}
        
        drop_offs = []
        for i in range(len(funnel) - 1):
            current_stage = funnel[i]
            next_stage = funnel[i + 1]
            
            drop_off_rate = current_stage["conversion_rate"] - next_stage["conversion_rate"]
            drop_offs.append({
                "from_stage": current_stage["stage"],
                "to_stage": next_stage["stage"],
                "drop_off_rate": round(drop_off_rate, 2),
                "customers_lost": current_stage["count"] - next_stage["count"]
            })
        
        # Find biggest drop-off
        biggest_drop_off = max(drop_offs, key=lambda x: x["drop_off_rate"]) if drop_offs else None
        
        return {
            "drop_offs": drop_offs,
            "biggest_drop_off_stage": biggest_drop_off["from_stage"] if biggest_drop_off else None,
            "biggest_drop_off_rate": biggest_drop_off["drop_off_rate"] if biggest_drop_off else 0
        }
    
    async def export_campaign_data(
        self,
        campaign: Campaign,
        format: str,
        session: AsyncSession
    ) -> AsyncGenerator[bytes, None]:
        """Export campaign data in specified format."""
        try:
            # Get comprehensive campaign data
            stmt = select(CampaignRecipient).where(
                CampaignRecipient.campaign_id == campaign.id
            ).options(
                selectinload(CampaignRecipient.customer),
                selectinload(CampaignRecipient.message)
            )
            
            result = await session.execute(stmt)
            recipients = result.scalars().all()
            
            # Prepare data for export
            export_data = []
            for recipient in recipients:
                export_data.append({
                    "campaign_name": campaign.name,
                    "campaign_type": campaign.campaign_type,
                    "customer_name": f"{recipient.customer.first_name} {recipient.customer.last_name or ''}".strip(),
                    "customer_phone": recipient.customer.phone_number,
                    "customer_language": recipient.customer.preferred_language,
                    "variant_id": recipient.variant_id or "",
                    "status": recipient.status,
                    "scheduled_time": recipient.scheduled_send_time.isoformat() if recipient.scheduled_send_time else "",
                    "sent_time": recipient.sent_at.isoformat() if recipient.sent_at else "",
                    "delivered_time": recipient.delivered_at.isoformat() if recipient.delivered_at else "",
                    "response_time": recipient.responded_at.isoformat() if recipient.responded_at else "",
                    "response_text": recipient.response_text or "",
                    "response_sentiment": recipient.response_sentiment or "",
                    "order_total": recipient.customer.order_total or 0,
                    "visit_date": recipient.customer.visit_date.isoformat() if recipient.customer.visit_date else ""
                })
            
            if format == "csv":
                yield await self._export_csv(export_data)
            elif format == "json":
                yield await self._export_json(export_data, campaign)
            elif format == "excel":
                yield await self._export_excel(export_data)
            elif format == "pdf":
                yield await self._export_pdf(export_data, campaign)
                
        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            yield b""
    
    async def _export_csv(self, data: List[Dict[str, Any]]) -> bytes:
        """Export data as CSV."""
        if not data:
            return b""
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue().encode('utf-8')
    
    async def _export_json(self, data: List[Dict[str, Any]], campaign: Campaign) -> bytes:
        """Export data as JSON."""
        export_object = {
            "campaign": {
                "id": str(campaign.id),
                "name": campaign.name,
                "type": campaign.campaign_type,
                "status": campaign.status,
                "created_at": campaign.created_at.isoformat(),
                "performance_summary": campaign.get_performance_summary()
            },
            "recipients": data,
            "export_timestamp": datetime.utcnow().isoformat(),
            "total_records": len(data)
        }
        
        return json.dumps(export_object, indent=2, ensure_ascii=False).encode('utf-8')
    
    async def _export_excel(self, data: List[Dict[str, Any]]) -> bytes:
        """Export data as Excel file."""
        if not data:
            return b""
        
        df = pd.DataFrame(data)
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Campaign Data', index=False)
        
        output.seek(0)
        return output.read()
    
    async def _export_pdf(self, data: List[Dict[str, Any]], campaign: Campaign) -> bytes:
        """Export data as PDF report."""
        # This would require a PDF library like reportlab
        # For now, return a placeholder
        report_content = f"""
        Campaign Report: {campaign.name}
        Type: {campaign.campaign_type}
        Status: {campaign.status}
        
        Total Recipients: {len(data)}
        Messages Sent: {campaign.messages_sent}
        Delivered: {campaign.messages_delivered}
        Response Rate: {campaign.response_rate:.2f}%
        
        Generated: {datetime.utcnow().isoformat()}
        """
        
        return report_content.encode('utf-8')