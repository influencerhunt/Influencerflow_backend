from decouple import config
from typing import List
import os


class Settings:
    def __init__(self):
        self.supabase_url = config("SUPABASE_URL", default="")
        self.supabase_anon_key = config("SUPABASE_ANON_KEY", default="")
        self.supabase_service_role_key = config("SUPABASE_SERVICE_ROLE_KEY", default="")
        self.jwt_secret_key = config("SECRET_KEY", default="your-secret-key")
        self.jwt_algorithm = config("JWT_ALGORITHM", default="HS256")
        self.access_token_expire_minutes = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=30, cast=int)
        self.database_url = config("DATABASE_URL", default="")
        self.cors_origins = config("CORS_ORIGINS", default="http://localhost:3000")
        
        # AI and External API Keys
        self.gemini_api_key = config("GEMINI_API_KEY", default="")
        self.serper_api_key = config("SERPER_API_KEY", default="")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins to list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Create settings instance
settings = Settings() 