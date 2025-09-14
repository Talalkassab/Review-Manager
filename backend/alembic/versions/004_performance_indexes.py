"""Performance optimization indexes

Revision ID: 004_performance_indexes
Revises: 003_previous_migration
Create Date: 2024-09-14 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '004_performance_indexes'
down_revision = '003_previous_migration'  # Replace with actual previous revision
branch_labels = None
depends_on = None


def upgrade():
    """Add performance optimization indexes."""

    # Customer table indexes for common query patterns

    # Phone number and restaurant lookup (most common customer lookup)
    op.create_index(
        'idx_customers_phone_restaurant',
        'customers',
        ['phone_number', 'restaurant_id'],
        postgresql_where=sa.text('is_deleted = FALSE'),
        postgresql_concurrently=True
    )

    # Status and restaurant lookup (for filtering by status)
    op.create_index(
        'idx_customers_status_restaurant',
        'customers',
        ['status', 'restaurant_id'],
        postgresql_where=sa.text('is_deleted = FALSE'),
        postgresql_concurrently=True
    )

    # Created date and restaurant (for chronological listings)
    op.create_index(
        'idx_customers_created_restaurant',
        'customers',
        [sa.text('created_at DESC'), 'restaurant_id'],
        postgresql_where=sa.text('is_deleted = FALSE'),
        postgresql_concurrently=True
    )

    # Feedback sentiment for analytics (partial index)
    op.create_index(
        'idx_customers_feedback_sentiment',
        'customers',
        ['restaurant_id', 'feedback_sentiment', 'created_at'],
        postgresql_where=sa.text('is_deleted = FALSE AND feedback_sentiment IS NOT NULL'),
        postgresql_concurrently=True
    )

    # Email lookup for notifications
    op.create_index(
        'idx_customers_email_restaurant',
        'customers',
        ['email', 'restaurant_id'],
        postgresql_where=sa.text('is_deleted = FALSE AND email IS NOT NULL'),
        postgresql_concurrently=True
    )

    # WhatsApp Messages table indexes

    # Customer and date lookup (conversation history)
    op.create_index(
        'idx_whatsapp_messages_customer_date',
        'whatsapp_messages',
        ['customer_id', sa.text('created_at DESC')],
        postgresql_concurrently=True
    )

    # Restaurant and date lookup (restaurant message history)
    op.create_index(
        'idx_whatsapp_messages_restaurant_date',
        'whatsapp_messages',
        ['restaurant_id', sa.text('created_at DESC')],
        postgresql_concurrently=True
    )

    # Direction and status for message analytics
    op.create_index(
        'idx_whatsapp_messages_direction_status',
        'whatsapp_messages',
        ['direction', 'status'],
        postgresql_concurrently=True
    )

    # Message type and restaurant for template analytics
    op.create_index(
        'idx_whatsapp_messages_type_restaurant',
        'whatsapp_messages',
        ['message_type', 'restaurant_id', 'created_at'],
        postgresql_concurrently=True
    )

    # Failed messages for retry processing
    op.create_index(
        'idx_whatsapp_messages_failed',
        'whatsapp_messages',
        ['status', 'retry_count', 'created_at'],
        postgresql_where=sa.text("status = 'failed' AND retry_count < max_retries"),
        postgresql_concurrently=True
    )

    # Analytics composite indexes

    # Customer analytics by restaurant and time period
    op.create_index(
        'idx_analytics_customer_restaurant_time',
        'customers',
        ['restaurant_id', 'visit_count', 'created_at', 'feedback_sentiment'],
        postgresql_where=sa.text('is_deleted = FALSE'),
        postgresql_concurrently=True
    )

    # Message analytics composite index
    op.create_index(
        'idx_analytics_messages_comprehensive',
        'whatsapp_messages',
        ['restaurant_id', 'direction', 'created_at', 'customer_id'],
        postgresql_concurrently=True
    )

    # Campaign performance index (if campaigns table exists)
    try:
        op.create_index(
            'idx_whatsapp_messages_campaign',
            'whatsapp_messages',
            ['campaign_id', 'status', 'created_at'],
            postgresql_where=sa.text('campaign_id IS NOT NULL'),
            postgresql_concurrently=True
        )
    except:
        # Campaign table might not exist yet
        pass


def downgrade():
    """Remove performance optimization indexes."""

    # Remove indexes in reverse order

    try:
        op.drop_index('idx_whatsapp_messages_campaign', table_name='whatsapp_messages')
    except:
        pass

    op.drop_index('idx_analytics_messages_comprehensive', table_name='whatsapp_messages')
    op.drop_index('idx_analytics_customer_restaurant_time', table_name='customers')
    op.drop_index('idx_whatsapp_messages_failed', table_name='whatsapp_messages')
    op.drop_index('idx_whatsapp_messages_type_restaurant', table_name='whatsapp_messages')
    op.drop_index('idx_whatsapp_messages_direction_status', table_name='whatsapp_messages')
    op.drop_index('idx_whatsapp_messages_restaurant_date', table_name='whatsapp_messages')
    op.drop_index('idx_whatsapp_messages_customer_date', table_name='whatsapp_messages')
    op.drop_index('idx_customers_email_restaurant', table_name='customers')
    op.drop_index('idx_customers_feedback_sentiment', table_name='customers')
    op.drop_index('idx_customers_created_restaurant', table_name='customers')
    op.drop_index('idx_customers_status_restaurant', table_name='customers')
    op.drop_index('idx_customers_phone_restaurant', table_name='customers')