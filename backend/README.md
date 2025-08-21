# Restaurant AI Assistant - Backend

A comprehensive FastAPI backend system for managing AI-powered customer feedback collection and analysis for restaurants, with Arabic/English bilingual support and WhatsApp integration.

## Features

### Core Functionality
- **Multi-language Support**: Native Arabic and English support with cultural awareness
- **WhatsApp Integration**: Automated customer outreach via WhatsApp Business API
- **AI-Powered Responses**: OpenRouter integration with Claude and GPT models
- **Campaign Management**: Bulk messaging with advanced targeting and A/B testing
- **Customer Management**: Complete customer lifecycle tracking and feedback analysis
- **Real-time Analytics**: Performance metrics and business insights

### AI Agent System
- **Configurable Personas**: Create custom AI personalities with cultural sensitivity
- **Message Flow Designer**: Multi-step conversation sequences with intelligent routing
- **Sentiment Analysis**: Advanced emotion detection with Arabic language support
- **Learning System**: Continuous improvement based on interaction outcomes

### Technical Features
- **Async FastAPI**: High-performance async Python web framework
- **PostgreSQL**: Robust database with async SQLAlchemy ORM
- **FastAPI-Users**: Complete authentication and user management system
- **Docker Support**: Full containerization with docker-compose
- **Comprehensive API**: RESTful APIs with automatic OpenAPI documentation

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Environment Setup

1. **Clone and Setup**
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Database Setup**
   ```bash
   # Initialize database
   python scripts/init_db.py
   
   # Run migrations
   alembic upgrade head
   ```

4. **Start Development Server**
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Docker Deployment

1. **Development Environment**
   ```bash
   docker-compose up -d
   ```

2. **Production Environment**
   ```bash
   docker-compose -f docker-compose.yml --profile nginx up -d
   ```

## Configuration

### Required Environment Variables

```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/restaurant_ai

# Security
SECRET_KEY=your-super-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# OpenRouter AI
OPENROUTER_API_KEY=your-openrouter-api-key
PRIMARY_MODEL_ARABIC=anthropic/claude-3.5-haiku

# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=your-whatsapp-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
WHATSAPP_BUSINESS_ACCOUNT_ID=your-business-account-id
```

See `.env.example` for complete configuration options.

## API Documentation

### Endpoints Overview

- **Authentication**: `/api/v1/auth/*` - User registration, login, JWT management
- **Customers**: `/api/v1/customers/*` - Customer CRUD, feedback tracking
- **Restaurants**: `/api/v1/restaurants/*` - Restaurant management, settings
- **Campaigns**: `/api/v1/campaigns/*` - Bulk messaging, A/B testing
- **AI Agent**: `/api/v1/ai-agent/*` - Personas, message flows, interactions

### Interactive Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/api/v1/openapi.json`

## Database Schema

### Core Models

```python
# User Management
User -> Restaurant (Many-to-One)
User -> Customer (One-to-Many, created_by)

# Customer Management  
Restaurant -> Customer (One-to-Many)
Customer -> WhatsAppMessage (One-to-Many)
Customer -> AIInteraction (One-to-Many)

# Campaign System
Restaurant -> Campaign (One-to-Many)
Campaign -> CampaignRecipient (One-to-Many)
Campaign -> WhatsAppMessage (One-to-Many)

# AI Agent System
Restaurant -> AgentPersona (One-to-Many)
Restaurant -> MessageFlow (One-to-Many)
AgentPersona -> AIInteraction (One-to-Many)
MessageFlow -> AIInteraction (One-to-Many)
```

## Architecture

### Application Structure

```
app/
├── api/                    # API routes and endpoints
│   ├── auth.py            # Authentication routes
│   ├── customers.py       # Customer management
│   ├── restaurants.py     # Restaurant management
│   ├── campaigns.py       # Campaign management
│   └── ai_agent.py        # AI agent management
├── core/                   # Core application logic
│   ├── config.py          # Configuration management
│   └── logging.py         # Logging setup
├── models/                 # Database models
│   ├── user.py            # User model
│   ├── restaurant.py      # Restaurant model
│   ├── customer.py        # Customer model
│   ├── campaign.py        # Campaign models
│   ├── whatsapp.py        # WhatsApp models
│   └── ai_agent.py        # AI agent models
├── schemas/                # Pydantic schemas
│   ├── user.py            # User schemas
│   ├── customer.py        # Customer schemas
│   └── ...                # Other schemas
├── database.py            # Database connection
├── dependencies.py        # FastAPI dependencies
└── main.py               # Application entry point
```

