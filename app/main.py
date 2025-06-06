from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.routers.negotiation import router as negotiation_router
from app.core.config import settings
from app.services.monitoring.api import router as monitoring_router  # ✅ Added monitoring router
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="InfluencerFlow API",
    description="Backend API for InfluencerFlow platform with role-based authentication and AI-powered voice calls",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Try to include routers - handle missing dependencies gracefully
try:
    from app.api.auth import router as auth_router
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])
    app.include_router(negotiation_router, prefix="/api/v1/negotiation", tags=["negotiation"])
    logger.info("Authentication routes loaded")
except ImportError as e:
    logger.warning(f"Authentication routes not available: {e}")

try:
    from app.api.voice_call import router as voice_call_router
    app.include_router(voice_call_router, prefix="/api/v1/voice-call", tags=["voice-call"])
    logger.info("Voice call routes loaded")
except ImportError as e:
    logger.warning(f"Voice call routes not available: {e}")

try:
    from app.api.agent import router as agent_router
    app.include_router(agent_router, prefix="/api/v1/agent", tags=["agent"])
    logger.info("Agent routes loaded")
except ImportError as e:
    logger.warning(f"Agent routes not available: {e}")

try:
    from app.api.contracts import router as contracts_router
    app.include_router(contracts_router, prefix="/api/v1", tags=["contracts"])
    logger.info("Contract routes loaded")
except ImportError as e:
    logger.warning(f"Contract routes not available: {e}")

# Include routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(monitoring_router, prefix="/api/v1/monitor", tags=["campaign-monitoring"])  # ✅ Include monitoring

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to InfluencerFlow API",
        "version": "1.0.0",
        "status": "active",
        "features": ["basic-api", "voice-call-mock", "agent-service"],
        "note": "Running in MVP mode - some features may be mocked"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "mode": "mvp"}

from googleapiclient.discovery import build
from app.core.config import settings  # ensure your API key is loaded correctly

def build_youtube_service():
    return build("youtube", "v3", developerKey=settings.youtube_api_key)

def get_uploads_playlist_id(channel_id: str) -> str:
    youtube = build("youtube", "v3", developerKey=settings.youtube_api_key)
    
    response = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    ).execute()
    
    try:
        uploads_playlist_id = response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        return uploads_playlist_id
    except (KeyError, IndexError):
        raise ValueError("Could not retrieve uploads playlist ID")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",  # ✅ Use correct module path for reloading
        host="0.0.0.0",
        port=8000,
        reload=True
    )
