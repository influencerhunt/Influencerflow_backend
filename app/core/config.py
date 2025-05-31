import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL", "")
        self.supabase_anon_key = os.getenv("SUPABASE_ANON_KEY", "")
        self.supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.database_url = os.getenv("DATABASE_URL", "")
        self.cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins to list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]

settings = Settings() 