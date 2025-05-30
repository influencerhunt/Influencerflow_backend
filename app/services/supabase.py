from supabase import create_client, Client
from ..core.config import settings
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SupabaseService:
    _client: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        if cls._client is None:
            cls._client = create_client(
                settings.supabase_url,
                settings.supabase_anon_key
            )
        return cls._client
    
    @classmethod
    async def sign_up(cls, email: str, password: str, role: str = "user"):
        """Sign up a new user"""
        try:
            client = cls.get_client()
            response = client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "role": role
                    }
                }
            })
            
            if response.user is None:
                raise Exception("Failed to create user")
                
            return response
            
        except Exception as e:
            logger.error(f"Supabase sign up error: {str(e)}")
            raise e
    
    @classmethod
    async def sign_in(cls, email: str, password: str):
        """Sign in an existing user"""
        try:
            client = cls.get_client()
            response = client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user is None:
                raise Exception("Invalid credentials")
                
            return response
            
        except Exception as e:
            logger.error(f"Supabase sign in error: {str(e)}")
            raise e
    
    @classmethod
    async def exchange_oauth_code(cls, provider: str, code: str):
        """Exchange OAuth authorization code for tokens"""
        try:
            client = cls.get_client()
            logger.info(f"Attempting to exchange OAuth code for provider: {provider}")
            
            # Try using the session exchange method
            response = client.auth.exchange_code_for_session({"auth_code": code})
            
            if response.user is None:
                raise Exception("Failed to exchange code for session")
                
            return response
            
        except Exception as e:
            logger.error(f"Supabase OAuth code exchange error: {str(e)}")
            raise e
    
    @classmethod
    async def sign_in_with_oauth_token(cls, provider: str, access_token: str):
        """Exchange OAuth token with Supabase"""
        try:
            client = cls.get_client()
            response = client.auth.sign_in_with_oauth({
                "provider": provider,
                "options": {
                    "access_token": access_token
                }
            })
            
            if response.user is None:
                raise Exception("Failed to authenticate with OAuth")
                
            return response
            
        except Exception as e:
            logger.error(f"Supabase OAuth sign in error: {str(e)}")
            raise e
    
    @classmethod
    def get_oauth_url(cls, provider: str, redirect_to: str = None):
        """Get OAuth provider URL with implicit flow"""
        try:
            client = cls.get_client()
            response = client.auth.sign_in_with_oauth({
                "provider": provider,
                "options": {
                    "redirect_to": redirect_to or "http://localhost:3000/auth/callback"
                }
            })
            
            return response.url
            
        except Exception as e:
            logger.error(f"Supabase OAuth URL error: {str(e)}")
            raise e
    
    @classmethod
    async def sign_out(cls, access_token: str):
        """Sign out current user"""
        try:
            client = cls.get_client()
            response = client.auth.sign_out()
            return response
            
        except Exception as e:
            logger.error(f"Supabase sign out error: {str(e)}")
            raise e
    
    @classmethod
    async def get_user(cls, access_token: str):
        """Get user from access token"""
        try:
            client = cls.get_client()
            response = client.auth.get_user(access_token)
            
            if response.user is None:
                raise Exception("Invalid token")
                
            return response.user
            
        except Exception as e:
            logger.error(f"Supabase get user error: {str(e)}")
            raise e

supabase_service = SupabaseService() 