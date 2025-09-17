# Support System API

Modern support ticket system built with FastAPI, PostgreSQL, and MongoDB. This is a technical assessment project demonstrating enterprise-level architecture patterns.

## Architecture

- **Backend**: FastAPI with async/await
- **Primary Database**: PostgreSQL with Tortoise ORM
- **Logging Database**: MongoDB with Motor driver
- **Authentication**: JWT tokens with role-based permissions
- **Migration**: Aerich for database schema management
- **Containerization**: Docker Compose for development

## Features

### Core Functionality
- User registration and JWT authentication
- Three-tier role system (USER, STAFF, ADMIN)
- Support ticket CRUD operations
- Staff assignment and ticket status management
- Request action logging in MongoDB

### Security & Permissions
- Granular permission system
- Password strength validation
- Role-based access control
- Secure credential management

### Admin Features
- User and staff management
- System statistics and analytics
- CSV export functionality
- Request action audit logs
- Staff workload analysis

### Data Models
- **User**: Includes INN, phone, personal details with prefixed IDs (USR000001)
- **Request**: Support tickets with staff assignment and comments (REQ000001)
- **Audit Logs**: Complete action tracking in MongoDB

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Environment variables configured

### Environment Setup

Create `.env` file:
```env
DATABASE_URL=postgres://postgres:postgres@postgres:5432/support_system
MONGODB_URL=mongodb://mongodb:27017
MONGODB_DATABASE=app_logs
SECRET_KEY=your-secure-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DEBUG=True

# Default users (created on first startup)
INITIAL_ADMIN_EMAIL=admin@company.com
INITIAL_ADMIN_PASSWORD=SecureAdminPass123!
INITIAL_STAFF_EMAIL=staff@company.com
INITIAL_STAFF_PASSWORD=SecureStaffPass123!
INITIAL_USER_EMAIL=user@company.com
INITIAL_USER_PASSWORD=SecureUserPass123!
```

### Running the Application

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

The API will be available at `http://localhost:8000`

- **API Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

## API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User authentication
- `GET /auth/profile` - Get user profile
- `PUT /auth/profile` - Update profile
- `POST /auth/change-password` - Change password

### User Requests
- `POST /user_request/` - Create support request
- `GET /user_request/my` - Get user's own requests
- `GET /user_request/{id}` - Get specific request
- `PUT /user_request/{id}` - Update request
- `DELETE /user_request/{id}` - Delete request

### Staff Operations
- `GET /staff/requests` - Get assigned requests
- `PUT /staff/requests/{id}/status` - Update request status
- `POST /staff/requests/{id}/assign` - Assign request to staff

### Admin Functions
- `GET /admin/statistics` - System statistics
- `GET /admin/users` - List all users
- `GET /admin/staff` - List all staff
- `DELETE /admin/users/{id}` - Delete user
- `GET /admin/requests/export` - Export requests to CSV

### Logging & Monitoring
- `GET /admin/logs/api-logs` - API request logs
- `GET /admin/logs/request-actions` - Request action logs
- `GET /admin/logs/stats` - Logging statistics

## Development

### Database Migrations

```bash
# Generate migration
docker-compose exec api aerich init-db

# Create new migration
docker-compose exec api aerich migrate

# Apply migrations
docker-compose exec api aerich upgrade
```

### Project Structure

```
src/
├── api/
│   ├── auth/              # JWT and password management
│   ├── routers/           # API endpoints
│   ├── schemas/           # Pydantic models
│   └── services/          # Business logic
├── core/
│   ├── config.py          # Configuration settings
│   ├── database.py        # Database manager
│   ├── dependencies.py    # FastAPI dependencies
│   └── security.py        # Security utilities
├── middleware/            # Custom middleware
├── models/                # Tortoise ORM models
├── utils/                 # Helper utilities
├── bootstrap_initial.py   # Initial user creation
├── enums.py              # Application enums
└── main.py               # FastAPI application entry point
```

## Technical Highlights

### Architecture Patterns
- **Dependency Injection**: Clean separation of concerns
- **Repository Pattern**: Database abstraction
- **Middleware Pipeline**: Request/response processing
- **Service Layer**: Business logic encapsulation

### Database Design
- **Dual Database Strategy**: PostgreSQL for transactional data, MongoDB for logs
- **Model Prefixes**: Human-readable IDs (USR000001, REQ000001)
- **Audit Trail**: Complete action logging with user context

### Security Implementation
- **JWT with Refresh Tokens**: Secure authentication
- **Permission-Based Authorization**: Granular access control
- **Password Security**: Bcrypt hashing with strength validation
- **Request Validation**: Comprehensive input sanitization

### Monitoring & Observability
- **Health Checks**: Database connectivity monitoring
- **Action Logging**: Complete audit trail in MongoDB
- **Performance Tracking**: Request timing and metrics
- **Error Handling**: Structured error responses

## Testing

Default test users are created automatically:

- **Admin**: admin@company.com / SecureAdminPass123!
- **Staff**: staff@company.com / SecureStaffPass123!
- **User**: user@company.com / SecureUserPass123!

## Production Considerations

- Set `DEBUG=False` in production
- Use strong, unique `SECRET_KEY`
- Configure proper database credentials
- Set up SSL/TLS termination
- Implement rate limiting
- Configure log rotation for MongoDB

## Technology Stack

- **FastAPI 0.104.1** - Modern Python web framework
- **Tortoise ORM 0.20.0** - Async ORM for PostgreSQL
- **Motor 3.6.0** - Async MongoDB driver
- **PyJWT 2.8.0** - JWT token handling
- **Passlib 1.7.4** - Password hashing
- **Pydantic 2.5.0** - Data validation
- **Uvicorn 0.24.0** - ASGI server