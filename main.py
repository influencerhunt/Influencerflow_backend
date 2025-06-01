from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.search import router as search_router
from app.core.config import settings

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

# Try to load settings - handle missing dependencies gracefully
try:
    from app.core.config import settings
    cors_origins = settings.cors_origins_list
except ImportError as e:
    logger.warning(f"Settings not available, using default CORS: {e}")
    cors_origins = ["*"]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(search_router, prefix="/api/v1/search", tags=["search"])

# Try to include routers - handle missing dependencies gracefully
try:
    from app.api.auth import router as auth_router
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])
    logger.info("Authentication routes loaded")
except ImportError as e:
    logger.warning(f"Authentication routes not available: {e}")

# try:
#     # from app.routers.negotiation import router as negotiation_router
#     app.include_router(negotiation_router, prefix="/api/v1/negotiation", tags=["negotiation"])
#     logger.info("Negotiation routes loaded")
# except ImportError as e:
#     logger.warning(f"Negotiation routes not available: {e}")

# try:
#     from app.routers.negotiation_fixed import router as negotiation_fixed_router
#     app.include_router(negotiation_fixed_router, prefix="/api/v1/negotiation-fixed", tags=["negotiation-fixed", "voice-call"])
#     logger.info("Negotiation fixed routes loaded")
# except ImportError as e:
#     logger.warning(f"Negotiation fixed routes not available: {e}")

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
    from app.services.monitoring.api import router as monitoring_router
    app.include_router(monitoring_router, prefix="/api/v1/monitor", tags=["campaign-monitoring"])
    logger.info("Monitoring routes loaded")
except ImportError as e:
    logger.warning(f"Monitoring routes not available: {e}")

try:
    from app.routers.negotiation_agent import router as negotiation_agent_router
    app.include_router(negotiation_agent_router, prefix="/api/v1", tags=["negotiation-agent"])
    logger.info("Negotiation Agent routes loaded")
except ImportError as e:
    logger.warning(f"Negotiation Agent routes not available: {e}")

# try:
#     from app.api.contracts import router as contracts_router
#     app.include_router(contracts_router, prefix="/api/v1", tags=["contracts"])
#     logger.info("Contract routes loaded")
# except ImportError as e:
#     logger.warning(f"Contract routes not available: {e}")


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

# YouTube service functions - only load if dependencies are available
try:
    from googleapiclient.discovery import build
    from app.core.config import settings
    
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
            
except ImportError as e:
    logger.warning(f"YouTube service not available: {e}")


if __name__  == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",  # ✅ Corrected module path
        host="0.0.0.0",
        port=8000,
        reload=True
    )
