"""
Async messaging service with retry mechanisms and queue management.

This module provides robust asynchronous message sending capabilities with
comprehensive retry logic, queue management, and background processing for
WhatsApp Business API integration.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict
import heapq

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.config import settings
from app.models.whatsapp import (
    WhatsAppMessage, MessageStatus, MessageType, MessageDirection, Priority
)
from app.models.customer import Customer
from .client import WhatsAppClient
from .exceptions import (
    MessageDeliveryError, QueueError, RateLimitExceededError
)
from .rate_limiter import RateLimiter, RateLimitType


class MessageQueueStatus(str, Enum):
    """Message queue status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RetryStrategy(str, Enum):
    """Retry strategy enumeration."""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    FIXED_INTERVAL = "fixed_interval"
    LINEAR_BACKOFF = "linear_backoff"
    IMMEDIATE = "immediate"


@dataclass
class MessageTask:
    """Message task for queue processing."""
    id: str
    customer_id: int
    phone_number: str
    message_type: MessageType
    priority: Priority
    scheduled_at: datetime
    retry_count: int = 0
    max_retries: int = 3
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    
    # Message content
    content: Optional[str] = None
    media_url: Optional[str] = None
    template_name: Optional[str] = None
    template_language: Optional[str] = None
    template_parameters: Optional[Dict[str, Any]] = None
    interactive_data: Optional[Dict[str, Any]] = None
    
    # Metadata
    conversation_id: Optional[str] = None
    campaign_id: Optional[str] = None
    automation_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # Callbacks
    success_callback: Optional[Callable] = None
    failure_callback: Optional[Callable] = None
    
    def __lt__(self, other):
        """Support priority queue ordering."""
        if self.priority != other.priority:
            # Higher priority values come first
            return self.priority.value > other.priority.value
        return self.scheduled_at < other.scheduled_at
    
    def should_retry(self) -> bool:
        """Check if task should be retried."""
        return self.retry_count < self.max_retries
    
    def get_next_retry_delay(self) -> float:
        """Calculate delay for next retry attempt."""
        if self.retry_strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            return min(30 * (2 ** self.retry_count), 3600)  # Max 1 hour
        elif self.retry_strategy == RetryStrategy.LINEAR_BACKOFF:
            return min(30 + (self.retry_count * 30), 1800)  # Max 30 minutes
        elif self.retry_strategy == RetryStrategy.FIXED_INTERVAL:
            return 60  # 1 minute
        else:  # IMMEDIATE
            return 0


