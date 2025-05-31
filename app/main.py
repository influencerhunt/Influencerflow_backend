from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.core.config import settings
from app.services.monitoring.api import router as monitoring_router  # ✅ Added monitoring router
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="InfluencerFlow API",
    description="Backend API for InfluencerFlow platform with role-based authentication",
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

# Include routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(monitoring_router, prefix="/api/v1/monitor", tags=["campaign-monitoring"])  # ✅ Include monitoring

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to InfluencerFlow API",
        "version": "1.0.0",
        "status": "active"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

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
