# Voice Call Integration with Negotiation Agent

This document describes the voice call functionality integrated with the `negotiation_fixed` agent that enables real-time phone conversations for influencer marketing negotiations.

## 🎯 Overview

The voice call system combines:
- **Twilio Voice API** for phone calls and speech recognition
- **AdvancedNegotiationAgent** for intelligent brand-side negotiations  
- **Real-time TwiML responses** for conversational flow
- **Session management** linking voice calls to negotiation sessions

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│   Phone Call    │───▶│   Twilio Voice   │───▶│  FastAPI Backend    │
│  (Influencer)   │    │   (Speech-to-Text│    │ (negotiation_fixed) │
└─────────────────┘    │   Text-to-Speech)│    └─────────────────────┘
                       └──────────────────┘              │
                                                          ▼
                                                ┌─────────────────────┐
                                                │ AdvancedNegotiation │
                                                │       Agent         │
                                                │  (AI Conversations) │
                                                └─────────────────────┘
```

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Install dependencies
pip install twilio python-dotenv

# Set up environment variables in .env
GOOGLE_API_KEY=your_gemini_api_key
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token  
TWILIO_NUMBER=your_twilio_phone_number
```

### 2. Start the Server

```bash
# Start FastAPI server
uvicorn main:app --reload

# In another terminal, start ngrok for webhook URLs
ngrok http 8000
```

### 3. Test Voice Call

```bash
# Run the demo script
python demo_voice_call.py
```

## 📞 Voice Call Endpoints

### Start Voice Call
```http
POST /api/v1/negotiation-fixed/voice/start-call
```

**Request Body:**
```json
{
  "to_number": "+1234567890",
  "webhook_base_url": "https://your-ngrok-url.ngrok.io",
  "brand_details": {
    "name": "EcoTech Solutions",
    "budget": 8000.0,
    "goals": ["brand awareness", "product launch"],
    "target_platforms": ["instagram", "youtube"],
    "content_requirements": {
      "instagram_post": 4,
      "instagram_reel": 3
    },
    "campaign_duration_days": 45,
    "target_audience": "Eco-conscious millennials"
  },
  "influencer_profile": {
    "name": "Sarah EcoLiving", 
    "followers": 125000,
    "engagement_rate": 0.078,
    "location": "US",
    "platforms": ["instagram", "youtube"],
    "niches": ["sustainability", "zero waste"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "call_sid": "CAXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "negotiation_session_id": "uuid-of-negotiation-session",
  "message": "Voice call initiated to +1234567890",
  "initial_negotiation_message": "Hello! I'm representing EcoTech Solutions..."
}
```

### Get Call Status
```http
GET /api/v1/negotiation-fixed/voice/status/{call_sid}
```

**Response:**
```json
{
  "call_sid": "CAXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "call_status": "active",
  "brand_name": "EcoTech Solutions",
  "influencer_name": "Sarah EcoLiving",
  "negotiation_session_id": "uuid-of-session",
  "negotiation_summary": {
    "status": "in_progress", 
    "negotiation_round": 3,
    "conversation_length": 12
  }
}
```

### List Voice Sessions
```http
GET /api/v1/negotiation-fixed/voice/sessions
```

### End Voice Session
```http
DELETE /api/v1/negotiation-fixed/voice/end-session/{call_sid}
```

## 🔗 Twilio Webhook Endpoints

These endpoints are called automatically by Twilio:

### Inbound Call Handler
```http
POST /api/v1/negotiation-fixed/voice/inbound
```
- Handles incoming voice calls
- Creates negotiation session
- Returns TwiML with initial greeting

### Speech Gathering 
```http
POST /api/v1/negotiation-fixed/voice/gather
```
- Processes speech-to-text results
- Sends input to negotiation agent
- Returns TwiML with agent response

### Partial Results
```http
POST /api/v1/negotiation-fixed/voice/partial
```
- Handles partial speech recognition results
- Used for interruption detection

## ⚙️ Configuration

### Twilio Configuration

1. **Phone Number Setup**
   - Purchase a Twilio phone number
   - Configure webhook URL: `https://your-ngrok-url.ngrok.io/api/v1/negotiation-fixed/voice/inbound`

2. **Speech Recognition Settings**
   - Language: `en-IN` (Indian English)
   - Speech Model: `phone_call` (optimized for calls)
   - Enhanced: `true` (better accuracy)
   - Hints: Business and negotiation terms

### Environment Variables

```bash
# Required for real voice calls
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_NUMBER=+1234567890

# Required for AI agent
GOOGLE_API_KEY=your_gemini_api_key

# Optional
NGROK_URL=https://your-ngrok-url.ngrok.io
```

