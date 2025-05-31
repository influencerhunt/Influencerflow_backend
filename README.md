# InfluencerFlow Backend - AI-Powered Influencer Search

A comprehensive backend system for searching and discovering social media influencers using AI-powered natural language processing and multi-platform scraping.

## 🚀 Features

- **AI-Powered Search**: Natural language query parsing using Google Gemini AI
- **Multi-Platform Support**: Instagram, YouTube, TikTok, Twitter, LinkedIn, Facebook
- **Hybrid Search**: Combines on-platform (database) and external (web scraping) results
- **Smart Filtering**: Follower count, engagement rate, price range, location, niche
- **Real-time Discovery**: Finds influencers not yet on your platform
- **RESTful API**: FastAPI-based with comprehensive endpoints
- **Role-based Authentication**: Admin, Influencer, Brand, User roles

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │────│   FastAPI API    │────│   AI Parser     │
│   (React/Vue)   │    │                  │    │   (Gemini)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                    ┌───────────┼───────────┐
                    │                       │
            ┌───────▼────────┐    ┌────────▼────────┐
            │   Database     │    │  External APIs  │
            │   (Supabase)   │    │  (Serper/Web)   │
            └────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

- Python 3.8+
- Supabase account (for database)
- Google AI Studio account (for Gemini API)
- Serper.dev account (for web search)

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