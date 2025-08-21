"""
Campaign execution service with advanced features.
Handles bulk messaging, rate limiting, and real-time monitoring.
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, AsyncGenerator
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.orm import selectinload

from ...core.logging import get_logger
from ...models import Campaign, CampaignRecipient, Customer, WhatsAppMessage, Restaurant
from ..openrouter.client import OpenRouterClient

logger = get_logger(__name__)

# Temporary stub for missing WebSocket manager
class CampaignWebSocketManager:
    """Stub for WebSocket manager - to be implemented."""
    pass


class RateLimiter:
    """Rate limiter for campaign message sending."""
    
    def __init__(self, max_rate_per_hour: int = 100):
        self.max_rate_per_hour = max_rate_per_hour
        self.sent_times: List[datetime] = []
        
    def can_send(self) -> bool:
        """Check if we can send a message based on rate limit."""
        now = datetime.utcnow()
        cutoff_time = now - timedelta(hours=1)
        
        # Remove old entries
        self.sent_times = [t for t in self.sent_times if t > cutoff_time]
        
        return len(self.sent_times) < self.max_rate_per_hour
    
    def record_send(self):
        """Record that a message was sent."""
        self.sent_times.append(datetime.utcnow())
    
    def time_until_next_send(self) -> Optional[float]:
        """Get seconds to wait until next message can be sent."""
        if self.can_send():
            return 0
        
        if not self.sent_times:
            return 0
            
        # Find the oldest message in the current hour
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        oldest_in_hour = min([t for t in self.sent_times if t > cutoff_time])
        
        # Time until oldest message expires from the hour window
        next_available = oldest_in_hour + timedelta(hours=1)
        return (next_available - datetime.utcnow()).total_seconds()


class CampaignExecutionService:
    """Service for executing campaigns with advanced features."""
    
    def __init__(self):
        self.openrouter_client = OpenRouterClient()
        self.rate_limiters: Dict[str, RateLimiter] = {}
        
    async def execute_campaign(
        self,
        campaign_id: UUID,
        websocket_manager: Optional[CampaignWebSocketManager] = None
    ):
        """Execute campaign with real-time monitoring."""
        from ...database import db_manager
        
        async with db_manager.get_session() as session:
            try:
                # Get campaign with recipients
                stmt = select(Campaign).where(Campaign.id == campaign_id).options(
                    selectinload(Campaign.campaign_recipients).selectinload(CampaignRecipient.customer)
                )
                result = await session.execute(stmt)
                campaign = result.scalar_one_or_none()
                
                if not campaign:
                    logger.error(f"Campaign not found: {campaign_id}")
                    return
                
                if not campaign.is_running:
                    logger.error(f"Campaign not in running state: {campaign.status}")
                    return
                
                # Initialize rate limiter
                rate_limiter = RateLimiter(campaign.send_rate_per_hour)
                self.rate_limiters[str(campaign_id)] = rate_limiter
                
                # Get pending recipients
                pending_recipients = [
                    r for r in campaign.campaign_recipients 
                    if r.status == "pending"
                ]
                
                if not pending_recipients:
                    logger.info(f"No pending recipients for campaign: {campaign_id}")
                    campaign.complete_campaign()
                    await session.commit()
                    return
                
                logger.info(f"Starting execution of campaign {campaign_id} with {len(pending_recipients)} recipients")
                
                # Send messages with rate limiting
                sent_count = 0
                failed_count = 0
                
                for recipient in pending_recipients:
                    try:
                        # Check if campaign is still running
                        await session.refresh(campaign)
                        if campaign.status != "running":
                            logger.info(f"Campaign {campaign_id} stopped during execution")
                            break
                        
                        # Rate limiting
                        if not rate_limiter.can_send():
                            wait_time = rate_limiter.time_until_next_send()
                            if wait_time > 0:
                                logger.info(f"Rate limit reached, waiting {wait_time:.1f}s")
                                await asyncio.sleep(wait_time)
                        
                        # Send message
                        success = await self._send_campaign_message(
                            campaign=campaign,
                            recipient=recipient,
                            session=session
                        )
                        
                        if success:
                            sent_count += 1
                            rate_limiter.record_send()
                            
                            # Update recipient status
                            recipient.mark_sent()
                            
                            # Update campaign metrics
                            campaign.messages_sent += 1
                        else:
                            failed_count += 1
                            recipient.status = "failed"
                            campaign.messages_failed += 1
                        
                        await session.commit()
                        
                        # Send real-time update via WebSocket
                        if websocket_manager:
                            progress = {
                                "campaign_id": str(campaign_id),
                                "sent": sent_count,
                                "failed": failed_count,
                                "remaining": len(pending_recipients) - sent_count - failed_count,
                                "progress_percent": round((sent_count + failed_count) / len(pending_recipients) * 100, 2),
                                "timestamp": datetime.utcnow().isoformat()
                            }
                            await websocket_manager.broadcast_to_campaign(
                                str(campaign_id),
                                progress
                            )
                        
                        # Small delay to prevent overwhelming the system
                        await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        logger.error(f"Error sending message to recipient {recipient.id}: {str(e)}")
                        failed_count += 1
                        recipient.status = "failed"
                        campaign.messages_failed += 1
                        await session.commit()
                
                # Complete campaign
                campaign.complete_campaign()
                await session.commit()
                
                logger.info(f"Campaign {campaign_id} completed - Sent: {sent_count}, Failed: {failed_count}")
                
                # Final WebSocket update
                if websocket_manager:
                    final_update = {
                        "campaign_id": str(campaign_id),
                        "status": "completed",
                        "total_sent": sent_count,
                        "total_failed": failed_count,
                        "completion_time": datetime.utcnow().isoformat()
                    }
                    await websocket_manager.broadcast_to_campaign(
                        str(campaign_id),
                        final_update
                    )
                
            except Exception as e:
                logger.error(f"Campaign execution failed: {str(e)}")
                # Update campaign status to failed
                if campaign:
                    campaign.status = "failed"
                    await session.commit()
    
    async def _send_campaign_message(
        self,
        campaign: Campaign,
        recipient: CampaignRecipient,
        session: AsyncSession
    ) -> bool:
        """Send a message to a campaign recipient."""
        try:
            # Get message variant for this recipient
            message_variant = self._get_message_variant(campaign, recipient)
            
            # Personalize message content
            personalized_content = await self._personalize_message(
                message_variant,
                recipient,
                campaign,
                session
            )
            
            # Create WhatsApp message record
            whatsapp_message = WhatsAppMessage(
                content=personalized_content,
                direction="outbound",
                status="queued",
                language=campaign.default_language,
                template_name=message_variant.get("template_name"),
                template_parameters=message_variant.get("template_parameters"),
                customer_id=recipient.customer_id,
                restaurant_id=campaign.restaurant_id,
                campaign_id=campaign.id
            )
            
            session.add(whatsapp_message)
            await session.commit()
            await session.refresh(whatsapp_message)
            
            # TODO: Integrate with actual WhatsApp Business API
            # For now, simulate message sending
            await asyncio.sleep(0.1)  # Simulate API call
            
            # Update message status (simulated success)
            whatsapp_message.status = "sent"
            whatsapp_message.sent_at = datetime.utcnow()
            
            # Link message to recipient
            recipient.message_id = whatsapp_message.id
            
            await session.commit()
            
            logger.debug(f"Message sent to customer {recipient.customer_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            return False
    
    def _get_message_variant(
        self,
        campaign: Campaign,
        recipient: CampaignRecipient
    ) -> Dict[str, Any]:
        """Get the appropriate message variant for a recipient."""
        if not campaign.message_variants:
            raise ValueError("No message variants configured for campaign")
        
        # If A/B testing, use assigned variant
        if campaign.is_ab_test and recipient.variant_id:
            for variant in campaign.message_variants:
                if variant.get("id") == recipient.variant_id:
                    return variant
        
        # Default to first variant
        return campaign.message_variants[0]
    
    async def _personalize_message(
        self,
        message_variant: Dict[str, Any],
        recipient: CampaignRecipient,
        campaign: Campaign,
        session: AsyncSession
    ) -> str:
        """Personalize message content for recipient."""
        base_content = message_variant.get("content", "")
        
        # Get customer data
        await session.refresh(recipient.customer)
        customer = recipient.customer
        
        # Basic personalization variables
        variables = {
            "customer_name": customer.first_name or "عزيزي العميل",
            "restaurant_name": campaign.restaurant.name if campaign.restaurant else "مطعمنا",
            "first_name": customer.first_name or "عزيزي",
            "last_name": customer.last_name or "",
            "phone": customer.phone_number,
        }
        
        # Add custom personalization data
        if recipient.personalization_data:
            variables.update(recipient.personalization_data)
        
        # Replace variables in content
        personalized_content = base_content
        for key, value in variables.items():
            personalized_content = personalized_content.replace(f"{{{key}}}", str(value))
        
        # Use AI for advanced personalization if configured
        if message_variant.get("use_ai_personalization", False):
            personalized_content = await self._ai_personalize_message(
                content=personalized_content,
                customer=customer,
                campaign=campaign
            )
        
        return personalized_content
    
    async def _ai_personalize_message(
        self,
        content: str,
        customer: Customer,
        campaign: Campaign
    ) -> str:
        """Use AI to enhance message personalization."""
        try:
            # Prepare context for AI
            context = {
                "customer_language": customer.preferred_language,
                "campaign_type": campaign.campaign_type,
                "customer_history": {
                    "visit_date": customer.visit_date.isoformat() if customer.visit_date else None,
                    "party_size": customer.party_size,
                    "order_total": customer.order_total,
                    "special_requests": customer.special_requests
                }
            }
            
            prompt = f"""
            Please enhance this customer message to be more personalized and culturally appropriate:
            
            Original message: {content}
            Customer context: {json.dumps(context)}
            
            Requirements:
            - Maintain the core message intent
            - Use appropriate cultural tone for Arabic customers
            - Keep it concise and professional
            - Include relevant personal touches based on context
            
            Return only the enhanced message text.
            """
            
            response = await self.openrouter_client.generate_text(
                prompt=prompt,
                model="anthropic/claude-3-haiku"
            )
            
            return response.strip() if response else content
            
        except Exception as e:
            logger.error(f"AI personalization failed: {str(e)}")
            return content
    
    async def execute_bulk_operation(
        self,
        campaigns: List[Campaign],
        operation: str,
        parameters: Optional[Dict[str, Any]] = None,
        websocket_manager: Optional[CampaignWebSocketManager] = None
    ):
        """Execute bulk operations on multiple campaigns."""
        from ...database import db_manager
        
        async with db_manager.get_session() as session:
            try:
                results = []
                
                for i, campaign in enumerate(campaigns):
                    try:
                        if operation == "start":
                            if campaign.can_be_started:
                                campaign.start_campaign()
                                # Execute in background
                                asyncio.create_task(
                                    self.execute_campaign(
                                        campaign.id,
                                        websocket_manager
                                    )
                                )
                        elif operation == "pause":
                            if campaign.is_running:
                                campaign.pause_campaign()
                        elif operation == "resume":
                            if campaign.status == "paused":
                                campaign.resume_campaign()
                        elif operation == "cancel":
                            if campaign.status in ["running", "paused", "scheduled"]:
                                reason = parameters.get("reason") if parameters else None
                                campaign.cancel_campaign(reason)
                        
                        results.append({
                            "campaign_id": str(campaign.id),
                            "status": "success",
                            "new_status": campaign.status
                        })
                        
                    except Exception as e:
                        results.append({
                            "campaign_id": str(campaign.id),
                            "status": "error",
                            "error": str(e)
                        })
                    
                    # Send progress update
                    if websocket_manager:
                        progress = {
                            "operation": operation,
                            "progress": (i + 1) / len(campaigns) * 100,
                            "completed": i + 1,
                            "total": len(campaigns),
                            "results": results
                        }
                        await websocket_manager.broadcast_bulk_update(progress)
                
                await session.commit()
                logger.info(f"Bulk operation {operation} completed on {len(campaigns)} campaigns")
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Bulk operation failed: {str(e)}")
    
    async def optimize_campaign(
        self,
        campaign: Campaign,
        optimization_type: str,
        session: AsyncSession,
        websocket_manager: Optional[CampaignWebSocketManager] = None
    ):
        """Optimize campaign using AI and machine learning."""
        try:
            logger.info(f"Starting {optimization_type} optimization for campaign {campaign.id}")
            
            optimization_results = {}
            
            if optimization_type in ["timing", "full"]:
                # Optimize send timing
                optimal_times = await self._optimize_timing(campaign, session)
                optimization_results["timing"] = optimal_times
            
            if optimization_type in ["content", "full"]:
                # Optimize message content
                optimized_content = await self._optimize_content(campaign, session)
                optimization_results["content"] = optimized_content
            
            if optimization_type in ["targeting", "full"]:
                # Optimize targeting
                better_targeting = await self._optimize_targeting(campaign, session)
                optimization_results["targeting"] = better_targeting
            
            if optimization_type in ["ab_test", "full"]:
                # Optimize A/B testing setup
                ab_optimization = await self._optimize_ab_testing(campaign, session)
                optimization_results["ab_testing"] = ab_optimization
            
            # Apply optimizations
            await self._apply_optimizations(campaign, optimization_results, session)
            
            # Send results via WebSocket
            if websocket_manager:
                await websocket_manager.broadcast_to_campaign(
                    str(campaign.id),
                    {
                        "type": "optimization_complete",
                        "optimization_type": optimization_type,
                        "results": optimization_results,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            
            logger.info(f"Optimization completed for campaign {campaign.id}")
            
        except Exception as e:
            logger.error(f"Campaign optimization failed: {str(e)}")
            if websocket_manager:
                await websocket_manager.broadcast_to_campaign(
                    str(campaign.id),
                    {
                        "type": "optimization_error",
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
    
    async def _optimize_timing(self, campaign: Campaign, session: AsyncSession) -> Dict[str, Any]:
        """Optimize campaign timing based on historical data."""
        # Analyze historical campaign performance by time
        stmt = text("""
            SELECT 
                EXTRACT(HOUR FROM sent_at) as send_hour,
                COUNT(*) as message_count,
                SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as delivered_count,
                SUM(CASE WHEN status = 'read' THEN 1 ELSE 0 END) as read_count
            FROM whatsapp_messages 
            WHERE restaurant_id = :restaurant_id 
            AND sent_at IS NOT NULL
            AND sent_at >= NOW() - INTERVAL '30 days'
            GROUP BY EXTRACT(HOUR FROM sent_at)
            ORDER BY delivered_count DESC, read_count DESC
        """)
        
        result = await session.execute(stmt, {"restaurant_id": campaign.restaurant_id})
        timing_data = result.fetchall()
        
        if timing_data:
            best_hours = [row[0] for row in timing_data[:3]]  # Top 3 hours
            return {
                "optimal_hours": best_hours,
                "recommendation": f"Best sending times: {', '.join(map(str, best_hours))}:00",
                "data_points": len(timing_data)
            }
        
        # Default cultural timing for Arabic customers
        return {
            "optimal_hours": [10, 14, 19],  # 10 AM, 2 PM, 7 PM
            "recommendation": "Using cultural defaults for Arabic customers",
            "data_points": 0
        }
    
    async def _optimize_content(self, campaign: Campaign, session: AsyncSession) -> Dict[str, Any]:
        """Optimize message content using AI."""
        try:
            # Get high-performing message examples
            stmt = select(WhatsAppMessage).where(
                and_(
                    WhatsAppMessage.restaurant_id == campaign.restaurant_id,
                    WhatsAppMessage.status == "delivered",
                    WhatsAppMessage.content.isnot(None)
                )
            ).limit(10)
            
            result = await session.execute(stmt)
            successful_messages = result.scalars().all()
            
            # Generate optimized content using AI
            current_variants = campaign.message_variants or []
            optimized_variants = []
            
            for variant in current_variants:
                prompt = f"""
                Optimize this campaign message for better engagement with Arabic customers:
                
                Current message: {variant.get('content', '')}
                Campaign type: {campaign.campaign_type}
                
                Consider:
                - Cultural appropriateness for Arabic customers
                - Clear call-to-action
                - Emotional resonance
                - Professional yet warm tone
                
                Provide 3 optimized variations.
                """
                
                response = await self.openrouter_client.generate_text(
                    prompt=prompt,
                    model="anthropic/claude-3-haiku"
                )
                
                if response:
                    optimized_variants.append({
                        "original": variant,
                        "optimized_options": response.strip().split("\n\n")[:3]
                    })
            
            return {
                "optimized_variants": optimized_variants,
                "recommendation": "AI-generated content optimizations based on cultural preferences"
            }
            
        except Exception as e:
            logger.error(f"Content optimization failed: {str(e)}")
            return {"error": str(e)}
    
    async def _optimize_targeting(self, campaign: Campaign, session: AsyncSession) -> Dict[str, Any]:
        """Optimize campaign targeting based on customer behavior."""
        # Analyze customer segments and their response patterns
        stmt = text("""
            SELECT 
                c.preferred_language,
                CASE 
                    WHEN c.order_total > 200 THEN 'high_value'
                    WHEN c.order_total > 100 THEN 'medium_value'
                    ELSE 'low_value'
                END as value_segment,
                COUNT(*) as customer_count,
                AVG(CASE WHEN wm.status IN ('delivered', 'read') THEN 1.0 ELSE 0.0 END) as success_rate
            FROM customers c
            LEFT JOIN whatsapp_messages wm ON c.id = wm.customer_id
            WHERE c.restaurant_id = :restaurant_id
            GROUP BY c.preferred_language, value_segment
            ORDER BY success_rate DESC
        """)
        
        result = await session.execute(stmt, {"restaurant_id": campaign.restaurant_id})
        segment_data = result.fetchall()
        
        recommendations = []
        for row in segment_data:
            if row[3] > 0.5:  # Success rate > 50%
                recommendations.append({
                    "segment": f"{row[0]}_{row[1]}",
                    "success_rate": round(row[3] * 100, 1),
                    "customer_count": row[2]
                })
        
        return {
            "high_performing_segments": recommendations,
            "recommendation": "Focus on segments with highest engagement rates"
        }
    
    async def _optimize_ab_testing(self, campaign: Campaign, session: AsyncSession) -> Dict[str, Any]:
        """Optimize A/B testing configuration."""
        if not campaign.is_ab_test:
            return {
                "recommendation": "Consider enabling A/B testing to optimize performance",
                "suggested_variants": 2,
                "test_duration": "24-48 hours"
            }
        
        # Analyze current A/B test if running
        stmt = select(CampaignRecipient).where(
            and_(
                CampaignRecipient.campaign_id == campaign.id,
                CampaignRecipient.variant_id.isnot(None)
            )
        )
        result = await session.execute(stmt)
        recipients = result.scalars().all()
        
        variant_performance = {}
        for recipient in recipients:
            variant = recipient.variant_id
            if variant not in variant_performance:
                variant_performance[variant] = {"total": 0, "responded": 0}
            
            variant_performance[variant]["total"] += 1
            if recipient.has_responded:
                variant_performance[variant]["responded"] += 1
        
        return {
            "variant_performance": variant_performance,
            "recommendation": "Continue current A/B test or implement suggested optimizations"
        }
    
    async def _apply_optimizations(
        self,
        campaign: Campaign,
        optimizations: Dict[str, Any],
        session: AsyncSession
    ):
        """Apply optimization results to campaign."""
        try:
            # Apply timing optimizations
            if "timing" in optimizations:
                timing_data = optimizations["timing"]
                if "optimal_hours" in timing_data:
                    if not campaign.scheduling_config:
                        campaign.scheduling_config = {}
                    campaign.scheduling_config["optimal_send_hours"] = timing_data["optimal_hours"]
            
            # Apply content optimizations
            if "content" in optimizations and "optimized_variants" in optimizations["content"]:
                # For now, log the suggestions (could be applied by user approval)
                logger.info(f"Content optimization suggestions available for campaign {campaign.id}")
            
            # Apply targeting optimizations
            if "targeting" in optimizations:
                targeting_data = optimizations["targeting"]
                if "high_performing_segments" in targeting_data:
                    if not campaign.targeting_config:
                        campaign.targeting_config = {}
                    campaign.targeting_config["recommended_segments"] = targeting_data["high_performing_segments"]
            
            await session.commit()
            logger.info(f"Optimizations applied to campaign {campaign.id}")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to apply optimizations: {str(e)}")
    
    async def get_campaign_templates(
        self,
        restaurant_id: UUID,
        campaign_type: Optional[str] = None,
        session: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        """Get campaign templates for quick setup."""
        # Pre-defined templates for different campaign types
        templates = [
            {
                "name": "Customer Feedback Survey",
                "description": "Request customer feedback after dining experience",
                "campaign_type": "feedback_survey",
                "default_targeting": {
                    "customer_segments": ["recent_visitors"],
                    "visit_days_ago": [1, 2, 3],
                    "preferred_language": ["ar", "en"]
                },
                "default_messages": [
                    {
                        "id": "variant_1",
                        "content": "مرحباً {customer_name}، نشكرك لزيارة {restaurant_name}. نرجو تقييم تجربتك معنا",
                        "language": "ar",
                        "template_name": "feedback_request"
                    }
                ],
                "default_scheduling": {
                    "optimal_send_hours": [10, 14, 19],
                    "avoid_weekends": False,
                    "cultural_considerations": ["ramadan_timing", "prayer_times"]
                },
                "is_system_template": True
            },
            {
                "name": "Promotional Offer",
                "description": "Send promotional offers to customers",
                "campaign_type": "promotion",
                "default_targeting": {
                    "customer_segments": ["loyal_customers", "high_value"],
                    "order_total_min": 50,
                    "preferred_language": ["ar", "en"]
                },
                "default_messages": [
                    {
                        "id": "variant_1", 
                        "content": "عرض خاص لك في {restaurant_name}! خصم 20% على طلبك القادم",
                        "language": "ar",
                        "use_ai_personalization": True
                    }
                ],
                "default_scheduling": {
                    "optimal_send_hours": [11, 17, 20],
                    "avoid_weekends": False
                },
                "is_system_template": True
            },
            {
                "name": "Welcome New Customers",
                "description": "Welcome message for first-time customers",
                "campaign_type": "welcome",
                "default_targeting": {
                    "customer_segments": ["new_customers"],
                    "visit_count_max": 1
                },
                "default_messages": [
                    {
                        "id": "variant_1",
                        "content": "مرحباً {customer_name}! شكراً لزيارتك الأولى لـ {restaurant_name}. نتطلع لرؤيتك مرة أخرى",
                        "language": "ar"
                    }
                ],
                "default_scheduling": {
                    "optimal_send_hours": [14, 18, 21],
                    "send_delay_hours": 2
                },
                "is_system_template": True
            }
        ]
        
        if campaign_type:
            templates = [t for t in templates if t["campaign_type"] == campaign_type]
        
        return templates