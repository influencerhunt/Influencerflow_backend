# InfluencerFlow AI-Powered Search System

## 🎯 Overview

A comprehensive AI-powered influencer search system that combines natural language processing, database search, and web scraping to find the perfect influencers for any campaign.

## ✨ Features

### 🧠 AI-Powered Query Parsing
- **Natural Language Processing**: Uses Google Gemini AI to convert human queries into structured search filters
- **Intelligent Understanding**: Processes queries like "fashion influencers in NYC with 50k-100k followers under $1000"
- **Context Awareness**: Understands platform-specific terminology and engagement patterns

### 🔍 Hybrid Search Architecture
- **On-Platform Search**: Fast database queries against verified influencer profiles
- **External Discovery**: Web scraping via Serper API to find new influencers from Instagram, YouTube, TikTok
- **Smart Ranking**: Combines relevance, engagement rate, and follower count for optimal results

### 📊 Advanced Filtering
- **Platform**: Instagram, YouTube, TikTok, Twitter, LinkedIn, Facebook
- **Demographics**: Location, follower count ranges, engagement rates
- **Commercial**: Price per post, verified status
- **Content**: Niche categories, content themes

### 🚀 RESTful API
- **GET Endpoints**: Simple query-based search with URL parameters
- **POST Endpoints**: Advanced search with complex filter objects
- **Suggestions**: Auto-complete and search recommendations
- **Filter Options**: Dynamic filter values and ranges

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   AI Parser      │    │   Search        │
│   Endpoints     │───▶│   (Gemini)       │───▶│   Orchestrator  │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                               ┌─────────────────────────────────────┐
                               │           Search Sources            │
                               ├─────────────────┬───────────────────┤
                               │   Database      │   External APIs   │
                               │   (Supabase)    │   (Serper)       │
                               │                 │                   │
                               │ • Fast lookup   │ • Web scraping   │
                               │ • Verified data │ • Real-time data │
                               │ • Rich profiles │ • Discovery       │
                               └─────────────────┴───────────────────┘
```

## 🛠️ Technical Stack

- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL)
- **AI**: Google Gemini 1.5 Flash
- **Web Scraping**: Serper API
- **Data Models**: Python Dataclasses
- **Authentication**: JWT tokens
- **Configuration**: python-decouple

## 📁 Project Structure

```
InfluencerFlow_backend/
├── app/
│   ├── api/
│   │   ├── auth.py           # Authentication endpoints
│   │   └── search.py         # Search endpoints
│   ├── core/
│   │   └── config.py         # Configuration management
│   ├── models/
│   │   └── influencer.py     # Data models and schemas
│   ├── services/
│   │   ├── ai_parser.py      # Gemini AI integration
│   │   ├── database.py       # Database search service
│   │   ├── external_scraper.py # Web scraping service
│   │   ├── search_service.py # Main orchestration service
│   │   └── supabase.py       # Database client
│   └── middleware/
│       └── auth.py           # Authentication middleware
├── main.py                   # FastAPI application
├── requirements.txt          # Python dependencies
├── database_schema.sql       # Database schema
└── setup_database.py        # Database setup script
```

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Clone and navigate to project
cd InfluencerFlow_backend

# Create virtual environment
python -m venv env
source env/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create `.env` file with your API keys:

```env
# Database
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# AI & External APIs
GEMINI_API_KEY=your_gemini_api_key
SERPER_API_KEY=your_serper_api_key

# Application
SECRET_KEY=your_jwt_secret_key
CORS_ORIGINS=http://localhost:3000
```

### 3. Database Setup

```bash
# Run database setup script
python setup_database.py
```

### 4. Start the Server

```bash
# Start FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Test the API

Visit `http://localhost:8000/docs` for interactive API documentation.

## 📚 API Reference

### Search Endpoints

#### POST /api/v1/search/search
Advanced search with AI parsing and complex filters.

**Request Body:**
```json
{
  "query": "fashion influencers in NYC with 50k followers",
  "limit": 20,
  "include_external": true,
  "filters": {
    "platform": "instagram",
    "followers_min": 50000,
    "followers_max": 100000,
    "location": "New York",
    "niche": "fashion",
    "price_max": 1000,
    "verified_only": false
  }
}
```

**Response:**
```json
{
  "query": "fashion influencers in NYC with 50k followers",
  "total_results": 15,
  "on_platform_count": 8,
  "external_count": 7,
  "influencers": [
    {
      "id": "uuid",
      "name": "Sarah Fashion",
      "username": "sarahfashion",
      "platform": "instagram",
      "followers": 125000,
      "engagement_rate": 3.5,
      "price_per_post": 850,
      "location": "New York, NY",
      "niche": "fashion",
      "bio": "Fashion blogger and style influencer",
      "verified": true,
      "source": "on_platform"
    }
  ]
}
```

#### GET /api/v1/search/search
Simple search with query parameters.

