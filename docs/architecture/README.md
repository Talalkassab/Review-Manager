# Architecture Documentation - Customer WhatsApp Agent

## Table of Contents
1. [System Overview](#system-overview)
2. [Current State Analysis](#current-state-analysis)
3. [Architecture Components](#architecture-components)
4. [Critical Issues & Technical Debt](#critical-issues--technical-debt)
5. [Recommended Architecture](#recommended-architecture)
6. [Refactoring Roadmap](#refactoring-roadmap)

## System Overview

The Customer WhatsApp Agent is a bilingual (Arabic/English) restaurant feedback management system that automates customer outreach via WhatsApp, collects feedback, performs sentiment analysis, and routes responses appropriately (positive to Google Reviews, negative to management).

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│                    Next.js 13+ (App Router)                 │
│                  TypeScript + shadcn/ui + RTL               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway                            │
│                    FastAPI + Pydantic v2                    │
│                  JWT Authentication (FastAPI-Users)         │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
┌─────────────────────────┐  ┌─────────────────────────────┐
│    Database Layer       │  │    External Services        │
│  SQLite + SQLAlchemy    │  │  - Twilio WhatsApp API      │
│     (Async ORM)         │  │  - OpenRouter AI            │
│                         │  │  - Google Maps API          │
└─────────────────────────┘  └─────────────────────────────┘
```

## Current State Analysis

### Directory Structure
```
Customer-Whatsapp-agent/
├── frontend/               # Next.js application
│   ├── app/               # App router pages
│   ├── components/        # React components
│   ├── lib/              # Utilities and API clients
│   └── hooks/            # Custom React hooks
├── backend/              # PRIMARY FastAPI backend
│   ├── app/             # Main application
│   ├── models/          # SQLAlchemy models
│   ├── routes/          # API endpoints
│   └── services/        # Business logic
├── backend-python/       # DUPLICATE backend (ISSUE!)
└── product-development/  # Documentation
```

## Architecture Components

### Frontend Layer

**Technology Stack:**
- Framework: Next.js 13+ with App Router
- Language: TypeScript
- UI Library: shadcn/ui (Radix UI primitives)
- Styling: Tailwind CSS with RTL support
- State Management: React Context API
- API Communication: Custom fetch wrapper with interceptors

**Key Components:**
- Authentication context and guards
- Bilingual (Arabic/English) support with RTL
- Dashboard with real-time metrics
- Customer management interface
- Analytics and reporting views

### Backend Layer

**Technology Stack:**
- Framework: FastAPI (Python 3.8+)
- Database ORM: SQLAlchemy 2.0 (async)
- Authentication: FastAPI-Users with JWT
- Validation: Pydantic v2
- API Documentation: Auto-generated OpenAPI/Swagger

**Core Services:**
- Customer management (CRUD operations)
- WhatsApp integration (Twilio)
- AI sentiment analysis (OpenRouter)
- Authentication & authorization
- Analytics aggregation

### Database Layer

**Technology:**
- Database: SQLite (development) / PostgreSQL (production-ready)
- ORM: SQLAlchemy with async support
- Migrations: Alembic

**Schema Overview:**
- Users (authentication, roles)
- Restaurants (multi-tenant support)
- Customers (profiles, contact info)
- Feedback (responses, sentiment)
- Analytics (aggregated metrics)

### External Integrations

1. **Twilio WhatsApp Business API**
   - Message templates
   - Webhook handling
   - Status tracking

2. **OpenRouter AI Integration**
   - Multiple model support (Claude, GPT-4, Llama)
   - Sentiment analysis
   - Language detection

3. **Google Maps/Business API**
   - Review link generation
   - Location verification

## Critical Issues & Technical Debt

### 🚨 Priority 1: Critical Issues

1. **Duplicate Backend Implementation**
   - Two complete backend folders (`backend/` and `backend-python/`)
   - Inconsistent model schemas between implementations
   - Maintenance nightmare and data inconsistency risk
   - **Impact:** High - Causes confusion and bugs
   - **Solution:** Consolidate to single backend

2. **Inconsistent Data Models**
   - Multiple Customer model definitions with different fields
   - No single source of truth for database schema
   - **Impact:** High - Data integrity issues
   - **Solution:** Standardize on single schema definition

### ⚠️ Priority 2: Code Quality Issues

1. **Code Duplication**
   - Duplicate webhook handlers (`webhook.py`, `webhook_old.py`, `webhook_stable.py`)
   - Repeated business logic across files
   - **Impact:** Medium - Increases maintenance burden
   - **Solution:** Extract shared logic to service layer

2. **Poor Separation of Concerns**
   - Business logic mixed with route handlers
   - Database queries in API endpoints
   - **Impact:** Medium - Hard to test and maintain
   - **Solution:** Implement proper service layer pattern

3. **Inconsistent Error Handling**
   - Mix of try/catch patterns
   - Inconsistent error responses
   - **Impact:** Medium - Poor debugging experience
   - **Solution:** Centralized error handling middleware

### 📝 Priority 3: Best Practices Violations

1. **Missing Configuration Management**
   - Hardcoded values throughout codebase
   - No environment-based configuration
   - **Solution:** Implement proper config management with Pydantic Settings

2. **Lack of Testing**
   - No unit tests found
   - No integration tests
   - **Solution:** Add comprehensive test suite

3. **Missing API Versioning**
   - No version prefix in API routes
   - **Solution:** Implement API versioning strategy

4. **Insufficient Logging**
   - Limited logging for debugging
   - **Solution:** Implement structured logging

## Recommended Architecture

### Clean Architecture Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│                  (Frontend + API Routes)                    │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                       │
│                    (Use Cases/Services)                     │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Domain Layer                           │
│                   (Business Entities)                       │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                      │
│              (Database, External APIs, etc.)                │
└─────────────────────────────────────────────────────────────┘
```

### Proposed Backend Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/       # Route handlers only
│   │   │   └── dependencies/    # Dependency injection
│   ├── core/
│   │   ├── config.py           # Configuration management
│   │   ├── security.py         # Auth utilities
│   │   └── exceptions.py       # Custom exceptions
│   ├── domain/
│   │   ├── entities/           # Business entities
│   │   └── value_objects/      # Domain value objects
│   ├── services/
│   │   ├── customer_service.py
│   │   ├── whatsapp_service.py
│   │   ├── ai_service.py
│   │   └── analytics_service.py
│   ├── infrastructure/
│   │   ├── database/
│   │   │   ├── models/         # SQLAlchemy models
│   │   │   └── repositories/   # Data access layer
│   │   └── external/
│   │       ├── twilio/         # WhatsApp integration
│   │       ├── openrouter/     # AI integration
│   │       └── google/         # Maps integration
│   └── main.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── alembic/                    # Database migrations
```

## Refactoring Roadmap

### Phase 1: Critical Fixes (Week 1-2)

1. **Consolidate Backend Implementation**
   - Remove `backend-python/` directory
   - Migrate any unique features to main `backend/`
   - Standardize on single implementation

2. **Standardize Data Models**
   - Create canonical model definitions
   - Update all references to use standard models
   - Add database migrations

3. **Remove Duplicate Code**
   - Consolidate webhook handlers
   - Extract shared logic to services
   - Remove redundant files

### Phase 2: Architecture Improvements (Week 3-4)

1. **Implement Service Layer**
   - Extract business logic from routes
   - Create dedicated service classes
   - Implement dependency injection

2. **Add Configuration Management**
   - Create settings module with Pydantic
   - Move hardcoded values to config
   - Support environment-based configuration

3. **Improve Error Handling**
   - Create custom exception classes
   - Implement global error handler
   - Standardize error responses

### Phase 3: Quality Improvements (Week 5-6)

1. **Add Testing**
   - Unit tests for services
   - Integration tests for API endpoints
   - E2E tests for critical flows

2. **Implement Logging**
   - Add structured logging
   - Include request/response logging
   - Add performance metrics

3. **API Versioning**
   - Add `/api/v1` prefix
   - Document versioning strategy
   - Plan deprecation policy

### Phase 4: Performance & Scalability (Week 7-8)

1. **Database Optimization**
   - Add proper indexes
   - Implement connection pooling
   - Add query optimization

2. **Caching Strategy**
   - Implement Redis for caching
   - Cache frequently accessed data
   - Add cache invalidation logic

3. **Async Improvements**
   - Ensure all I/O operations are async
   - Implement background task processing
   - Add task queue for heavy operations

## Development Guidelines

### Code Standards

1. **Python Style**
   - Follow PEP 8
   - Use type hints everywhere
   - Document all public APIs

2. **TypeScript Style**
   - Use strict mode
   - Define interfaces for all data structures
   - Avoid `any` type

3. **Git Workflow**
   - Feature branches for all changes
   - Meaningful commit messages
   - PR reviews required

### Testing Requirements

- Minimum 80% code coverage
- All new features require tests
- Integration tests for external services
- Performance tests for critical paths

### Documentation Standards

- API documentation via OpenAPI
- Code comments for complex logic
- README files for each module
- Architecture decision records (ADRs)

## Monitoring & Observability

### Recommended Stack

1. **Application Monitoring**
   - Sentry for error tracking
   - Prometheus for metrics
   - Grafana for visualization

2. **Logging**
   - Structured JSON logging
   - Centralized log aggregation
   - Log levels: DEBUG, INFO, WARNING, ERROR

3. **Performance Monitoring**
   - API response time tracking
   - Database query performance
   - External service latency

## Security Considerations

1. **Authentication & Authorization**
   - JWT with refresh tokens
   - Role-based access control (RBAC)
   - API key management for services

2. **Data Protection**
   - Encrypt sensitive data at rest
   - Use HTTPS everywhere
   - Implement rate limiting

3. **Compliance**
   - GDPR compliance for EU customers
   - WhatsApp Business API compliance
   - Data retention policies

## Deployment Architecture

### Recommended Setup

```
┌─────────────────────────────────────────────────────────────┐
│                      Load Balancer                          │
│                        (Nginx)                              │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
┌─────────────────────────┐  ┌─────────────────────────────┐
│    Frontend Server      │  │     API Server              │
│    (Next.js on Vercel)  │  │  (FastAPI on Railway)       │
└─────────────────────────┘  └─────────────────────────────┘
                                        │
                              ┌─────────┴─────────┐
                              ▼                   ▼
                    ┌─────────────────┐  ┌─────────────────┐
                    │   PostgreSQL     │  │     Redis       │
                    │   (Primary DB)   │  │    (Cache)      │
                    └─────────────────┘  └─────────────────┘
```

### Environment Configuration

- **Development:** Local SQLite, mock external services
- **Staging:** PostgreSQL, test API keys
- **Production:** PostgreSQL with replicas, production API keys

## Conclusion

The Customer WhatsApp Agent system has a solid foundation but requires significant refactoring to address technical debt and improve maintainability. The priority should be:

1. **Immediate:** Fix critical issues (duplicate backend, inconsistent models)
2. **Short-term:** Improve architecture (service layer, configuration)
3. **Medium-term:** Enhance quality (testing, logging, monitoring)
4. **Long-term:** Optimize performance and scalability

Following this roadmap will result in a more maintainable, scalable, and reliable system that can support future growth and feature development.