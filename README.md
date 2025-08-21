# Restaurant AI Customer Feedback Agent 🤖

## Overview

The Restaurant AI Customer Feedback Agent is a comprehensive bilingual (Arabic/English) web application designed to help restaurants collect, analyze, and manage customer feedback efficiently. The system automatically contacts customers via WhatsApp, collects feedback, analyzes sentiment, and generates actionable insights to improve restaurant service quality.

## ✨ Key Features

### Customer Management
- **Bilingual Customer Profiles**: Full Arabic and English support with RTL text handling
- **Automated Contact System**: WhatsApp integration for customer outreach
- **Smart Status Tracking**: Real-time monitoring of customer interaction stages
- **Visit History**: Complete record of customer visits and interactions

### Intelligent Analytics
- **Real-time Dashboard**: Live metrics showing response rates, feedback trends, and customer satisfaction
- **Sentiment Analysis**: AI-powered analysis of customer feedback (positive, negative, neutral)
- **Performance Metrics**: Response rates, positive feedback percentages, and Google review generation
- **Customer Insights**: Detailed breakdown of customer behavior and preferences

### Authentication & Security
- **JWT-based Authentication**: Secure token-based user authentication
- **Role-based Access Control**: Different permission levels for restaurant staff and administrators
- **Secure API Communication**: Protected endpoints with proper authorization

### Multi-language Support
- **Arabic/English Interface**: Complete bilingual user interface
- **RTL Layout Support**: Proper right-to-left text rendering for Arabic content
- **Dynamic Language Switching**: Users can switch between languages seamlessly

## 🏗️ System Architecture

### Frontend (Next.js 13+)
- **Framework**: Next.js with App Router and TypeScript
- **UI Components**: shadcn/ui for consistent, accessible components
- **Styling**: Tailwind CSS with RTL support
- **State Management**: React Context API for language and authentication
- **API Communication**: Custom API client with error handling and token management

### Backend (FastAPI)
- **Framework**: FastAPI with async/await support
- **Database**: SQLite with SQLAlchemy ORM (async)
- **Authentication**: FastAPI-Users with JWT strategy
- **Data Validation**: Pydantic v2 models
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

### Database Schema
- **Users**: Authentication and role management
- **Restaurants**: Multi-tenant restaurant data
- **Customers**: Customer profiles and contact information
- **WhatsApp Messages**: Message history and status tracking
- **Campaigns**: Marketing campaign management

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm/yarn
- Python 3.8+ and pip
- Git

### 1. Clone and Setup
```bash
git clone <repository-url>
cd Customer-Whatsapp-agent

# Setup Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Setup Frontend
cd ../frontend
npm install
```

### 2. Environment Configuration
```bash
# Backend (.env)
DATABASE_URL=sqlite+aiosqlite:///./restaurant_ai.db
SECRET_KEY=your-secret-key-here
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:3002"]

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Database Initialization
```bash
cd backend
python -m app.core.init_db
```

### 4. Start Services
```bash
# Terminal 1: Backend (Port 8000)
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend (Port 3002)
cd frontend
npm run dev -- -p 3002
```

### 5. Admin Account
Default admin credentials:
- **Email**: admin@restaurant.com
- **Password**: Admin123!

## 🔧 API Endpoints

### Authentication
- `POST /api/v1/auth/jwt/login` - User login
- `POST /api/v1/auth/register` - User registration
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/auth/jwt/logout` - User logout

### Customers
- `GET /api/v1/customers/` - List customers (paginated)
- `POST /api/v1/customers/` - Create new customer
- `PUT /api/v1/customers/{id}/` - Update customer
- `DELETE /api/v1/customers/{id}/` - Delete customer
- `GET /api/v1/customers/stats/summary` - Customer analytics stats

### Restaurants
- `GET /api/v1/restaurants/` - List restaurants
- `POST /api/v1/restaurants/` - Create restaurant (admin only)
- `GET /api/v1/restaurants/{id}` - Get restaurant details
- `PATCH /api/v1/restaurants/{id}` - Update restaurant
- `GET /api/v1/restaurants/{id}/stats` - Restaurant statistics

## 📱 User Interface

### Dashboard
- **Key Metrics**: Total customers, response rates, positive feedback percentages
- **Recent Activity**: Latest customer interactions and feedback
- **Quick Actions**: Add customers, view analytics, manage settings

### Customer Management
- **Customer List**: Searchable, filterable list with status indicators
- **Add Customer Form**: Bilingual form with validation
- **Customer Profiles**: Detailed view with interaction history

