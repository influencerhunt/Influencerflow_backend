# InfluencerFlow Backend

A FastAPI backend with role-based authentication using Supabase and AI-powered negotiation capabilities.

## Features

- **FastAPI** framework for high-performance API
- **Supabase** integration for authentication and database
- **Role-based access control** (Admin, Influencer, Brand, User)
- **JWT token** authentication
- **AI-Powered Negotiation Service** using Twilio and Google Gemini
- **Voice Call Integration** for automated negotiations
- **CORS** support for frontend integration
- **Pydantic** models for request/response validation

## User Roles

- `ADMIN`: Full system access
- `INFLUENCER`: Influencer-specific features
- `BRAND`: Brand-specific features  
- `USER`: Basic user access

## Services

### Authentication Service
- User registration, login, and role-based access control
- JWT token management
- Supabase integration

### AI Negotiation Service
- AI-powered phone call negotiations for influencer marketing deals
- Twilio voice integration for inbound/outbound calls
- Google Gemini AI for intelligent conversation handling
- Optimized for Indian English speakers
- Real-time speech processing and session management

For detailed documentation, see [NEGOTIATION_SERVICE.md](./NEGOTIATION_SERVICE.md)

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
# Edit .env with your Supabase, Twilio, and Google API credentials
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

### AI Negotiation
- `POST /api/v1/negotiation/outbound-call` - Initiate negotiation call
- `GET /api/v1/negotiation/call-status/{call_sid}` - Get call status
- `POST /api/v1/negotiation/end-session` - End negotiation session
- `GET /api/v1/negotiation/sessions` - Get active sessions
- `GET /api/v1/negotiation/health` - Service health check
- Twilio webhook endpoints for voice processing

### Health
- `GET /` - Root endpoint
- `GET /health` - Health check

## Environment Variables

Required environment variables in `.env`:

```
# Supabase Configuration
SUPABASE_URL=your_supabase_url_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=postgresql://user:password@localhost:5432/influencerflow
CORS_ORIGINS=http://localhost:3000

# Twilio Configuration for AI Negotiation Service
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_NUMBER=your_twilio_phone_number_here

# Google GenAI Configuration for AI Negotiation
GOOGLE_API_KEY=your_google_genai_api_key_here
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
│   │   ├── auth.py       # Authentication endpoints
│   │   └── negotiation.py # AI negotiation endpoints
│   ├── core/             # Core configuration
│   ├── middleware/       # Authentication middleware
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas
│   │   └── negotiation.py # Negotiation service schemas
│   └── services/         # Business logic services
│       ├── supabase.py   # Supabase service
│       └── negotiation_service.py # AI negotiation service
├── main.py               # FastAPI application
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── NEGOTIATION_SERVICE.md # Detailed negotiation service docs
```

## Quick Start with AI Negotiation

1. Set up your Twilio and Google API credentials in `.env`
2. Configure Twilio webhooks to point to your deployed API
3. Test with a simple outbound call:

```python
import requests

response = requests.post("http://localhost:8000/api/v1/negotiation/outbound-call", json={
    "to_number": "+1234567890",
    "webhook_base_url": "https://your-domain.com"
})
``` 