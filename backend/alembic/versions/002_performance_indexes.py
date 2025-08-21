"""Add performance indexes and constraints

Revision ID: 002
Revises: 001
Create Date: 2024-01-15 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes and constraints for optimization."""
    
    # Enable required PostgreSQL extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"pg_trgm\"")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"unaccent\"")
    
    # Customer search and performance indexes
    op.create_index('idx_customers_phone_search', 'customers', 
                   [sa.text('phone_number gin_trgm_ops')], 
                   postgresql_using='gin', postgresql_concurrently=True)
    
    op.create_index('idx_customers_name_search', 'customers', 
                   [sa.text("(first_name || ' ' || COALESCE(last_name, '')) gin_trgm_ops")], 
                   postgresql_using='gin', postgresql_concurrently=True)
    
    op.create_index('idx_customers_visit_date_status', 'customers', 
                   [sa.desc('visit_date'), 'status'], 
                   postgresql_where=sa.text('is_deleted = false'),
                   postgresql_concurrently=True)
    
    op.create_index('idx_customers_feedback_sentiment', 'customers', 
                   ['feedback_sentiment', 'rating'], 
                   postgresql_where=sa.text('feedback_sentiment IS NOT NULL'),
                   postgresql_concurrently=True)
    
    op.create_index('idx_customers_requires_follow_up', 'customers', 
                   ['requires_follow_up', 'restaurant_id', 'created_at'], 
                   postgresql_where=sa.text('requires_follow_up = true AND is_deleted = false'),
                   postgresql_concurrently=True)
    
    # WhatsApp message performance indexes
    op.create_index('idx_whatsapp_messages_conversation', 'whatsapp_messages', 
                   ['customer_id', sa.desc('created_at')], 
                   postgresql_where=sa.text("direction = 'outbound'"),
                   postgresql_concurrently=True)
    
    op.create_index('idx_whatsapp_messages_status_retry', 'whatsapp_messages', 
                   ['status', 'retry_count'], 
                   postgresql_where=sa.text("status = 'failed'"),
                   postgresql_concurrently=True)
    
    op.create_index('idx_whatsapp_messages_delivery_tracking', 'whatsapp_messages', 
                   ['restaurant_id', 'status', 'sent_at'], 
                   postgresql_where=sa.text('sent_at IS NOT NULL'),
                   postgresql_concurrently=True)
    
    # Campaign performance indexes
    op.create_index('idx_campaigns_active_scheduled', 'campaigns', 
                   ['scheduled_start_at'], 
                   postgresql_where=sa.text("status = 'scheduled'"),
                   postgresql_concurrently=True)
    
    op.create_index('idx_campaigns_performance_metrics', 'campaigns', 
                   ['restaurant_id', 'status', sa.desc('created_at')], 
                   postgresql_where=sa.text('is_deleted = false'),
                   postgresql_concurrently=True)
    
    op.create_index('idx_campaign_recipients_pending', 'campaign_recipients', 
                   ['campaign_id', 'status'], 
                   postgresql_where=sa.text("status = 'pending'"),
                   postgresql_concurrently=True)
    
    op.create_index('idx_campaign_recipients_scheduled', 'campaign_recipients', 
                   ['scheduled_send_time', 'status'], 
                   postgresql_where=sa.text('scheduled_send_time IS NOT NULL'),
                   postgresql_concurrently=True)
    
    # AI interaction analytics indexes
    op.create_index('idx_ai_interactions_performance', 'ai_interactions', 
                   ['restaurant_id', sa.desc('created_at'), 'confidence_score'], 
                   postgresql_concurrently=True)
    
    op.create_index('idx_ai_interactions_review', 'ai_interactions', 
                   ['requires_review', 'created_at'], 
                   postgresql_where=sa.text('requires_review = true'),
                   postgresql_concurrently=True)
    
    op.create_index('idx_ai_interactions_persona_performance', 'ai_interactions', 
                   ['agent_persona_id', 'resulted_in_positive_outcome', 'created_at'], 
                   postgresql_where=sa.text('agent_persona_id IS NOT NULL'),
                   postgresql_concurrently=True)
    
    op.create_index('idx_ai_interactions_cost_tracking', 'ai_interactions', 
                   ['restaurant_id', 'ai_model_used', sa.desc('created_at'), 'estimated_cost_usd'], 
                   postgresql_concurrently=True)
    
    # Restaurant operational indexes
    op.create_index('idx_restaurants_active_subscription', 'restaurants', 
                   ['is_active', 'subscription_active'], 
                   postgresql_where=sa.text('is_active = true'),
                   postgresql_concurrently=True)
    
    op.create_index('idx_restaurants_whatsapp_active', 'restaurants', 
                   ['whatsapp_active', 'whatsapp_verified'], 
                   postgresql_where=sa.text('whatsapp_active = true'),
                   postgresql_concurrently=True)
    
    # Agent persona performance indexes
    op.create_index('idx_agent_personas_active_default', 'agent_personas', 
                   ['restaurant_id', 'is_active', 'is_default'], 
                   postgresql_where=sa.text('is_active = true'),
                   postgresql_concurrently=True)
    
    op.create_index('idx_agent_personas_performance', 'agent_personas', 
                   ['restaurant_id', 'success_rate', 'usage_count'], 
                   postgresql_where=sa.text('is_active = true'),
                   postgresql_concurrently=True)
    
    # Message flow execution indexes
    op.create_index('idx_message_flows_trigger_conditions', 'message_flows', 
                   ['restaurant_id', 'flow_type', 'is_active', 'priority'], 
                   postgresql_where=sa.text('is_active = true'),
                   postgresql_concurrently=True)
    
    # Conversation threading indexes
    op.create_index('idx_conversation_threads_active', 'conversation_threads', 
                   ['customer_id', 'status', sa.desc('started_at')], 
                   postgresql_where=sa.text("status = 'active'"),
                   postgresql_concurrently=True)
    
    op.create_index('idx_conversation_threads_human_intervention', 'conversation_threads', 
                   ['requires_human_intervention', 'restaurant_id', 'created_at'], 
                   postgresql_where=sa.text('requires_human_intervention = true'),
                   postgresql_concurrently=True)
    
    # GDPR compliance indexes
    op.create_index('idx_customers_retention_date', 'customers', 
                   ['data_retention_date'], 
                   postgresql_where=sa.text('data_retention_date IS NOT NULL'),
                   postgresql_concurrently=True)
    
    op.create_index('idx_customers_gdpr_consent', 'customers', 
                   ['gdpr_consent', 'restaurant_id', 'created_at'], 
                   postgresql_where=sa.text('gdpr_consent = false'),
                   postgresql_concurrently=True)
    
    # User management indexes
    op.create_index('idx_users_restaurant_role', 'users', 
                   ['restaurant_id', 'role', 'is_active'], 
                   postgresql_where=sa.text('is_active = true AND restaurant_id IS NOT NULL'),
                   postgresql_concurrently=True)
    
    op.create_index('idx_users_last_login', 'users', 
                   [sa.desc('last_login_at'), 'is_active'], 
                   postgresql_where=sa.text('is_active = true'),
                   postgresql_concurrently=True)
    
    # Composite indexes for common query patterns
    op.create_index('idx_customers_restaurant_status_date', 'customers', 
                   ['restaurant_id', 'status', sa.desc('visit_date')], 
                   postgresql_where=sa.text('is_deleted = false'),
                   postgresql_concurrently=True)
    
    op.create_index('idx_whatsapp_messages_customer_direction_date', 'whatsapp_messages', 
                   ['customer_id', 'direction', sa.desc('created_at')], 
                   postgresql_where=sa.text('is_deleted = false'),
                   postgresql_concurrently=True)
    
    # Analytics and reporting indexes
    op.create_index('idx_campaigns_date_range_analysis', 'campaigns', 
                   ['restaurant_id', sa.desc('started_at'), 'status'], 
                   postgresql_where=sa.text("started_at IS NOT NULL"),
                   postgresql_concurrently=True)
    
    op.create_index('idx_ai_interactions_daily_stats', 'ai_interactions', 
                   ['restaurant_id', sa.text("DATE(created_at)"), 'interaction_type'], 
                   postgresql_concurrently=True)