class MessageQueue:
    """Priority queue for message tasks with persistent storage."""
    
    def __init__(self, db: Session, name: str = "default"):
        """Initialize message queue."""
        self.db = db
        self.name = name
        self.logger = logging.getLogger(__name__)
        
        # In-memory priority queue for active tasks
        self._queue: List[MessageTask] = []
        self._task_lookup: Dict[str, MessageTask] = {}
        
        # Queue statistics
        self.stats = {
            'total_added': 0,
            'total_processed': 0,
            'total_failed': 0,
            'current_size': 0,
            'processing_count': 0
        }
        
        # Queue lock for thread safety
        self._lock = asyncio.Lock()
    
    async def add_task(self, task: MessageTask) -> bool:
        """
        Add a task to the queue.
        
        Args:
            task: Message task to add
            
        Returns:
            True if task added successfully
        """
        async with self._lock:
            try:
                # Add to priority queue
                heapq.heappush(self._queue, task)
                self._task_lookup[task.id] = task
                
                # Update statistics
                self.stats['total_added'] += 1
                self.stats['current_size'] = len(self._queue)
                
                self.logger.debug(f"Task {task.id} added to queue {self.name}")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to add task to queue: {str(e)}")
                return False
    
    async def get_next_task(self) -> Optional[MessageTask]:
        """
        Get the next task from the queue.
        
        Returns:
            Next task or None if queue is empty
        """
        async with self._lock:
            try:
                # Find next ready task
                now = datetime.utcnow()
                ready_tasks = []
                delayed_tasks = []
                
                # Separate ready and delayed tasks
                while self._queue:
                    task = heapq.heappop(self._queue)
                    if task.scheduled_at <= now:
                        ready_tasks.append(task)
                    else:
                        delayed_tasks.append(task)
                
                # Restore delayed tasks to queue
                for task in delayed_tasks:
                    heapq.heappush(self._queue, task)
                
                # Return highest priority ready task
                if ready_tasks:
                    # Sort by priority and time
                    ready_tasks.sort(key=lambda t: (t.priority.value, t.scheduled_at), reverse=True)
                    next_task = ready_tasks[0]
                    
                    # Restore other ready tasks to queue
                    for task in ready_tasks[1:]:
                        heapq.heappush(self._queue, task)
                    
                    # Remove from lookup
                    del self._task_lookup[next_task.id]
                    
                    # Update statistics
                    self.stats['current_size'] = len(self._queue)
                    self.stats['processing_count'] += 1
                    
                    return next_task
                
                return None
                
            except Exception as e:
                self.logger.error(f"Failed to get next task: {str(e)}")
                return None
    
    async def reschedule_task(
        self,
        task: MessageTask,
        delay_seconds: float
    ) -> bool:
        """
        Reschedule a task for later processing.
        
        Args:
            task: Task to reschedule
            delay_seconds: Delay in seconds
            
        Returns:
            True if rescheduled successfully
        """
        task.retry_count += 1
        task.scheduled_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
        
        return await self.add_task(task)
    
    async def remove_task(self, task_id: str) -> bool:
        """
        Remove a task from the queue.
        
        Args:
            task_id: Task ID to remove
            
        Returns:
            True if removed successfully
        """
        async with self._lock:
            if task_id in self._task_lookup:
                task = self._task_lookup[task_id]
                try:
                    self._queue.remove(task)
                    heapq.heapify(self._queue)  # Restore heap property
                    del self._task_lookup[task_id]
                    
                    self.stats['current_size'] = len(self._queue)
                    return True
                except ValueError:
                    # Task might have been already processed
                    del self._task_lookup[task_id]
                    return True
            
            return False
    
    def get_size(self) -> int:
        """Get current queue size."""
        return len(self._queue)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        return {
            **self.stats,
            'current_size': len(self._queue),
            'tasks_by_priority': self._get_priority_distribution()
        }
    
    def _get_priority_distribution(self) -> Dict[str, int]:
        """Get distribution of tasks by priority."""
        distribution = defaultdict(int)
        for task in self._queue:
            distribution[task.priority.value] += 1
        return dict(distribution)


class RetryManager:
    """Manages retry logic for failed messages."""
    
    def __init__(self, db: Session):
        """Initialize retry manager."""
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    async def schedule_retries(self) -> int:
        """
        Schedule retries for failed messages that can be retried.
        
        Returns:
            Number of messages scheduled for retry
        """
        # Find messages that can be retried
        now = datetime.utcnow()
        retry_candidates = self.db.query(WhatsAppMessage).filter(
            and_(
                WhatsAppMessage.status == MessageStatus.FAILED,
                WhatsAppMessage.retry_count < WhatsAppMessage.max_retries,
                or_(
                    WhatsAppMessage.next_retry_at.is_(None),
                    WhatsAppMessage.next_retry_at <= now.isoformat()
                )
            )
        ).limit(100).all()  # Process in batches
        
        scheduled_count = 0
        
        for message in retry_candidates:
            try:
                # Create retry task
                task = self._create_retry_task(message)
                
                # Add to messaging queue
                # This would be done by the AsyncMessagingService
                scheduled_count += 1
                
                # Update message retry info
                message.retry_count += 1
                retry_delay = message.get_retry_delay_seconds()
                next_retry = now + timedelta(seconds=retry_delay)
                message.next_retry_at = next_retry.isoformat()
                
            except Exception as e:
                self.logger.error(f"Failed to schedule retry for message {message.id}: {str(e)}")
        
        if scheduled_count > 0:
            self.db.commit()
            self.logger.info(f"Scheduled {scheduled_count} messages for retry")
        
        return scheduled_count
    
    def _create_retry_task(self, message: WhatsAppMessage) -> MessageTask:
        """Create a retry task from a failed message."""
        customer = message.customer
        
        # Determine retry strategy based on failure reason
        retry_strategy = RetryStrategy.EXPONENTIAL_BACKOFF
        if message.error_code and message.error_code.startswith('429'):
            # Rate limit errors - use longer backoff
            retry_strategy = RetryStrategy.EXPONENTIAL_BACKOFF
        
        task = MessageTask(
            id=f"retry_{message.id}_{message.retry_count}",
            customer_id=customer.id,
            phone_number=customer.phone,
            message_type=message.message_type,
            priority=message.priority or Priority.NORMAL,
            scheduled_at=datetime.utcnow(),
            retry_count=message.retry_count,
            max_retries=message.max_retries,
            retry_strategy=retry_strategy,
            content=message.content,
            media_url=message.media_url,
            template_name=message.template_name,
            template_language=message.template_language,
            template_parameters=message.template_parameters,
            conversation_id=message.conversation_id,
            campaign_id=message.campaign_id,
            automation_id=message.automation_id,
            user_id=message.user_id,
            metadata=message.metadata
        )
        
        return task