## 🧪 Testing

### Mock Mode (No Twilio)
```python
# Run without Twilio credentials
python demo_voice_call.py
```

### Real Call Testing
```python
# Set environment variables and run
TWILIO_ACCOUNT_SID=your_sid TWILIO_AUTH_TOKEN=your_token python demo_voice_call.py
```

### Manual Testing
```bash
# Test mock voice call
curl -X POST "http://localhost:8000/api/v1/negotiation-fixed/test/mock-voice-call"

# Check voice sessions
curl -X GET "http://localhost:8000/api/v1/negotiation-fixed/voice/sessions"
```

## 📋 Features

### ✅ Current Features
- **Real-time voice calls** via Twilio
- **AI-powered negotiations** using AdvancedNegotiationAgent
- **Speech-to-text** with Indian English support
- **Text-to-speech** responses from AI
- **Session management** linking calls to negotiations
- **Mock mode** for testing without Twilio
- **Status monitoring** and session tracking
- **Webhook handling** for Twilio callbacks

### 🔄 Call Flow

1. **Initiate Call**: API call starts voice call and negotiation session
2. **Inbound Handler**: Twilio webhook creates TwiML with greeting
3. **Speech Gathering**: User speech → AI agent → TwiML response
4. **Continuous Loop**: Back-and-forth conversation until completion
5. **Session End**: Cleanup of call and negotiation sessions

### 🎤 Speech Features

- **Enhanced Recognition**: Better accuracy for business terms
- **Indian English Support**: Optimized for Indian pronunciation
- **Business Hints**: Terms like "rupees, lakhs, crores, negotiation"
- **Partial Results**: Real-time speech processing
- **Interruption Handling**: Natural conversation flow

## 🛠️ Advanced Usage

### Custom Negotiation Parameters

```python
# Create specialized negotiation session
brand_details = BrandDetails(
    name="Custom Brand",
    budget=10000.0,
    goals=["specific", "goals"],
    # ... other parameters
)

# Start voice call with custom data
voice_call_result = await start_voice_call(voice_request)
```

### Monitoring Active Calls

```python
# Get all active voice sessions
sessions = requests.get("/api/v1/negotiation-fixed/voice/sessions")

# Monitor specific call
status = requests.get(f"/api/v1/negotiation-fixed/voice/status/{call_sid}")
```

### Integration with Frontend

```javascript
// Start voice call from frontend
const voiceCall = await fetch('/api/v1/negotiation-fixed/voice/start-call', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(voiceCallData)
});

// Monitor call status
const callStatus = await fetch(`/api/v1/negotiation-fixed/voice/status/${callSid}`);
```

## 🔧 Troubleshooting

### Common Issues

1. **"Service temporarily unavailable"**
   - Check if Twilio library is installed: `pip install twilio`
   - Verify environment variables are set

2. **Mock calls only**
   - Set real Twilio credentials in `.env`
   - Restart the FastAPI server

3. **Webhook errors**
   - Ensure ngrok is running: `ngrok http 8000`
   - Update webhook URLs in Twilio console
   - Check ngrok logs for incoming requests

4. **AI responses not working**
   - Verify `GOOGLE_API_KEY` is set
   - Check agent service status: `/api/v1/agent/health`

### Debug Mode

```bash
# Run with debug logging
PYTHONPATH=. python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from main import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8000, log_level='debug')
"
```

## 📚 API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation with all endpoints, request/response schemas, and testing capabilities.

## 🤝 Integration Points

The voice call system integrates with:
- **AdvancedNegotiationAgent**: Core AI negotiation logic
- **PricingService**: Market rate calculations
- **ConversationHandler**: Session management
- **Twilio Voice API**: Phone call infrastructure
- **Google Gemini**: AI conversation capabilities

## 📈 Performance Considerations

- **Session Cleanup**: Automatic cleanup of completed calls
- **Memory Management**: In-memory session storage (consider Redis for production)
- **Rate Limiting**: Twilio API limits apply
- **Speech Timeout**: 30-second timeout with 5-second speech detection
- **Error Handling**: Graceful fallbacks for API failures

## 🔐 Security

- **Webhook Validation**: Twilio signature validation (configurable)
- **Environment Variables**: Sensitive credentials stored securely
- **HTTPS Required**: ngrok/production URLs must use HTTPS
- **Session Isolation**: Each call has independent session data

---

**Need Help?** 
- Check the logs for detailed error messages
- Test with mock mode first before using real Twilio calls
- Verify all environment variables are properly set
- Use the demo script for initial testing 