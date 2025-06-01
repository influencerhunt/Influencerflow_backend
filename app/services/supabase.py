from supabase import create_client, Client
from ..core.config import settings
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SupabaseService:
    _client: Optional[Client] = None
    _admin_client: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        if cls._client is None:
            cls._client = create_client(
                settings.supabase_url,
                settings.supabase_anon_key
            )
        return cls._client
    
    @classmethod
    def get_admin_client(cls) -> Client:
        if cls._admin_client is None:
            cls._admin_client = create_client(
                settings.supabase_url,
                settings.supabase_service_role_key
            )
        return cls._admin_client
    
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

    @classmethod
    async def update_user_metadata(cls, user_id: str, metadata: dict):
        """Update user metadata"""
        try:
            client = cls.get_admin_client()
            
            # Use admin client to update user metadata
            response = client.auth.admin.update_user_by_id(
                user_id,
                {
                    "user_metadata": metadata
                }
            )
            
            if response.user is None:
                raise Exception("Failed to update user metadata")
                
            return response.user
            
        except Exception as e:
            logger.error(f"Supabase update user metadata error: {str(e)}")
            raise e

    # ==================== DATABASE OPERATIONS ====================
    
    @classmethod
    async def insert_data(cls, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert data into a table"""
        try:
            client = cls.get_admin_client()
            response = client.table(table).insert(data).execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Supabase insert error on table {table}: {str(e)}")
            raise e

    @classmethod
    async def fetch_data(cls, table: str, filters: Dict[str, Any] = None) -> list:
        """Fetch data from a table with optional filters"""
        try:
            client = cls.get_admin_client()
            query = client.table(table).select("*")
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Supabase fetch error on table {table}: {str(e)}")
            raise e

    @classmethod
    async def update_data(cls, table: str, updates: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Update data in a table"""
        try:
            client = cls.get_admin_client()
            query = client.table(table).update(updates)
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            response = query.execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Supabase update error on table {table}: {str(e)}")
            raise e

    @classmethod
    async def delete_data(cls, table: str, filters: Dict[str, Any]) -> bool:
        """Delete data from a table"""
        try:
            client = cls.get_admin_client()
            query = client.table(table).delete()
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            response = query.execute()
            return True
        except Exception as e:
            logger.error(f"Supabase delete error on table {table}: {str(e)}")
            raise e

    @classmethod
    async def upload_file(cls, bucket: str, file_path: str, file_data: bytes, content_type: str = None) -> str:
        """Upload a file to Supabase storage"""
        try:
            client = cls.get_admin_client()
            
            # Upload file
            response = client.storage.from_(bucket).upload(
                file_path, 
                file_data,
                {"content-type": content_type} if content_type else {}
            )
            
            if response.status_code == 200:
                # Get public URL
                public_url = client.storage.from_(bucket).get_public_url(file_path)
                return public_url
            else:
                raise Exception(f"Upload failed with status: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Supabase file upload error: {str(e)}")
            raise e

supabase_service = SupabaseService() 