def downgrade() -> None:
    """Remove performance indexes."""
    
    # Drop all custom indexes (keep the basic ones from migration 001)
    indexes_to_drop = [
        'idx_customers_phone_search',
        'idx_customers_name_search', 
        'idx_customers_visit_date_status',
        'idx_customers_feedback_sentiment',
        'idx_customers_requires_follow_up',
        'idx_whatsapp_messages_conversation',
        'idx_whatsapp_messages_status_retry',
        'idx_whatsapp_messages_delivery_tracking',
        'idx_campaigns_active_scheduled',
        'idx_campaigns_performance_metrics',
        'idx_campaign_recipients_pending',
        'idx_campaign_recipients_scheduled',
        'idx_ai_interactions_performance',
        'idx_ai_interactions_review',
        'idx_ai_interactions_persona_performance',
        'idx_ai_interactions_cost_tracking',
        'idx_restaurants_active_subscription',
        'idx_restaurants_whatsapp_active',
        'idx_agent_personas_active_default',
        'idx_agent_personas_performance',
        'idx_message_flows_trigger_conditions',
        'idx_conversation_threads_active',
        'idx_conversation_threads_human_intervention',
        'idx_customers_retention_date',
        'idx_customers_gdpr_consent',
        'idx_users_restaurant_role',
        'idx_users_last_login',
        'idx_customers_restaurant_status_date',
        'idx_whatsapp_messages_customer_direction_date',
        'idx_campaigns_date_range_analysis',
        'idx_ai_interactions_daily_stats'
    ]
    
    for index_name in indexes_to_drop:
        try:
            op.drop_index(index_name)
        except:
            pass  # Index might not exist