from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 