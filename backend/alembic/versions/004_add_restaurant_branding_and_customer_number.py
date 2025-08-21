"""Add restaurant branding and customer number fields

Revision ID: 004
Revises: 003
Create Date: 2025-01-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to restaurants table
    op.add_column('restaurants', sa.Column('logo_url', sa.String(length=500), nullable=True))
    op.add_column('restaurants', sa.Column('persona', sa.Text(), nullable=True))
    
    # Add customer_number column to customers table
    op.add_column('customers', sa.Column('customer_number', sa.String(length=50), nullable=True))
    
    # Generate customer numbers for existing customers (SQLite compatible)
    op.execute("""
        UPDATE customers 
        SET customer_number = 'CUST-' || printf('%06d', (SELECT COUNT(*) + 1 FROM customers c2 WHERE c2.created_at < customers.created_at))
        WHERE customer_number IS NULL
    """)
    
    # Make customer_number NOT NULL after populating it
    op.alter_column('customers', 'customer_number', nullable=False)
    
    # Create index on customer_number
    op.create_index('ix_customers_customer_number', 'customers', ['customer_number'])
    
    # Make first_name nullable (optional)
    op.alter_column('customers', 'first_name', nullable=True)


def downgrade():
    # Remove index
    op.drop_index('ix_customers_customer_number', table_name='customers')
    
    # Make first_name required again
    op.alter_column('customers', 'first_name', nullable=False)
    
    # Remove columns
    op.drop_column('customers', 'customer_number')
    op.drop_column('restaurants', 'persona')
    op.drop_column('restaurants', 'logo_url')