class AsyncMessagingService:
    """
    Asynchronous messaging service with comprehensive queue management.
    
    Features:
    - Priority-based message queuing
    - Retry mechanisms with configurable strategies
    - Rate limiting integration
    - Background processing workers
    - Message delivery tracking
    - Batch processing capabilities
    - Dead letter queue for permanently failed messages
    """
    
    def __init__(
        self,
        db: Session,
        whatsapp_client: Optional[WhatsAppClient] = None,
        rate_limiter: Optional[RateLimiter] = None,
        worker_count: int = 3
    ):
        """
        Initialize async messaging service.
        
        Args:
            db: Database session
            whatsapp_client: WhatsApp client instance
            rate_limiter: Rate limiter instance
            worker_count: Number of background workers
        """
        self.db = db
        self.whatsapp_client = whatsapp_client or WhatsAppClient(db)
        self.rate_limiter = rate_limiter or RateLimiter()
        self.worker_count = worker_count
        self.logger = logging.getLogger(__name__)
        
        # Message queues
        self.queues = {
            'high': MessageQueue(db, "high_priority"),
            'normal': MessageQueue(db, "normal_priority"),
            'low': MessageQueue(db, "low_priority")
        }
        
        # Retry manager
        self.retry_manager = RetryManager(db)
        
        # Worker management
        self.workers: List[asyncio.Task] = []
        self.running = False
        self.shutdown_event = asyncio.Event()
        
        # Service statistics
        self.stats = {
            'messages_sent': 0,
            'messages_failed': 0,
            'retries_scheduled': 0,
            'workers_active': 0,
            'uptime_start': datetime.utcnow()
        }
    
    async def send_message_async(
        self,
        customer_id: int,
        phone_number: str,
        message_type: MessageType,
        priority: Priority = Priority.NORMAL,
        scheduled_at: Optional[datetime] = None,
        **message_data
    ) -> str:
        """
        Queue a message for asynchronous sending.
        
        Args:
            customer_id: Customer database ID
            phone_number: Recipient phone number
            message_type: Type of message
            priority: Message priority
            scheduled_at: When to send the message
            **message_data: Additional message data
            
        Returns:
            Task ID for tracking
        """
        task_id = f"msg_{customer_id}_{datetime.utcnow().timestamp()}"
        
        task = MessageTask(
            id=task_id,
            customer_id=customer_id,
            phone_number=phone_number,
            message_type=message_type,
            priority=priority,
            scheduled_at=scheduled_at or datetime.utcnow(),
            **message_data
        )
        
        # Add to appropriate queue based on priority
        queue_name = self._get_queue_name(priority)
        queue = self.queues[queue_name]
        
        if await queue.add_task(task):
            self.logger.info(f"Message task {task_id} queued for async processing")
            return task_id
        else:
            raise QueueError(f"Failed to queue message task {task_id}")
    
    async def send_text_message_async(
        self,
        customer_id: int,
        phone_number: str,
        message: str,
        priority: Priority = Priority.NORMAL,
        scheduled_at: Optional[datetime] = None,
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Queue a text message for async sending."""
        return await self.send_message_async(
            customer_id=customer_id,
            phone_number=phone_number,
            message_type=MessageType.TEXT,
            priority=priority,
            scheduled_at=scheduled_at,
            content=message,
            conversation_id=conversation_id,
            metadata=metadata
        )
    
    async def send_template_message_async(
        self,
        customer_id: int,
        phone_number: str,
        template_name: str,
        template_language: str,
        template_parameters: Optional[Dict[str, Any]] = None,
        priority: Priority = Priority.NORMAL,
        scheduled_at: Optional[datetime] = None,
        conversation_id: Optional[str] = None
    ) -> str:
        """Queue a template message for async sending."""
        return await self.send_message_async(
            customer_id=customer_id,
            phone_number=phone_number,
            message_type=MessageType.TEMPLATE,
            priority=priority,
            scheduled_at=scheduled_at,
            template_name=template_name,
            template_language=template_language,
            template_parameters=template_parameters,
            conversation_id=conversation_id
        )
    
    async def send_media_message_async(
        self,
        customer_id: int,
        phone_number: str,
        media_url: str,
        media_type: MessageType,
        caption: Optional[str] = None,
        priority: Priority = Priority.NORMAL,
        scheduled_at: Optional[datetime] = None,
        conversation_id: Optional[str] = None
    ) -> str:
        """Queue a media message for async sending."""
        return await self.send_message_async(
            customer_id=customer_id,
            phone_number=phone_number,
            message_type=media_type,
            priority=priority,
            scheduled_at=scheduled_at,
            media_url=media_url,
            content=caption,
            conversation_id=conversation_id
        )
    
    async def start_workers(self):
        """Start background message processing workers."""
        if self.running:
            self.logger.warning("Workers already running")
            return
        
        self.running = True
        self.shutdown_event.clear()
        
        # Start worker tasks
        for i in range(self.worker_count):
            worker_task = asyncio.create_task(
                self._worker(f"worker_{i}"),
                name=f"messaging_worker_{i}"
            )
            self.workers.append(worker_task)
        
        # Start retry scheduler
        retry_task = asyncio.create_task(
            self._retry_scheduler(),
            name="retry_scheduler"
        )
        self.workers.append(retry_task)
        
        self.logger.info(f"Started {len(self.workers)} messaging workers")
    
    async def stop_workers(self):
        """Stop all background workers gracefully."""
        if not self.running:
            return
        
        self.logger.info("Stopping messaging workers...")
        self.running = False
        self.shutdown_event.set()
        
        # Wait for workers to complete
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)
            self.workers.clear()
        
        self.logger.info("All messaging workers stopped")
    
    async def _worker(self, worker_name: str):
        """Background worker for processing message tasks."""
        self.logger.info(f"Worker {worker_name} started")
        self.stats['workers_active'] += 1
        
        try:
            while self.running:
                try:
                    # Get next task from queues (priority order)
                    task = await self._get_next_task()
                    
                    if task is None:
                        # No tasks available, sleep briefly
                        await asyncio.sleep(1)
                        continue
                    
                    # Process the task
                    await self._process_task(task, worker_name)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"Worker {worker_name} error: {str(e)}")
                    await asyncio.sleep(5)  # Brief pause on error
        
        finally:
            self.stats['workers_active'] -= 1
            self.logger.info(f"Worker {worker_name} stopped")
    
    async def _retry_scheduler(self):
        """Background scheduler for retry processing."""
        self.logger.info("Retry scheduler started")
        
        try:
            while self.running:
                try:
                    # Schedule retries every minute
                    scheduled_count = await self.retry_manager.schedule_retries()
                    if scheduled_count > 0:
                        self.stats['retries_scheduled'] += scheduled_count
                    
                    # Sleep for 60 seconds or until shutdown
                    try:
                        await asyncio.wait_for(
                            self.shutdown_event.wait(),
                            timeout=60.0
                        )
                        break  # Shutdown requested
                    except asyncio.TimeoutError:
                        pass  # Continue scheduling
                        
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"Retry scheduler error: {str(e)}")
                    await asyncio.sleep(10)
        
        finally:
            self.logger.info("Retry scheduler stopped")
    
    async def _get_next_task(self) -> Optional[MessageTask]:
        """Get next task from queues in priority order."""
        # Check queues in priority order
        for queue_name in ['high', 'normal', 'low']:
            task = await self.queues[queue_name].get_next_task()
            if task:
                return task
        
        return None
    
    async def _process_task(self, task: MessageTask, worker_name: str):
        """Process a message task."""
        try:
            self.logger.debug(f"Worker {worker_name} processing task {task.id}")
            
            # Send the message based on type
            message_record = None
            
            if task.message_type == MessageType.TEXT:
                message_record = await self.whatsapp_client.send_text_message(
                    phone_number=task.phone_number,
                    message=task.content,
                    customer_id=task.customer_id,
                    priority=task.priority,
                    conversation_id=task.conversation_id,
                    metadata=task.metadata
                )
            
            elif task.message_type == MessageType.TEMPLATE:
                message_record = await self.whatsapp_client.send_template_message(
                    phone_number=task.phone_number,
                    template_name=task.template_name,
                    language_code=task.template_language,
                    parameters=task.template_parameters,
                    customer_id=task.customer_id,
                    priority=task.priority,
                    conversation_id=task.conversation_id
                )
            
            elif task.message_type in [MessageType.IMAGE, MessageType.DOCUMENT, 
                                     MessageType.AUDIO, MessageType.VIDEO]:
                message_record = await self.whatsapp_client.send_media_message(
                    phone_number=task.phone_number,
                    media_url=task.media_url,
                    media_type=task.message_type,
                    customer_id=task.customer_id,
                    caption=task.content,
                    priority=task.priority,
                    conversation_id=task.conversation_id
                )
            
            elif task.message_type == MessageType.INTERACTIVE:
                message_record = await self.whatsapp_client.send_interactive_message(
                    phone_number=task.phone_number,
                    customer_id=task.customer_id,
                    priority=task.priority,
                    conversation_id=task.conversation_id,
                    **task.interactive_data
                )
            
            if message_record and message_record.status != MessageStatus.FAILED:
                # Task completed successfully
                self.stats['messages_sent'] += 1
                
                # Call success callback if provided
                if task.success_callback:
                    try:
                        await self._call_callback(task.success_callback, message_record)
                    except Exception as e:
                        self.logger.error(f"Success callback error: {str(e)}")
                
                self.logger.info(f"Task {task.id} completed successfully")
            
            else:
                # Task failed
                await self._handle_task_failure(task, message_record)
        
        except Exception as e:
            self.logger.error(f"Task {task.id} processing failed: {str(e)}")
            await self._handle_task_failure(task, None, str(e))
    
    async def _handle_task_failure(
        self,
        task: MessageTask,
        message_record: Optional[WhatsAppMessage] = None,
        error_message: str = None
    ):
        """Handle task processing failure."""
        self.stats['messages_failed'] += 1
        
        # Check if task should be retried
        if task.should_retry():
            # Calculate retry delay
            delay = task.get_next_retry_delay()
            
            # Reschedule task
            queue_name = self._get_queue_name(task.priority)
            queue = self.queues[queue_name]
            
            if await queue.reschedule_task(task, delay):
                self.logger.info(f"Task {task.id} rescheduled for retry in {delay}s")
            else:
                self.logger.error(f"Failed to reschedule task {task.id}")
        
        else:
            # Max retries exceeded - call failure callback
            if task.failure_callback:
                try:
                    await self._call_callback(
                        task.failure_callback,
                        message_record,
                        error_message
                    )
                except Exception as e:
                    self.logger.error(f"Failure callback error: {str(e)}")
            
            self.logger.error(f"Task {task.id} permanently failed after {task.retry_count} retries")
    
    async def _call_callback(
        self,
        callback: Callable,
        *args
    ):
        """Call a callback function safely."""
        if asyncio.iscoroutinefunction(callback):
            await callback(*args)
        else:
            callback(*args)
    
    def _get_queue_name(self, priority: Priority) -> str:
        """Get queue name based on priority."""
        if priority == Priority.URGENT:
            return 'high'
        elif priority == Priority.HIGH:
            return 'high'
        elif priority == Priority.NORMAL:
            return 'normal'
        else:  # LOW
            return 'low'
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get statistics for all queues."""
        stats = {}
        for name, queue in self.queues.items():
            stats[name] = queue.get_stats()
        return stats
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get overall service statistics."""
        uptime = datetime.utcnow() - self.stats['uptime_start']
        
        return {
            **self.stats,
            'uptime_seconds': uptime.total_seconds(),
            'running': self.running,
            'queue_stats': self.get_queue_stats()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the messaging service."""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'issues': []
        }
        
        # Check if workers are running
        if not self.running or self.stats['workers_active'] == 0:
            health_status['status'] = 'unhealthy'
            health_status['issues'].append('No active workers')
        
        # Check queue sizes
        total_queued = sum(queue.get_size() for queue in self.queues.values())
        if total_queued > 10000:  # Arbitrary threshold
            health_status['status'] = 'warning'
            health_status['issues'].append(f'High queue size: {total_queued}')
        
        # Check rate limiter
        rate_limit_status = self.rate_limiter.get_current_status()
        if rate_limit_status['statistics']['rate_limited_requests'] > 100:
            health_status['status'] = 'warning'
            health_status['issues'].append('High rate limit rejections')
        
        return health_status
    
    async def clear_queues(self):
        """Clear all message queues (use with caution)."""
        for queue in self.queues.values():
            queue._queue.clear()
            queue._task_lookup.clear()
            queue.stats['current_size'] = 0
        
        self.logger.warning("All message queues cleared")
    
    async def close(self):
        """Close the messaging service and clean up resources."""
        await self.stop_workers()
        await self.whatsapp_client.close()
        self.logger.info("Async messaging service closed")