# InfluencerFlow API Documentation

Complete API documentation for the InfluencerFlow backend platform with authentication and AI-powered voice call capabilities.

## 📋 **Table of Contents**

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Environment Setup](#environment-setup)
4. [API Endpoints](#api-endpoints)
   - [Core Routes](#core-routes)
   - [Authentication Routes](#authentication-routes)
   - [Voice Call Routes](#voice-call-routes)
5. [Usage Examples](#usage-examples)
6. [Development Setup](#development-setup)
7. [Architecture](#architecture)
8. [Troubleshooting](#troubleshooting)

## 🎯 **Overview**

InfluencerFlow API is a FastAPI-based backend that provides:

- **Role-based Authentication** with Supabase integration
- **AI-Powered Voice Calls** using Twilio and Google Gemini
- **RESTful API Design** with comprehensive error handling
- **MVP-Friendly Architecture** that runs in mock mode without dependencies

### Features
- ✅ User authentication and authorization
- ✅ Real-time voice call processing
- ✅ AI-powered conversation handling
- ✅ Session management
- ✅ Webhook integration
- ✅ Mock mode for development

## 🚀 **Quick Start**

### 1. Start the Server
```bash
cd Influencerflow_backend
python main.py
```

### 2. Access the API
- **Base URL:** `http://localhost:8000`
- **API Documentation:** `http://localhost:8000/docs`
- **Health Check:** `http://localhost:8000/health`

### 3. Test with ngrok (for Twilio webhooks)
```bash
# Terminal 1: Start API
cd Influencerflow_backend && python main.py

# Terminal 2: Start ngrok
ngrok http 8000

# Use the ngrok HTTPS URL for webhook_base_url in API calls
```

## ⚙️ **Environment Setup**

### Minimal Setup (MVP Mode)
The API runs without any external dependencies for testing:

```bash
# Only core dependencies needed
pip install fastapi uvicorn python-multipart python-decouple
python main.py
```

### Full Setup (Production Mode)
For full functionality with real services:

```bash
# Install all dependencies
pip install fastapi uvicorn python-multipart python-decouple supabase twilio google-generativeai

# Create .env file
cp .env.example .env
# Fill in your actual API keys
```

### Environment Variables

```env
# Core Configuration
CORS_ORIGINS=http://localhost:3000

# Supabase Configuration (Optional for MVP)
SUPABASE_URL=your_supabase_url_here
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=postgresql://user:password@localhost:5432/influencerflow

# Twilio Configuration (Optional for MVP)
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_NUMBER=your_twilio_phone_number_here

# Google GenAI Configuration (Optional for MVP)
GOOGLE_API_KEY=your_google_genai_api_key_here
```

## 📡 **API Endpoints**

### Core Routes

#### `GET /`
**Root endpoint** - API information and status

```bash
curl -X GET "http://localhost:8000/"
```

**Response:**
```json
{
  "message": "Welcome to InfluencerFlow API",
  "version": "1.0.0",
  "status": "active",
  "features": ["basic-api", "voice-call-mock"],
  "note": "Running in MVP mode - some features may be mocked"
}
```

#### `GET /health`
**Health check** - Service status

```bash
curl -X GET "http://localhost:8000/health"
```

**Response:**
```json
{
  "status": "healthy",
  "mode": "mvp"
}
```

### Authentication Routes

Base path: `/api/v1/auth`

#### `POST /api/v1/auth/signup`
**User registration** - Create new user account

```bash
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "role": "INFLUENCER"
  }'
```

#### `POST /api/v1/auth/login`
**User login** - Authenticate and get access token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

#### `POST /api/v1/auth/logout`
**User logout** - Invalidate access token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/logout" \
  -H "Authorization: Bearer your_access_token"
```

#### `GET /api/v1/auth/me`
**Get current user** - Retrieve authenticated user information

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer your_access_token"
```

#### `GET /api/v1/auth/protected`
**Protected route** - Test authentication

```bash
curl -X GET "http://localhost:8000/api/v1/auth/protected" \
  -H "Authorization: Bearer your_access_token"
```

#### `GET /api/v1/auth/admin-only`
**Admin route** - Admin-only access

```bash
curl -X GET "http://localhost:8000/api/v1/auth/admin-only" \
  -H "Authorization: Bearer your_admin_access_token"
```

### Voice Call Routes

Base path: `/api/v1/voice-call`

#### `GET /api/v1/voice-call/health`
**Voice service health check**

```bash
curl -X GET "http://localhost:8000/api/v1/voice-call/health"
```

**Response:**
```json
{
  "success": true,
  "message": "Voice call service is healthy",
  "data": {
    "service": "voice-call",
    "status": "healthy",
    "gemini_client": "mock",
    "twilio_client": "mock",
    "mode": "mvp"
  }
}
```

#### `POST /api/v1/voice-call/outbound-call`
**Initiate outbound call**

```bash
curl -X POST "http://localhost:8000/api/v1/voice-call/outbound-call" \
  -H "Content-Type: application/json" \
  -d '{
    "to_number": "+1234567890",
    "webhook_base_url": "https://your-ngrok-url.ngrok.io"
  }'
```

**Response:**
```json
{
  "success": true,
  "call_sid": "MOCK_CALL_SID_+1234567890",
  "message": "Call initiated successfully to +1234567890"
}
```

#### `GET /api/v1/voice-call/call-status/{call_sid}`
**Get call status**

```bash
curl -X GET "http://localhost:8000/api/v1/voice-call/call-status/MOCK_CALL_SID_+1234567890"
```

**Response:**
```json
{
  "sid": "MOCK_CALL_SID_+1234567890",
  "status": "mock-completed",
  "duration": "120",
  "direction": "outbound-api",
  "from_number": "+1234567890",
  "to_number": "+1234567890"
}
```

#### `GET /api/v1/voice-call/sessions`
**Get active voice call sessions**

```bash
curl -X GET "http://localhost:8000/api/v1/voice-call/sessions"
```

**Response:**
```json
{
  "success": true,
  "message": "Found 2 active sessions",
  "data": {
    "active_sessions": ["CA123", "CA456"],
    "count": 2
  }
}
```

#### `POST /api/v1/voice-call/end-session`
**End voice call session**

```bash
curl -X POST "http://localhost:8000/api/v1/voice-call/end-session" \
  -H "Content-Type: application/json" \
  -d '{
    "call_sid": "MOCK_CALL_SID_+1234567890"
  }'
```

#### Twilio Webhook Endpoints

These endpoints are called by Twilio automatically:

- `POST /api/v1/voice-call/voice` - Incoming voice calls
- `POST /api/v1/voice-call/gather` - Speech input processing  
- `POST /api/v1/voice-call/partial` - Partial speech results

**Twilio Configuration:**
- Voice URL: `https://your-ngrok-url.ngrok.io/api/v1/voice-call/voice`

## 💡 **Usage Examples**

### Complete Python Example

```python
import requests
import time

# Configuration
BASE_URL = "http://localhost:8000"
NGROK_URL = "https://your-ngrok-url.ngrok.io"  # Replace with your ngrok URL

def test_api_complete():
    """Complete API testing workflow"""
    
    print("🚀 Testing InfluencerFlow API")
    
    # 1. Test main health
    print("\n1️⃣ Testing main health...")
    health = requests.get(f"{BASE_URL}/health")
    print(f"Main Health: {health.json()}")
    
    # 2. Test voice call health
    print("\n2️⃣ Testing voice call health...")
    voice_health = requests.get(f"{BASE_URL}/api/v1/voice-call/health")
    print(f"Voice Health: {voice_health.json()}")
    
    # 3. Initiate outbound call
    print("\n3️⃣ Initiating outbound call...")
    call_response = requests.post(f"{BASE_URL}/api/v1/voice-call/outbound-call", json={
        "to_number": "+1234567890",
        "webhook_base_url": NGROK_URL
    })
    
    if call_response.status_code == 200:
        call_data = call_response.json()
        call_sid = call_data["call_sid"]
        print(f"Call initiated: {call_data}")
        
        # 4. Check call status
        print("\n4️⃣ Checking call status...")
        status_response = requests.get(f"{BASE_URL}/api/v1/voice-call/call-status/{call_sid}")
        print(f"Call status: {status_response.json()}")
        
        # 5. Get active sessions
        print("\n5️⃣ Getting active sessions...")
        sessions_response = requests.get(f"{BASE_URL}/api/v1/voice-call/sessions")
        print(f"Active sessions: {sessions_response.json()}")
        
        # 6. End session
        print("\n6️⃣ Ending session...")
        end_response = requests.post(f"{BASE_URL}/api/v1/voice-call/end-session", json={
            "call_sid": call_sid
        })
        print(f"Session ended: {end_response.json()}")
        
    else:
        print(f"❌ Error: {call_response.text}")

def test_auth_workflow():
    """Test authentication workflow (requires Supabase setup)"""
    
    print("\n🔐 Testing Authentication (requires Supabase)")
    
    # Test signup
    signup_data = {
        "email": "test@example.com",
        "password": "password123",
        "role": "INFLUENCER"
    }
    
    try:
        signup_response = requests.post(f"{BASE_URL}/api/v1/auth/signup", json=signup_data)
        print(f"Signup: {signup_response.status_code}")
        
        # Test login
        login_data = {
            "email": "test@example.com", 
            "password": "password123"
        }
        
        login_response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        print(f"Login: {login_response.status_code}")
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test protected route
            protected_response = requests.get(f"{BASE_URL}/api/v1/auth/protected", headers=headers)
            print(f"Protected route: {protected_response.status_code}")
            
    except Exception as e:
        print(f"Auth testing skipped (mock mode): {e}")

if __name__ == "__main__":
    test_api_complete()
    test_auth_workflow()
```

### JavaScript/Frontend Example

```javascript
class InfluencerFlowAPI {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.token = null;
    }
    
    // Authentication
    async login(email, password) {
        const response = await fetch(`${this.baseUrl}/api/v1/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            this.token = data.access_token;
            return data;
        }
        throw new Error('Login failed');
    }
    
    // Voice calls
    async initiateCall(toNumber, webhookUrl) {
        const response = await fetch(`${this.baseUrl}/api/v1/voice-call/outbound-call`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                to_number: toNumber,
                webhook_base_url: webhookUrl
            })
        });
        
        return response.json();
    }
    
    async getCallStatus(callSid) {
        const response = await fetch(`${this.baseUrl}/api/v1/voice-call/call-status/${callSid}`);
        return response.json();
    }
    
    async getActiveSessions() {
        const response = await fetch(`${this.baseUrl}/api/v1/voice-call/sessions`);
        return response.json();
    }
    
    // Health checks
    async checkHealth() {
        const response = await fetch(`${this.baseUrl}/health`);
        return response.json();
    }
    
    async checkVoiceHealth() {
        const response = await fetch(`${this.baseUrl}/api/v1/voice-call/health`);
        return response.json();
    }
}

// Usage example
const api = new InfluencerFlowAPI();

async function demo() {
    // Check health
    const health = await api.checkHealth();
    console.log('Health:', health);
    
    // Initiate call
    const call = await api.initiateCall('+1234567890', 'https://your-ngrok-url.ngrok.io');
    console.log('Call:', call);
    
    // Check call status
    const status = await api.getCallStatus(call.call_sid);
    console.log('Status:', status);
}
```

## 🛠 **Development Setup**

### 1. Clone and Setup
```bash
git clone <your-repo>
cd influencerflowAI/Influencerflow_backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your values
nano .env
```

### 3. Development Workflow
```bash
# Terminal 1: API Server
python main.py

# Terminal 2: ngrok (for webhooks)
ngrok http 8000

# Terminal 3: Testing
curl -X GET "http://localhost:8000/health"
```

### 4. API Documentation
Access interactive documentation:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## 🏗 **Architecture**

### Project Structure
```
Influencerflow_backend/
├── app/
│   ├── api/                    # API route handlers
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── voice_call.py      # Voice call endpoints
│   │   └── __init__.py
│   ├── core/                  # Core configuration
│   │   ├── config.py          # Settings and environment variables
│   │   └── __init__.py
│   ├── middleware/            # Custom middleware
│   ├── models/               # Database models
│   ├── services/             # Business logic services
│   │   ├── supabase.py       # Supabase authentication service
│   │   ├── voice_call_service.py # AI voice call service
│   │   └── __init__.py
│   └── __init__.py
├── main.py                   # FastAPI application entry point
├── requirements.txt          # Python dependencies
├── .env.example             # Environment template
├── .gitignore              # Git ignore rules
└── API_DOCUMENTATION.md    # This file
```

### Service Architecture

#### Authentication Service
- **Technology:** Supabase
- **Features:** JWT tokens, role-based access, user management
- **Modes:** Production (real Supabase) / Mock (for MVP)

#### Voice Call Service  
- **Technology:** Twilio + Google Gemini AI
- **Features:** Outbound calls, speech processing, AI conversations
- **Modes:** Production (real APIs) / Mock (for MVP)

#### Core API
- **Technology:** FastAPI
- **Features:** RESTful endpoints, automatic documentation, CORS support
- **Validation:** Simplified for MVP (no Pydantic)

### Data Flow

```
Client Request → FastAPI Router → Service Layer → External APIs → Response
                     ↓
               Middleware (Auth, CORS)
                     ↓
               Error Handling → Logging
```

## 🔧 **Troubleshooting**

### Common Issues

#### 1. Service Won't Start
```bash
# Check if ports are available
lsof -i :8000

# Check Python environment
which python
python --version

# Check dependencies
pip list
```

#### 2. Import Errors
```bash
# Missing dependencies - install them
pip install supabase twilio google-generativeai

# Or run in MVP mode (ignore optional deps)
python main.py  # Should work without external deps
```

#### 3. Webhook Issues
```bash
# Check ngrok is running
curl https://your-ngrok-url.ngrok.io/health

# Verify Twilio webhook URL in console
# Must be: https://your-ngrok-url.ngrok.io/api/v1/voice-call/voice
```

#### 4. Environment Variables
```bash
# Check if .env file exists
ls -la .env

# Verify variables are loaded
python -c "from app.core.config import settings; print(settings.cors_origins)"
```

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### API Testing

Use the interactive docs for testing:
- Navigate to http://localhost:8000/docs
- Click "Try it out" on any endpoint
- Fill parameters and execute

## 📚 **Additional Resources**

- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **Twilio Voice API:** https://www.twilio.com/docs/voice
- **Google Gemini AI:** https://ai.google.dev/docs
- **Supabase Auth:** https://supabase.com/docs/guides/auth
- **ngrok Documentation:** https://ngrok.com/docs

## 🤝 **Support**

For issues and questions:
1. Check this documentation
2. Review error logs
3. Test with curl/Postman
4. Check external service status (Twilio, Google, Supabase)

---

**API Version:** 1.0.0  
**Last Updated:** 2024  
**Mode:** MVP-Ready with Production Capabilities 