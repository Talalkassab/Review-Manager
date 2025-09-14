"""
WhatsApp Message Repository Implementation
Handles data access operations for WhatsApp messages.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc

from .base_repository import BaseRepository
from ....models.whatsapp import WhatsAppMessage


class WhatsAppMessageRepository(BaseRepository[WhatsAppMessage]):
    """Repository for WhatsApp message data operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, WhatsAppMessage)

    def get_model(self) -> type[WhatsAppMessage]:
        return WhatsAppMessage

    async def find_by_twilio_sid(self, twilio_sid: str) -> Optional[WhatsAppMessage]:
        """Find message by Twilio SID."""
        stmt = select(WhatsAppMessage).where(
            WhatsAppMessage.twilio_sid == twilio_sid
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_conversation_history(
        self,
        customer_id: UUID,
        limit: int = 50,
        include_system: bool = False
    ) -> List[WhatsAppMessage]:
        """Get conversation history for a customer."""
        stmt = select(WhatsAppMessage).where(
            WhatsAppMessage.customer_id == customer_id
        )

        if not include_system:
            stmt = stmt.where(
                WhatsAppMessage.direction.in_(['inbound', 'outbound'])
            )

        stmt = stmt.order_by(desc(WhatsAppMessage.created_at)).limit(limit)

        result = await self.session.execute(stmt)
        messages = result.scalars().all()

        # Return in chronological order (oldest first)
        return list(reversed(messages))

    async def get_messages_by_direction(
        self,
        direction: str,
        customer_id: Optional[UUID] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[WhatsAppMessage]:
        """Get messages by direction (inbound/outbound)."""
        stmt = select(WhatsAppMessage).where(
            WhatsAppMessage.direction == direction
        )

        if customer_id:
            stmt = stmt.where(WhatsAppMessage.customer_id == customer_id)

        if since:
            stmt = stmt.where(WhatsAppMessage.created_at >= since)

        stmt = stmt.order_by(desc(WhatsAppMessage.created_at)).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_pending_messages(
        self,
        status_filter: List[str] = None
    ) -> List[WhatsAppMessage]:
        """Get messages with pending status."""
        if status_filter is None:
            status_filter = ['queued', 'sent', 'delivered']

        stmt = select(WhatsAppMessage).where(
            and_(
                WhatsAppMessage.direction == 'outbound',
                WhatsAppMessage.status.in_(status_filter)
            )
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_failed_messages(
        self,
        since: Optional[datetime] = None
    ) -> List[WhatsAppMessage]:
        """Get failed messages."""
        stmt = select(WhatsAppMessage).where(
            WhatsAppMessage.status.in_(['failed', 'undelivered'])
        )

        if since:
            stmt = stmt.where(WhatsAppMessage.created_at >= since)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_message_status(
        self,
        twilio_sid: str,
        status: str,
        status_data: Optional[Dict] = None
    ) -> Optional[WhatsAppMessage]:
        """Update message status by Twilio SID."""
        message = await self.find_by_twilio_sid(twilio_sid)
        if not message:
            return None

        message.status = status
        message.updated_at = datetime.utcnow()

        # Add to status history
        if not message.status_history:
            message.status_history = []

        message.status_history.append({
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "data": status_data or {}
        })

        await self.session.commit()
        await self.session.refresh(message)

        return message

    async def get_message_stats(
        self,
        customer_id: Optional[UUID] = None,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get message statistics."""
        base_conditions = []

        if customer_id:
            base_conditions.append(WhatsAppMessage.customer_id == customer_id)

        if since:
            base_conditions.append(WhatsAppMessage.created_at >= since)

        # Total messages
        total_stmt = select(func.count()).select_from(WhatsAppMessage)
        if base_conditions:
            total_stmt = total_stmt.where(and_(*base_conditions))

        total_result = await self.session.execute(total_stmt)
        total_messages = total_result.scalar() or 0

        # Messages by direction
        direction_stmt = select(
            WhatsAppMessage.direction,
            func.count(WhatsAppMessage.id)
        ).group_by(WhatsAppMessage.direction)

        if base_conditions:
            direction_stmt = direction_stmt.where(and_(*base_conditions))

        direction_result = await self.session.execute(direction_stmt)
        direction_stats = dict(direction_result.all())

        # Messages by status
        status_stmt = select(
            WhatsAppMessage.status,
            func.count(WhatsAppMessage.id)
        ).group_by(WhatsAppMessage.status)

        if base_conditions:
            status_stmt = status_stmt.where(and_(*base_conditions))

        status_result = await self.session.execute(status_stmt)
        status_stats = dict(status_result.all())

        return {
            'total_messages': total_messages,
            'by_direction': direction_stats,
            'by_status': status_stats
        }

    async def get_recent_conversations(
        self,
        hours: int = 24,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get recent conversations."""
        cutoff_time = datetime.utcnow().replace(
            hour=datetime.utcnow().hour - hours,
            minute=0,
            second=0,
            microsecond=0
        )

        stmt = select(
            WhatsAppMessage.customer_id,
            func.count(WhatsAppMessage.id).label('message_count'),
            func.max(WhatsAppMessage.created_at).label('last_message'),
            func.min(WhatsAppMessage.created_at).label('first_message')
        ).where(
            WhatsAppMessage.created_at >= cutoff_time
        ).group_by(
            WhatsAppMessage.customer_id
        ).order_by(
            desc('last_message')
        ).limit(limit)

        result = await self.session.execute(stmt)
        conversations = []

        for row in result.all():
            conversations.append({
                'customer_id': str(row.customer_id),
                'message_count': row.message_count,
                'last_message': row.last_message.isoformat(),
                'first_message': row.first_message.isoformat(),
                'duration_hours': (row.last_message - row.first_message).total_seconds() / 3600
            })

        return conversations

    async def search_messages(
        self,
        search_term: str,
        customer_id: Optional[UUID] = None,
        direction: Optional[str] = None,
        limit: int = 100
    ) -> List[WhatsAppMessage]:
        """Search messages by content."""
        stmt = select(WhatsAppMessage).where(
            WhatsAppMessage.message_body.ilike(f"%{search_term}%")
        )

        if customer_id:
            stmt = stmt.where(WhatsAppMessage.customer_id == customer_id)

        if direction:
            stmt = stmt.where(WhatsAppMessage.direction == direction)

        stmt = stmt.order_by(desc(WhatsAppMessage.created_at)).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_delivery_rate(
        self,
        since: Optional[datetime] = None
    ) -> Dict[str, float]:
        """Calculate message delivery rates."""
        base_conditions = [WhatsAppMessage.direction == 'outbound']

        if since:
            base_conditions.append(WhatsAppMessage.created_at >= since)

        # Total sent messages
        total_stmt = select(func.count()).select_from(WhatsAppMessage).where(
            and_(*base_conditions)
        )
        total_result = await self.session.execute(total_stmt)
        total_sent = total_result.scalar() or 0

        if total_sent == 0:
            return {'delivery_rate': 0.0, 'failure_rate': 0.0}

        # Delivered messages
        delivered_conditions = base_conditions + [
            WhatsAppMessage.status.in_(['delivered', 'read'])
        ]
        delivered_stmt = select(func.count()).select_from(WhatsAppMessage).where(
            and_(*delivered_conditions)
        )
        delivered_result = await self.session.execute(delivered_stmt)
        delivered_count = delivered_result.scalar() or 0

        # Failed messages
        failed_conditions = base_conditions + [
            WhatsAppMessage.status.in_(['failed', 'undelivered'])
        ]
        failed_stmt = select(func.count()).select_from(WhatsAppMessage).where(
            and_(*failed_conditions)
        )
        failed_result = await self.session.execute(failed_stmt)
        failed_count = failed_result.scalar() or 0

        return {
            'delivery_rate': delivered_count / total_sent * 100,
            'failure_rate': failed_count / total_sent * 100,
            'total_sent': total_sent,
            'delivered': delivered_count,
            'failed': failed_count
        }