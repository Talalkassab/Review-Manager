"""Initial schema migration with all models

Revision ID: 001
Revises: 
Create Date: 2024-01-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all initial tables for the Restaurant AI Assistant."""
    
    # Create restaurants table
    op.create_table('restaurants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('name_arabic', sa.String(length=200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('description_arabic', sa.Text(), nullable=True),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('website_url', sa.String(length=500), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('address_arabic', sa.Text(), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=False),
        sa.Column('postal_code', sa.String(length=20), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('default_language', sa.String(length=5), nullable=False),
        sa.Column('timezone', sa.String(length=50), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('operating_hours', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('whatsapp_business_phone', sa.String(length=20), nullable=True),
        sa.Column('whatsapp_verified', sa.Boolean(), nullable=False),
        sa.Column('whatsapp_active', sa.Boolean(), nullable=False),
        sa.Column('ai_enabled', sa.Boolean(), nullable=False),
        sa.Column('sentiment_analysis_enabled', sa.Boolean(), nullable=False),
        sa.Column('auto_response_enabled', sa.Boolean(), nullable=False),
        sa.Column('message_templates', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('response_time_target_hours', sa.Integer(), nullable=False),
        sa.Column('review_follow_up_enabled', sa.Boolean(), nullable=False),
        sa.Column('max_customers_per_month', sa.Integer(), nullable=False),
        sa.Column('current_month_customers', sa.Integer(), nullable=False),
        sa.Column('subscription_active', sa.Boolean(), nullable=False),
        sa.Column('subscription_expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_featured', sa.Boolean(), nullable=False),
        sa.Column('google_business_id', sa.String(length=255), nullable=True),
        sa.Column('google_reviews_url', sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_restaurants_name'), 'restaurants', ['name'], unique=False)
    op.create_index(op.f('ix_restaurants_email'), 'restaurants', ['email'], unique=False)

    # Create users table 
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('email', sa.String(length=320), nullable=False),
        sa.Column('hashed_password', sa.String(length=1024), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('preferred_language', sa.String(length=5), nullable=False),
        sa.Column('role', sa.Enum('SUPER_ADMIN', 'RESTAURANT_OWNER', 'MANAGER', 'SERVER', 'VIEW_ONLY', name='userrolechoice'), nullable=False),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('login_count', sa.String(), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create customers table
    op.create_table('customers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('phone_number', sa.String(length=20), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('preferred_language', sa.String(length=5), nullable=False),
        sa.Column('whatsapp_opt_in', sa.Boolean(), nullable=False),
        sa.Column('email_opt_in', sa.Boolean(), nullable=False),
        sa.Column('visit_date', sa.DateTime(), nullable=False),
        sa.Column('table_number', sa.String(length=10), nullable=True),
        sa.Column('server_name', sa.String(length=100), nullable=True),
        sa.Column('party_size', sa.Integer(), nullable=False),
        sa.Column('order_details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('order_total', sa.Float(), nullable=True),
        sa.Column('special_requests', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('last_contacted_at', sa.DateTime(), nullable=True),
        sa.Column('contact_attempts', sa.Integer(), nullable=False),
        sa.Column('max_contact_attempts', sa.Integer(), nullable=False),
        sa.Column('feedback_received_at', sa.DateTime(), nullable=True),
        sa.Column('feedback_text', sa.Text(), nullable=True),
        sa.Column('feedback_sentiment', sa.String(length=10), nullable=True),
        sa.Column('feedback_confidence_score', sa.Float(), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('google_review_requested_at', sa.DateTime(), nullable=True),
        sa.Column('google_review_link_sent', sa.Boolean(), nullable=False),
        sa.Column('google_review_completed', sa.Boolean(), nullable=False),
        sa.Column('google_review_url', sa.String(length=500), nullable=True),
        sa.Column('requires_follow_up', sa.Boolean(), nullable=False),
        sa.Column('follow_up_notes', sa.Text(), nullable=True),
        sa.Column('issue_resolved', sa.Boolean(), nullable=False),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('is_repeat_customer', sa.Boolean(), nullable=False),
        sa.Column('visit_count', sa.Integer(), nullable=False),
        sa.Column('first_visit_date', sa.DateTime(), nullable=True),
        sa.Column('last_visit_date', sa.DateTime(), nullable=True),
        sa.Column('data_retention_date', sa.DateTime(), nullable=True),
        sa.Column('gdpr_consent', sa.Boolean(), nullable=False),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_customers_phone_number'), 'customers', ['phone_number'], unique=False)
    op.create_index(op.f('ix_customers_email'), 'customers', ['email'], unique=False)
    op.create_index(op.f('ix_customers_restaurant_id'), 'customers', ['restaurant_id'], unique=False)
    op.create_index(op.f('ix_customers_status'), 'customers', ['status'], unique=False)

    # Create agent_personas table
    op.create_table('agent_personas',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False),
        sa.Column('personality_traits', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('tone_style', sa.String(length=20), nullable=False),
        sa.Column('language_style', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('response_patterns', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('cultural_awareness', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('usage_count', sa.Integer(), nullable=False),
        sa.Column('success_rate', sa.Float(), nullable=False),
        sa.Column('average_response_time_seconds', sa.Float(), nullable=False),
        sa.Column('conversion_metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_personas_name'), 'agent_personas', ['name'], unique=False)
    op.create_index(op.f('ix_agent_personas_restaurant_id'), 'agent_personas', ['restaurant_id'], unique=False)

    # Create message_flows table
    op.create_table('message_flows',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('flow_type', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('trigger_conditions', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('message_sequence', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('personalization_rules', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('response_intelligence', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('execution_count', sa.Integer(), nullable=False),
        sa.Column('completion_rate', sa.Float(), nullable=False),
        sa.Column('average_customer_satisfaction', sa.Float(), nullable=False),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('default_persona_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['default_persona_id'], ['agent_personas.id'], ),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_message_flows_name'), 'message_flows', ['name'], unique=False)
    op.create_index(op.f('ix_message_flows_restaurant_id'), 'message_flows', ['restaurant_id'], unique=False)

    # Create campaigns table
    op.create_table('campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('campaign_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('scheduled_start_at', sa.DateTime(), nullable=True),
        sa.Column('scheduled_end_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('targeting_config', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('message_variants', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('default_language', sa.String(length=5), nullable=False),
        sa.Column('scheduling_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('max_recipients', sa.Integer(), nullable=True),
        sa.Column('send_rate_per_hour', sa.Integer(), nullable=False),
        sa.Column('budget_limit_usd', sa.Float(), nullable=True),
        sa.Column('estimated_cost_usd', sa.Float(), nullable=True),
        sa.Column('actual_cost_usd', sa.Float(), nullable=False),
        sa.Column('recipients_count', sa.Integer(), nullable=False),
        sa.Column('messages_sent', sa.Integer(), nullable=False),
        sa.Column('messages_delivered', sa.Integer(), nullable=False),
        sa.Column('messages_read', sa.Integer(), nullable=False),
        sa.Column('messages_failed', sa.Integer(), nullable=False),
        sa.Column('responses_received', sa.Integer(), nullable=False),
        sa.Column('is_ab_test', sa.Boolean(), nullable=False),
        sa.Column('ab_test_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_campaigns_name'), 'campaigns', ['name'], unique=False)
    op.create_index(op.f('ix_campaigns_status'), 'campaigns', ['status'], unique=False)
    op.create_index(op.f('ix_campaigns_restaurant_id'), 'campaigns', ['restaurant_id'], unique=False)

    # Create whatsapp_messages table
    op.create_table('whatsapp_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('whatsapp_message_id', sa.String(length=255), nullable=True),
        sa.Column('message_type', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('template_name', sa.String(length=100), nullable=True),
        sa.Column('template_parameters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('language', sa.String(length=5), nullable=False),
        sa.Column('direction', sa.String(length=10), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('failed_at', sa.DateTime(), nullable=True),
        sa.Column('error_code', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('max_retries', sa.Integer(), nullable=False),
        sa.Column('context', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_automated', sa.Boolean(), nullable=False),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sent_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ),
        sa.ForeignKeyConstraint(['sent_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_whatsapp_messages_whatsapp_message_id'), 'whatsapp_messages', ['whatsapp_message_id'], unique=True)
    op.create_index(op.f('ix_whatsapp_messages_status'), 'whatsapp_messages', ['status'], unique=False)
    op.create_index(op.f('ix_whatsapp_messages_campaign_id'), 'whatsapp_messages', ['campaign_id'], unique=False)
    op.create_index(op.f('ix_whatsapp_messages_restaurant_id'), 'whatsapp_messages', ['restaurant_id'], unique=False)
    op.create_index(op.f('ix_whatsapp_messages_customer_id'), 'whatsapp_messages', ['customer_id'], unique=False)

    # Create conversation_threads table
    op.create_table('conversation_threads',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('thread_identifier', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('last_message_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('ai_context', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('customer_sentiment', sa.String(length=10), nullable=True),
        sa.Column('requires_human_intervention', sa.Boolean(), nullable=False),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['assigned_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversation_threads_thread_identifier'), 'conversation_threads', ['thread_identifier'], unique=True)
    op.create_index(op.f('ix_conversation_threads_restaurant_id'), 'conversation_threads', ['restaurant_id'], unique=False)

    # Create campaign_recipients table
    op.create_table('campaign_recipients',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('variant_id', sa.String(length=50), nullable=True),
        sa.Column('personalization_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('scheduled_send_time', sa.DateTime(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('responded_at', sa.DateTime(), nullable=True),
        sa.Column('response_text', sa.Text(), nullable=True),
        sa.Column('response_sentiment', sa.String(length=10), nullable=True),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.ForeignKeyConstraint(['message_id'], ['whatsapp_messages.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_campaign_recipients_status'), 'campaign_recipients', ['status'], unique=False)
    op.create_index(op.f('ix_campaign_recipients_variant_id'), 'campaign_recipients', ['variant_id'], unique=False)
    op.create_index(op.f('ix_campaign_recipients_campaign_id'), 'campaign_recipients', ['campaign_id'], unique=False)

    # Create ai_interactions table
    op.create_table('ai_interactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('interaction_type', sa.String(length=50), nullable=False),
        sa.Column('trigger_event', sa.String(length=100), nullable=False),
        sa.Column('input_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('ai_response', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=False),
        sa.Column('ai_model_used', sa.String(length=100), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=True),
        sa.Column('prompt_tokens', sa.Integer(), nullable=False),
        sa.Column('completion_tokens', sa.Integer(), nullable=False),
        sa.Column('total_tokens', sa.Integer(), nullable=False),
        sa.Column('estimated_cost_usd', sa.Float(), nullable=False),
        sa.Column('conversation_context', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('personalization_applied', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('human_feedback_score', sa.Integer(), nullable=True),
        sa.Column('human_feedback_notes', sa.Text(), nullable=True),
        sa.Column('customer_satisfaction_inferred', sa.Boolean(), nullable=True),
        sa.Column('requires_review', sa.Boolean(), nullable=False),
        sa.Column('review_reason', sa.String(length=200), nullable=True),
        sa.Column('learning_tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('resulted_in_response', sa.Boolean(), nullable=False),
        sa.Column('resulted_in_escalation', sa.Boolean(), nullable=False),
        sa.Column('resulted_in_positive_outcome', sa.Boolean(), nullable=True),
        sa.Column('restaurant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_persona_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('message_flow_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('related_message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['agent_persona_id'], ['agent_personas.id'], ),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.ForeignKeyConstraint(['message_flow_id'], ['message_flows.id'], ),
        sa.ForeignKeyConstraint(['related_message_id'], ['whatsapp_messages.id'], ),
        sa.ForeignKeyConstraint(['restaurant_id'], ['restaurants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_interactions_interaction_type'), 'ai_interactions', ['interaction_type'], unique=False)
    op.create_index(op.f('ix_ai_interactions_restaurant_id'), 'ai_interactions', ['restaurant_id'], unique=False)
    op.create_index(op.f('ix_ai_interactions_customer_id'), 'ai_interactions', ['customer_id'], unique=False)


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('ai_interactions')
    op.drop_table('campaign_recipients')
    op.drop_table('conversation_threads')
    op.drop_table('whatsapp_messages')
    op.drop_table('campaigns')
    op.drop_table('message_flows')
    op.drop_table('agent_personas')
    op.drop_table('customers')
    op.drop_table('users')
    op.drop_table('restaurants')
    op.execute("DROP TYPE IF EXISTS userrolechoice")