**Parameters:**
- `query` (required): Natural language search query
- `limit`: Maximum results (default: 20, max: 100)
- `platform`: Filter by platform
- `location`: Filter by location
- `followers_min`/`followers_max`: Follower count range
- `price_min`/`price_max`: Price per post range
- `verified_only`: Only verified accounts

### Utility Endpoints

#### GET /api/v1/search/suggestions
Get search suggestions for autocomplete.

**Parameters:**
- `query`: Partial query for suggestions

**Response:**
```json
["fashion influencers in New York", "fashion bloggers", "fashion content creators"]
```

#### GET /api/v1/search/filters/options
Get available filter options.

**Response:**
```json
{
  "platforms": ["instagram", "youtube", "tiktok", "twitter", "linkedin", "facebook"],
  "popular_niches": ["fashion", "beauty", "fitness", "food", "travel", "tech"],
  "follower_ranges": [
    {"label": "Nano (1K-10K)", "min": 1000, "max": 10000},
    {"label": "Micro (10K-100K)", "min": 10000, "max": 100000}
  ],
  "price_ranges": [
    {"label": "Budget (<$100)", "min": 0, "max": 100},
    {"label": "Standard ($100-$500)", "min": 100, "max": 500}
  ]
}
```

## 🧪 Testing

### Run All Tests
```bash
# Test AI parsing
python test_search.py

# Test database functionality
python test_database.py

# Test complete search pipeline
python test_complete_search.py

# Test API endpoints
python test_api.py
```

### Sample Test Queries
- "fashion influencers in New York with 50k to 100k followers"
- "tech YouTubers with high engagement"
- "verified beauty influencers under $1000"
- "fitness TikTokers in Los Angeles"
- "travel influencers with 100k+ followers"

## 🎯 AI Query Examples

The system understands complex natural language queries:

| Query | AI Understanding |
|-------|------------------|
| "fashion bloggers in NYC under $500" | `location: "New York", niche: "fashion", price_max: 500` |
| "verified tech YouTubers with 100k+ followers" | `platform: "youtube", niche: "tech", followers_min: 100000, verified_only: true` |
| "high engagement fitness influencers" | `niche: "fitness", engagement_min: 5.0` |
| "beauty TikTokers in LA" | `platform: "tiktok", niche: "beauty", location: "Los Angeles"` |

## 📊 Database Schema

```sql
CREATE TABLE influencers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    followers INTEGER NOT NULL DEFAULT 0,
    engagement_rate DECIMAL(5,2),
    price_per_post INTEGER,
    location VARCHAR(255),
    niche VARCHAR(255),
    bio TEXT,
    profile_link VARCHAR(500),
    avatar_url VARCHAR(500),
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## 🔧 Configuration Options

### Environment Variables
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_ANON_KEY`: Supabase anonymous key
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role key
- `GEMINI_API_KEY`: Google Gemini AI API key
- `SERPER_API_KEY`: Serper web search API key
- `SECRET_KEY`: JWT token secret key
- `CORS_ORIGINS`: Allowed CORS origins

### AI Parser Configuration
- Model: `gemini-1.5-flash`
- Temperature: Optimized for structured output
- Safety settings: Configured for business use

### External Scraper Settings
- Platforms: Instagram, YouTube, TikTok
- Rate limiting: Respect API quotas
- Fallback: Graceful degradation if APIs fail

## 🔒 Security Features

- **Row Level Security**: Database-level access control
- **JWT Authentication**: Secure token-based auth
- **CORS Protection**: Configured allowed origins
- **Input Validation**: Comprehensive request validation
- **Rate Limiting**: Built-in API rate limiting

## 🚀 Deployment

### Production Checklist
- [ ] Set secure `SECRET_KEY`
- [ ] Configure production database
- [ ] Set up monitoring and logging
- [ ] Configure reverse proxy (nginx)
- [ ] Set up SSL certificates
- [ ] Configure environment variables
- [ ] Set up database backups

### Performance Optimization
- Database indexing on search fields
- Connection pooling for database
- Caching for frequent queries
- Async processing for external APIs
- Result pagination for large datasets

## 📈 Monitoring

### Key Metrics
- Search response times
- AI parsing accuracy
- External API success rates
- Database query performance
- User engagement patterns

### Logging
- Structured JSON logging
- Request/response tracking
- Error monitoring
- Performance metrics
- API usage analytics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

---

## 🎉 Status: Production Ready!

The InfluencerFlow AI-Powered Search System is now fully functional with:

✅ **AI Query Parsing** - Converting natural language to structured filters  
✅ **Database Search** - Fast queries against verified influencer profiles  
✅ **External Discovery** - Real-time web scraping for new influencers  
✅ **RESTful API** - Complete FastAPI endpoints with documentation  
✅ **Comprehensive Testing** - Full test suite with real API validation  
✅ **Production Configuration** - Environment management and security  

Ready for frontend integration and production deployment!
