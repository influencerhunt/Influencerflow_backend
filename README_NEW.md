# InfluencerFlow Backend - Advanced Negotiation Agent

## 🎯 Overview

InfluencerFlow Backend is a sophisticated platform featuring an AI-powered negotiation agent that facilitates fair and effective collaborations between brands and influencers. The system uses Google Gemini AI with LangChain React Agents to create human-like conversations that analyze market rates, negotiate terms, and reach mutually beneficial agreements.

## ✨ Key Features

### 🤖 Advanced Negotiation Agent (Maya)
- **Conversational AI**: Natural, human-like negotiations using Google Gemini
- **Market Rate Analysis**: Real-time pricing based on engagement, followers, location, and platform
- **Multi-Platform Support**: Instagram, YouTube, LinkedIn, TikTok, Twitter
- **Dynamic Pricing**: Content-type specific rates (posts, reels, stories, videos)
- **Smart Negotiations**: Counter-offer analysis and compromise suggestions
- **Session Management**: Persistent conversation states and history

### 📊 Intelligent Pricing Engine
- **Market-Based Calculations**: Fair pricing using industry standards
- **Location Multipliers**: Geography-based rate adjustments
- **Engagement Analysis**: Quality-focused pricing beyond follower count
- **Budget Optimization**: Alternative suggestions when budgets don't align
- **Content Type Pricing**: Different rates for different content formats