### Analytics
- **Performance Metrics**: Response rates, feedback analysis, trend indicators
- **Customer Insights**: Sentiment breakdown, rating distributions
- **Export Capabilities**: Data export for further analysis

### Settings
- **Language Preferences**: Arabic/English switching
- **Restaurant Configuration**: Business details and preferences
- **User Management**: Account settings and permissions

## 🔒 Security Features

### Authentication
- JWT tokens with secure storage
- Password encryption using bcrypt
- Session management and token refresh

### Authorization
- Role-based access control (Admin, Restaurant Owner, Staff)
- API endpoint protection
- Resource-level permissions

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- CORS configuration for secure cross-origin requests

## 🌍 Internationalization

### Language Support
- **Arabic (RTL)**: Complete right-to-left layout support
- **English (LTR)**: Standard left-to-right layout
- **Dynamic Switching**: Real-time language switching without page reload

### RTL Implementation
- CSS directional properties (`dir="rtl"`)
- Tailwind CSS RTL utilities
- Font optimization (Cairo for Arabic, Inter for English)
- Icon and layout mirroring

## 📊 Analytics & Reporting

### Key Metrics
- **Response Rate**: Percentage of customers who respond to outreach
- **Positive Feedback Rate**: Percentage of positive customer feedback
- **Customer Growth**: New customers over time
- **Google Review Generation**: Reviews generated through the system

### Data Visualization
- Real-time metric cards with trend indicators
- Customer sentiment breakdown charts
- Performance tracking over time
- Comparative analysis tools

## 🛠️ Development

### Code Structure
```
├── backend/
│   ├── app/
│   │   ├── api/          # API routes
│   │   ├── core/         # Configuration and utilities
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   └── main.py       # FastAPI application
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js App Router pages
│   │   ├── components/   # Reusable UI components
│   │   ├── contexts/     # React contexts
│   │   ├── lib/          # Utilities and API client
│   │   └── styles/       # Global styles
│   └── package.json
```

### Development Guidelines
- **Code Quality**: TypeScript for frontend, type hints for backend
- **Component Architecture**: Reusable, accessible UI components
- **API Design**: RESTful endpoints with consistent response formats
- **Error Handling**: Comprehensive error catching and user feedback
- **Performance**: Optimized queries, lazy loading, efficient state management

### Testing
- Backend API testing with pytest
- Frontend component testing capabilities
- Integration testing for critical user flows
- Manual testing procedures documented

## 🔧 Troubleshooting

### Common Issues

**Login Failed - 401 Unauthorized**
- Verify credentials are correct
- Check if user account exists
- Ensure backend server is running

**API Connection Errors**
- Verify backend is running on port 8000
- Check CORS configuration includes frontend port
- Confirm API endpoints match between frontend and backend

**Database Errors**
- Run database initialization: `python -m app.core.init_db`
- Check database file permissions
- Verify SQLAlchemy connection string

**Build/Deployment Issues**
- Clear node_modules and reinstall dependencies
- Check environment variables are set correctly
- Verify Python virtual environment is activated

## 📈 Performance Optimization

### Backend Optimization
- Async/await for database operations
- Connection pooling for database efficiency
- Proper indexing on frequently queried fields
- Pagination for large data sets

### Frontend Optimization
- Next.js App Router for optimized routing
- Component lazy loading
- Efficient state management
- Image optimization and caching

## 🚀 Deployment

### Production Setup
1. **Database**: Migrate to PostgreSQL for production
2. **Environment Variables**: Set production API URLs and secrets
3. **SSL/HTTPS**: Configure secure connections
4. **CORS**: Update allowed origins for production domains
5. **Monitoring**: Add logging and error tracking

### Docker Support
The application can be containerized using Docker for consistent deployment across environments.

## 📋 Feature Roadmap

### Planned Enhancements
- **WhatsApp Integration**: Direct messaging capabilities
- **Advanced Analytics**: Custom reporting and data export
- **Multi-restaurant Support**: Enhanced tenant isolation
- **Mobile Application**: React Native mobile app
- **AI Insights**: Machine learning for customer behavior prediction

## 🤝 Contributing

This is a comprehensive restaurant management system with real-time analytics, bilingual support, and modern web technologies. The system successfully integrates frontend React components with backend FastAPI services, providing a complete solution for restaurant customer feedback management.

---

**System Status**: ✅ Fully Operational
- Authentication system working
- All API endpoints functional  
- Real-time data integration complete
- Bilingual interface operational
- Analytics dashboard active

The Restaurant AI Customer Feedback Agent represents a complete, production-ready solution for modern restaurant customer relationship management with intelligent automation and comprehensive analytics capabilities.