# InfluencerFlow Backend

A FastAPI backend with role-based authentication using Supabase.

## Features

- **FastAPI** framework for high-performance API
- **Supabase** integration for authentication and database
- **Role-based access control** (Admin, Influencer, Brand, User)
- **JWT token** authentication
- **CORS** support for frontend integration
- **Pydantic** models for request/response validation

## User Roles

- `ADMIN`: Full system access
- `INFLUENCER`: Influencer-specific features
- `BRAND`: Brand-specific features  
- `USER`: Basic user access

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

4. Run the application:
```bash
python main.py
```

Or with uvicorn:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/signup` - Register new user
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/auth/me` - Get current user info
- `GET /api/v1/auth/protected` - Protected route (requires authentication)
- `GET /api/v1/auth/admin-only` - Admin-only route

### Health
- `GET /` - Root endpoint
- `GET /health` - Health check

## Environment Variables

Required environment variables in `.env`:

```
SUPABASE_URL=your_supabase_url_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=postgresql://user:password@localhost:5432/influencerflow
CORS_ORIGINS=http://localhost:3000
```

## Development

The API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
Influencerflow_backend/
├── app/
│   ├── api/              # API routes
│   ├── core/             # Core configuration
│   ├── middleware/       # Authentication middleware
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas
│   └── services/         # Business logic services
├── main.py               # FastAPI application
├── requirements.txt      # Python dependencies
└── README.md            # This file
``` 