### 🔧 Technical Stack
- **Backend**: FastAPI with Python 3.11+
- **AI/ML**: Google Gemini, LangChain React Agents
- **Database**: Supabase (PostgreSQL)
- **Authentication**: JWT-based role management
- **API**: RESTful with automatic OpenAPI documentation

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Google Gemini API key
- Supabase account (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Influencerflow_backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate     # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment setup**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your Google Gemini API key:
   ```bash
   GOOGLE_API_KEY=your_google_gemini_api_key_here
   ```

5. **Run the application**
   ```bash
   python main.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Access the API**
   - API Base URL: `http://localhost:8000`
   - Interactive Docs: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

## 🎬 Demo Usage

### Quick Demo
Run the included demo script to see the negotiation agent in action:

```bash
python demo_agent.py
```

This will demonstrate:
- Complete negotiation flow between a brand and influencer
- Market rate calculations
- Conversation management
- Different pricing scenarios

### API Usage Examples

#### 1. Start a New Negotiation

```bash
curl -X POST "http://localhost:8000/api/v1/negotiation/start" \
-H "Content-Type: application/json" \
-d '{
  "brand_details": {
    "name": "EcoTech Solutions",
    "budget": 8000.0,
    "goals": ["brand awareness", "product launch"],
    "target_platforms": ["instagram", "youtube"],
    "content_requirements": {
      "instagram_post": 3,
      "instagram_reel": 2,
      "youtube_shorts": 1
    },
    "campaign_duration_days": 30
  },
  "influencer_profile": {
    "name": "Alex Green",
    "followers": 75000,
    "engagement_rate": 0.065,
    "location": "US",
    "platforms": ["instagram", "youtube"],
    "niches": ["sustainability", "technology"]
  }
}'
```

#### 2. Continue the Conversation

```bash
curl -X POST "http://localhost:8000/api/v1/negotiation/continue" \
-H "Content-Type: application/json" \
-d '{
  "session_id": "your-session-id-from-start-response",
  "user_input": "The pricing looks good! I'm interested in moving forward. Can we discuss the timeline?"
}'
```

#### 3. Get Negotiation Summary

```bash
curl -X GET "http://localhost:8000/api/v1/negotiation/session/{session_id}/summary"
```

## 📋 API Endpoints

### Negotiation Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/negotiation/start` | Start new negotiation |
| POST | `/api/v1/negotiation/continue` | Continue conversation |
| GET | `/api/v1/negotiation/session/{id}/summary` | Get negotiation summary |
| DELETE | `/api/v1/negotiation/session/{id}` | Clear session |
| GET | `/api/v1/negotiation/sessions` | List active sessions |
| GET | `/api/v1/negotiation/platforms` | Get platform details |
| GET | `/api/v1/negotiation/locations` | Get supported locations |
| POST | `/api/v1/negotiation/test/mock-negotiation` | Create mock negotiation |

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | User login |
| POST | `/api/v1/auth/register` | User registration |
| GET | `/api/v1/auth/me` | Get current user |

## 💰 Pricing Model

### Base Rates (per 1K followers)
- **Instagram Post**: $1.00
- **Instagram Reel**: $1.50
- **Instagram Story**: $0.30
- **YouTube Long-form**: $2.00
- **YouTube Shorts**: $1.00
- **LinkedIn Post**: $0.80
- **LinkedIn Video**: $1.30

### Location Multipliers
- 🇺🇸 United States: 1.8x
- 🇬🇧 United Kingdom: 1.6x
- 🇨🇦 Canada: 1.5x
- 🇦🇺 Australia: 1.4x
- 🇩🇪 Germany: 1.3x
- 🇫🇷 France: 1.2x
- 🇯🇵 Japan: 1.1x
- 🇧🇷 Brazil: 0.8x
- 🇮🇳 India: 0.6x
- 🌍 Other: 1.0x

### Calculation Formula
```
Final Rate = Base Rate × (Engagement Rate × 100) × (Followers ÷ 1000) × Location Multiplier × Platform Weight
```

## 🏗️ Architecture

### Project Structure
```
Influencerflow_backend/
├── app/
│   ├── agents/                 # AI negotiation agents
│   │   └── negotiation_agent.py
│   ├── models/                 # Pydantic models
│   │   └── negotiation_models.py
│   ├── services/               # Business logic services
│   │   ├── pricing_service.py
│   │   ├── conversation_handler.py
│   │   └── supabase.py
│   ├── routers/                # API route handlers
│   │   └── negotiation.py
│   ├── api/                    # Authentication endpoints
│   │   └── auth.py
│   ├── core/                   # Core configuration
│   │   └── config.py
│   └── middleware/             # Custom middleware
│       └── auth.py
├── demo_agent.py              # Demo script
├── main.py                    # FastAPI application
├── requirements.txt           # Python dependencies
└── README.md                 # This file
```

### Key Components

#### 1. AdvancedNegotiationAgent
- **Purpose**: Main AI agent orchestrating negotiations
- **Features**: LangChain React Agent with custom tools
- **Tools**: Market rate calculation, campaign costing, budget alternatives

#### 2. PricingService
- **Purpose**: Calculate fair market rates
- **Features**: Multi-platform support, location-based pricing, engagement analysis

#### 3. ConversationHandler
- **Purpose**: Manage conversation flow and templates
- **Features**: Session state management, response templates, conversation analysis

#### 4. NegotiationModels
- **Purpose**: Type-safe data models
- **Features**: Pydantic validation, enum types, structured data

## 🔧 Configuration

### Environment Variables

```bash
# Required
GOOGLE_API_KEY=your_google_gemini_api_key

# Optional (for full functionality)
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# FastAPI Settings
DEBUG=True
HOST=localhost
PORT=8000
LOG_LEVEL=INFO
```

### Supported Platforms

| Platform | Content Types | Notes |
|----------|---------------|-------|
| Instagram | Post, Reel, Story | Visual content focus |
| YouTube | Long-form, Shorts | Video content |
| LinkedIn | Post, Video | Professional network |
| TikTok | Video | Short-form entertainment |
| Twitter | Post, Video | Microblogging |

## 🤝 Negotiation Flow

### 1. Initialization
- Brand submits campaign details and budget
- Agent analyzes requirements and market conditions
- Initial market rate calculation performed
- Personalized proposal generated

### 2. Conversation Stages
1. **Greeting & Analysis**: Introduction with market rate analysis
2. **Proposal Presentation**: Structured offer with breakdown
3. **Active Negotiation**: Back-and-forth discussion
4. **Counter-Offer Handling**: Analysis and compromise suggestions
5. **Agreement/Rejection**: Final terms or alternative options

### 3. Agent Capabilities
- ✅ Market rate analysis using real-time data
- ✅ Budget constraint handling and alternatives
- ✅ Counter-offer evaluation and compromise suggestions
- ✅ Timeline and deliverable negotiation
- ✅ Usage rights and terms discussion
- ✅ Professional relationship maintenance

## 🧪 Testing

### Run Demo
```bash
python demo_agent.py
```

### Test Mock Negotiation API
```bash
curl -X POST "http://localhost:8000/api/v1/negotiation/test/mock-negotiation"
```

### Manual Testing Flow
1. Start a negotiation using the `/start` endpoint
2. Use the returned `session_id` to continue conversations
3. Test different scenarios: acceptance, rejection, counter-offers
4. Check session summaries and conversation history

## 🐛 Troubleshooting

### Common Issues

1. **Missing Google API Key**
   ```
   Error: GOOGLE_API_KEY environment variable not set
   ```
   **Solution**: Add your Google Gemini API key to `.env`

2. **Import Errors**
   ```
   ModuleNotFoundError: No module named 'app'
   ```
   **Solution**: Run from project root directory

3. **Agent Parsing Errors**
   ```
   Could not parse LLM output
   ```
   **Solution**: Check API key validity and network connection

4. **Session Not Found**
   ```
   Session not found
   ```
   **Solution**: Use valid session_id from start response

### Debug Mode
Set `DEBUG=True` in `.env` for detailed logging and error traces.

## 🚀 Deployment

### Production Considerations
- Set `DEBUG=False` in production
- Use proper secrets management for API keys
- Configure CORS origins for your frontend domain
- Set up proper logging and monitoring
- Use a production WSGI server like Gunicorn

### Docker Deployment (Optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangChain Documentation](https://python.langchain.com/)
- [Google Gemini API](https://ai.google.dev/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

---

**Built with ❤️ for the creator economy**
