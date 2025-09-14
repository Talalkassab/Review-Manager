# Database Optimization Guide

## Overview

This document provides comprehensive guidance on database optimization for the WhatsApp Customer Agent application. It covers query optimization, index management, N+1 query prevention, and performance monitoring.

## Table of Contents

1. [Query Optimization](#query-optimization)
2. [Index Strategy](#index-strategy)
3. [N+1 Query Prevention](#n1-query-prevention)
4. [Connection Pool Configuration](#connection-pool-configuration)
5. [Performance Monitoring](#performance-monitoring)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

## Query Optimization

### 1. Eager Loading Strategies

#### SelectInLoad (Recommended for One-to-Many)
```python
from sqlalchemy.orm import selectinload

# Good: Load customer with all messages in one additional query
customer = await session.execute(
    select(Customer)
    .options(selectinload(Customer.whatsapp_messages))
    .where(Customer.id == customer_id)
)
```

#### JoinedLoad (For One-to-One or Small One-to-Many)
```python
from sqlalchemy.orm import joinedload

# Good: Load customer with restaurant in single query
customer = await session.execute(
    select(Customer)
    .options(joinedload(Customer.restaurant))
    .where(Customer.id == customer_id)
)
```

### 2. Efficient Analytics Queries

#### Single Query for Multiple Metrics
```python
# Good: Get multiple metrics in one query
analytics_query = select(
    func.count(Customer.id).label('total_customers'),
    func.count(case((Customer.created_at >= cutoff_date, Customer.id))).label('new_customers'),
    func.avg(Customer.rating).label('avg_rating')
).where(Customer.restaurant_id == restaurant_id)
```

#### Subquery for Complex Aggregations
```python
# Good: Use subquery to avoid N+1 problems
message_count_subquery = (
    select(
        WhatsAppMessage.customer_id,
        func.count(WhatsAppMessage.id).label('message_count')
    )
    .group_by(WhatsAppMessage.customer_id)
    .subquery()
)

customers_with_counts = await session.execute(
    select(Customer, message_count_subquery.c.message_count)
    .outerjoin(message_count_subquery, Customer.id == message_count_subquery.c.customer_id)
)
```

### 3. Avoiding Common Anti-patterns

#### ❌ Don't: N+1 Queries
```python
# Bad: This will cause N+1 queries
customers = await session.execute(select(Customer))
for customer in customers.scalars():
    messages = await session.execute(
        select(WhatsAppMessage).where(WhatsAppMessage.customer_id == customer.id)
    )
    customer.message_count = len(messages.scalars().all())
```

#### ✅ Do: Use Joins or Subqueries
```python
# Good: Single query with join
result = await session.execute(
    select(Customer, func.count(WhatsAppMessage.id).label('message_count'))
    .outerjoin(WhatsAppMessage, Customer.id == WhatsAppMessage.customer_id)
    .group_by(Customer.id)
)
```

## Index Strategy

### 1. Primary Indexes (Already Created)

#### Customer Table
- `idx_customers_phone_restaurant` - Phone number + restaurant lookup
- `idx_customers_status_restaurant` - Status filtering
- `idx_customers_created_restaurant` - Chronological listing
- `idx_customers_feedback_sentiment` - Analytics queries

#### WhatsApp Messages Table
- `idx_whatsapp_messages_customer_date` - Conversation history
- `idx_whatsapp_messages_restaurant_date` - Restaurant message history
- `idx_whatsapp_messages_direction_status` - Message analytics

### 2. Index Usage Patterns

#### Customer Lookup by Phone (Most Common)
```sql
-- Uses: idx_customers_phone_restaurant
SELECT * FROM customers
WHERE phone_number = '+1234567890'
  AND restaurant_id = 'uuid-here'
  AND is_deleted = FALSE;
```

#### Message History Retrieval
```sql
-- Uses: idx_whatsapp_messages_customer_date
SELECT * FROM whatsapp_messages
WHERE customer_id = 'customer-uuid'
ORDER BY created_at DESC
LIMIT 50;
```

### 3. Index Maintenance

#### Check Index Usage
```sql
-- Monitor index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_tup_read,
    idx_tup_fetch,
    idx_scan
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

#### Identify Unused Indexes
```sql
-- Find indexes that are never used
SELECT
    schemaname,
    tablename,
    indexname
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND schemaname = 'public';
```

## N+1 Query Prevention

### 1. Using QueryOptimizer Class

```python
from app.infrastructure.database.optimization import query_optimizer

# Get customers with message counts (prevents N+1)
customers = await query_optimizer.get_customers_with_messages_optimized(
    session=session,
    restaurant_id=restaurant_id,
    limit=100,
    include_message_count=True
)

# Each customer object now has ._message_count attribute
for customer in customers:
    print(f"{customer.name}: {customer._message_count} messages")
```

### 2. Conversation History Optimization

```python
# Get customer with full conversation history in 2 queries total
customer = await query_optimizer.get_customer_with_full_conversation_history(
    session=session,
    customer_id=customer_id,
    message_limit=50
)

# Messages are already loaded and sorted
for message in customer.whatsapp_messages:
    print(f"{message.direction}: {message.content}")
```

### 3. Analytics Optimization

```python
# Get comprehensive analytics in minimal queries
analytics = await query_optimizer.get_customer_analytics_optimized(
    session=session,
    restaurant_id=restaurant_id,
    date_range_days=30
)

# Returns complete analytics data structure
print(f"Total customers: {analytics['total_customers']}")
print(f"Response rate: {analytics['response_rate']}%")
```

## Connection Pool Configuration

### 1. Production Settings

```python
# Configured automatically in QueryOptimizer.configure_connection_pool()
PRODUCTION_POOL_CONFIG = {
    'pool_size': 20,           # Base number of connections
    'max_overflow': 30,        # Additional connections when needed
    'pool_timeout': 30,        # Seconds to wait for connection
    'pool_recycle': 3600,      # Recycle connections every hour
}
```

### 2. Development Settings

```python
DEVELOPMENT_POOL_CONFIG = {
    'pool_size': 5,
    'max_overflow': 10,
    'pool_timeout': 10,
    'pool_recycle': 1800,      # 30 minutes
}
```

### 3. Monitoring Pool Health

```python
from app.infrastructure.database.optimization import query_optimizer

# Check pool status
pool = engine.pool
print(f"Pool size: {pool.size()}")
print(f"Checked out: {pool.checkedout()}")
print(f"Checked in: {pool.checkedin()}")
```

## Performance Monitoring

### 1. Query Performance Tracking

The `QueryOptimizer` automatically tracks query performance:

```python
# Queries are automatically monitored
async with query_optimizer.track_query_performance("custom_operation"):
    result = await session.execute(complex_query)
```

### 2. Getting Performance Reports

```python
# Generate performance report
report = query_optimizer.get_query_performance_report()

print(f"Total queries monitored: {report['total_queries_monitored']}")
print(f"Slow queries: {report['slow_queries_count']}")

# Top slow queries
for query in report['top_slow_queries']:
    print(f"Query: {query['query_preview'][:100]}...")
    print(f"Avg duration: {query['avg_duration_ms']}ms")
```

### 3. Slow Query Configuration

```python
# Configure in settings
SLOW_QUERY_THRESHOLD_MS = 500  # Log queries slower than 500ms

# Adjust threshold for different environments
if settings.app.ENVIRONMENT == "production":
    SLOW_QUERY_THRESHOLD_MS = 100  # Stricter in production
```

## Best Practices

### 1. Query Design

#### Use Specific Columns
```python
# Good: Select only needed columns
select(Customer.id, Customer.name, Customer.phone_number)

# Avoid: Select all columns when not needed
select(Customer)  # Only use when you need all columns
```

#### Limit Result Sets
```python
# Always use limits for potentially large datasets
select(Customer).where(Customer.restaurant_id == restaurant_id).limit(100)
```

#### Use Filters Early
```python
# Good: Filter before joining
select(Customer).where(Customer.is_deleted == False).options(selectinload(Customer.messages))

# Better: Use partial indexes to make this even faster
```

### 2. Relationship Loading

#### Choose Appropriate Loading Strategy
- **selectinload**: Best for one-to-many relationships with many records
- **joinedload**: Best for one-to-one or small one-to-many relationships
- **subqueryload**: Alternative to selectinload, can be better in some cases

#### Load Related Data in Advance
```python
# Good: Load everything needed upfront
customers = await session.execute(
    select(Customer)
    .options(
        selectinload(Customer.whatsapp_messages),
        joinedload(Customer.restaurant),
        selectinload(Customer.ai_interactions)
    )
    .where(Customer.restaurant_id == restaurant_id)
)
```

### 3. Bulk Operations

#### Use Bulk Insert for Large Datasets
```python
from app.infrastructure.database.optimization import bulk_create_optimized

# Efficiently create many objects
customers_data = [
    {"customer_number": f"CUST-{i}", "phone_number": f"+123456789{i}"}
    for i in range(1000)
]

customers = await bulk_create_optimized(
    session=session,
    model_class=Customer,
    objects_data=customers_data,
    batch_size=100
)
```

### 4. Transaction Management

#### Keep Transactions Short
```python
# Good: Short, focused transactions
async with session.begin():
    customer = Customer(**customer_data)
    session.add(customer)
    # Transaction automatically committed

# Avoid: Long-running transactions that lock resources
```

## Troubleshooting

### 1. Identifying Slow Queries

#### Check Application Logs
```bash
# Look for slow query warnings
grep "Slow query detected" logs/app.log
```

#### Database Query Analysis
```sql
-- Enable query logging in PostgreSQL
ALTER SYSTEM SET log_min_duration_statement = '500ms';
SELECT pg_reload_conf();

-- View slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
WHERE mean_exec_time > 500
ORDER BY mean_exec_time DESC;
```

### 2. Connection Pool Issues

#### Pool Exhaustion
```python
# Symptoms: "QueuePool limit exceeded" errors
# Solutions:
# 1. Increase pool_size and max_overflow
# 2. Check for connection leaks
# 3. Optimize long-running queries

# Monitor pool usage
@event.listens_for(engine.pool, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    logger.info("New connection created", pool_size=engine.pool.size())
```

#### Connection Leaks
```python
# Always use proper session management
async with get_session() as session:
    # Do database work
    pass  # Session automatically closed
```

### 3. Index Problems

#### Missing Indexes
```sql
-- Find queries that might need indexes
SELECT query, calls, mean_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 100
  AND query NOT LIKE '%pg_%'
ORDER BY mean_exec_time * calls DESC;
```

#### Unused Indexes
```sql
-- Remove indexes that are never used
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;
```

### 4. Performance Testing

#### Load Testing Queries
```python
import asyncio
import time

async def test_query_performance():
    start_time = time.time()

    # Run query multiple times
    for i in range(100):
        result = await session.execute(test_query)

    duration = time.time() - start_time
    print(f"100 queries took {duration:.2f}s ({duration/100:.4f}s per query)")
```

## Migration Commands

### Apply Performance Indexes
```bash
# Run the performance optimization migration
alembic upgrade head

# Check if indexes were created
alembic current
```

### Monitor Index Creation
```sql
-- Monitor index creation progress (for large tables)
SELECT
    now() - query_start AS duration,
    query,
    state
FROM pg_stat_activity
WHERE query LIKE '%CREATE INDEX%';
```

## Conclusion

This optimization guide provides the foundation for maintaining high-performance database operations. Regular monitoring and proactive optimization are key to maintaining good performance as the application scales.

### Key Takeaways

1. **Prevent N+1 queries** using eager loading and the QueryOptimizer utilities
2. **Use appropriate indexes** for common query patterns
3. **Monitor query performance** continuously
4. **Configure connection pooling** appropriately for your environment
5. **Test performance** regularly, especially after schema changes

For questions or additional optimization needs, consult the development team or database administrator.