### Key Design Principles

- **Async-First**: All I/O operations use async/await
- **Type Safety**: Comprehensive type hints with Pydantic validation
- **Security**: JWT authentication with role-based access control
- **Scalability**: Modular architecture with dependency injection
- **Observability**: Structured logging and performance monitoring

## Development

### Code Quality

```bash
# Formatting
black app/
isort app/

# Linting
flake8 app/
mypy app/

# Testing
pytest tests/
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Integration tests only
pytest tests/integration/

# Unit tests only  
pytest tests/unit/
```

## Deployment

### Production Checklist

- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Use strong `SECRET_KEY` (64+ characters)
- [ ] Configure SSL certificates
- [ ] Set up database backups
- [ ] Configure monitoring (Sentry, etc.)
- [ ] Set up log aggregation
- [ ] Configure rate limiting
- [ ] Set up health checks

### Performance Optimization

- **Database**: Connection pooling, query optimization, indexes
- **Caching**: Redis for session storage and API caching
- **CDN**: Static asset delivery
- **Load Balancing**: Multiple application instances
- **Monitoring**: Performance metrics and alerting

## Monitoring & Observability

### Health Checks

- **Application**: `GET /health`
- **Database**: Connection pool status
- **Redis**: Cache connectivity
- **External APIs**: OpenRouter, WhatsApp status

### Logging

- **Structured Logging**: JSON format for easy parsing
- **Request Tracking**: Unique request IDs
- **Performance Metrics**: Response times, database queries
- **Security Events**: Authentication, authorization failures

### Metrics

- **Business Metrics**: Customer interactions, campaign performance
- **Technical Metrics**: Response times, error rates, resource usage
- **AI Metrics**: Token usage, model performance, cost tracking

## Security

### Authentication & Authorization

- **JWT Tokens**: Secure token-based authentication
- **Role-Based Access**: Fine-grained permission system
- **Session Management**: Secure session handling with Redis
- **Password Security**: Bcrypt hashing with salt

### API Security

- **CORS Configuration**: Restricted cross-origin access
- **Rate Limiting**: Per-IP and per-user limits
- **Input Validation**: Pydantic schema validation
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries

### Data Protection

- **Encryption at Rest**: Database-level encryption
- **PII Handling**: Secure customer data management
- **GDPR Compliance**: Data retention and deletion policies
- **Audit Logging**: Complete action trail

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check database status
   docker-compose logs postgres
   
   # Test connection
   python -c "from app.database import test_connection; asyncio.run(test_connection())"
   ```

2. **Authentication Issues**
   ```bash
   # Verify JWT configuration
   python -c "from app.core.config import settings; print(settings.security.SECRET_KEY)"
   ```

3. **API Integration Failures**
   ```bash
   # Test OpenRouter connection
   curl -H "Authorization: Bearer $OPENROUTER_API_KEY" https://openrouter.ai/api/v1/models
   
   # Test WhatsApp API
   curl -H "Authorization: Bearer $WHATSAPP_ACCESS_TOKEN" \
        "https://graph.facebook.com/v18.0/$WHATSAPP_PHONE_NUMBER_ID"
   ```

### Performance Issues

- **Slow Database Queries**: Enable SQL logging, analyze query performance
- **High Memory Usage**: Check connection pool settings, enable profiling
- **API Timeouts**: Review timeout configurations, optimize async operations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run quality checks (`black`, `isort`, `flake8`, `mypy`)
5. Submit a pull request

### Development Workflow

```bash
# Setup development environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Run tests
pytest

# Start development server
python -m uvicorn app.main:app --reload
```

## License

Copyright (c) 2024 Restaurant AI Assistant. All rights reserved.

## Support

For technical support, please create an issue in the repository or contact the development team.

---

**Built with ❤️ using FastAPI, SQLAlchemy, and modern Python best practices.**