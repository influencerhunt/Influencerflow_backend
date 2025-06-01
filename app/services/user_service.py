from .supabase import SupabaseService
from ..schemas.user import UserUpdate, UserProfile
from typing import Optional, Dict, Any
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class UserService:
    
    @classmethod
    async def create_user_profile_table(cls):
        """Create user_profiles table if it doesn't exist"""
        try:
            client = SupabaseService.get_admin_client()
            
            # Create the user_profiles table
            query = """
            CREATE TABLE IF NOT EXISTS user_profiles (
                id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
                email TEXT NOT NULL,
                full_name TEXT,
                role TEXT,
                profile_completed BOOLEAN DEFAULT FALSE,
                
                -- Profile information
                bio TEXT,
                location TEXT,
                website TEXT,
                phone TEXT,
                
                -- Social media handles
                social_instagram TEXT,
                social_tiktok TEXT,
                social_youtube TEXT,
                social_twitter TEXT,
                
                -- Influencer-specific fields
                experience_level TEXT,
                content_categories JSONB,
                
                -- Brand-specific fields
                company TEXT,
                budget_range TEXT,
                
                -- Common fields
                interests JSONB,
                
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            -- Create or replace the update trigger
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ language 'plpgsql';
            
            DROP TRIGGER IF EXISTS update_user_profiles_updated_at ON user_profiles;
            CREATE TRIGGER update_user_profiles_updated_at
                BEFORE UPDATE ON user_profiles
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
                
            -- Enable RLS
            ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
            
            -- Create policies
            CREATE POLICY "Users can view own profile" ON user_profiles
                FOR SELECT USING (auth.uid() = id);
                
            CREATE POLICY "Users can update own profile" ON user_profiles
                FOR UPDATE USING (auth.uid() = id);
                
            CREATE POLICY "Users can insert own profile" ON user_profiles
                FOR INSERT WITH CHECK (auth.uid() = id);
            """
            
            client.postgrest.rpc('exec_sql', {'sql': query}).execute()
            logger.info("User profiles table created successfully")
            
        except Exception as e:
            logger.error(f"Error creating user profiles table: {str(e)}")
            # Don't raise the error as the table might already exist
    
    @classmethod
    async def get_or_create_user_profile(cls, user_id: str, email: str, role: str = "user") -> Optional[Dict[str, Any]]:
        """Get user profile or create if doesn't exist"""
        try:
            client = SupabaseService.get_admin_client()
            
            # First, try to get existing profile
            response = client.table('user_profiles').select('*').eq('id', user_id).execute()
            
            if response.data and len(response.data) > 0:
                profile = response.data[0]
                
                # Convert JSON fields back to lists
                if profile.get('content_categories'):
                    try:
                        profile['content_categories'] = json.loads(profile['content_categories'])
                    except:
                        profile['content_categories'] = []
                
                if profile.get('interests'):
                    try:
                        profile['interests'] = json.loads(profile['interests'])
                    except:
                        profile['interests'] = []
                
                return profile
            
            # If no profile exists, create one
            # Handle case where role is None (new Google OAuth users)
            profile_data = {
                'id': user_id,
                'email': email,
                'role': role,  # Keep as None if not provided
                'profile_completed': False,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            response = client.table('user_profiles').insert(profile_data).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting/creating user profile: {str(e)}")
            # If table doesn't exist, return minimal profile data
            return {
                'id': user_id,
                'email': email,
                'role': role,  # Keep as None if not provided
                'profile_completed': False,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
    
    @classmethod
    async def update_user_profile(cls, user_id: str, profile_data: UserUpdate) -> Optional[Dict[str, Any]]:
        """Update user profile with new data"""
        try:
            client = SupabaseService.get_admin_client()
            
            # Convert profile data to dict and handle JSON fields
            update_data = profile_data.dict(exclude_unset=True)
            
            # Convert lists to JSON for database storage
            if 'content_categories' in update_data and update_data['content_categories']:
                update_data['content_categories'] = json.dumps(update_data['content_categories'])
            
            if 'interests' in update_data and update_data['interests']:
                update_data['interests'] = json.dumps(update_data['interests'])
            
            # Mark profile as completed if significant data is provided
            if any(key in update_data for key in ['full_name', 'bio', 'location', 'company']):
                update_data['profile_completed'] = True
            
            update_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Try to update existing profile
            response = client.table('user_profiles').update(update_data).eq('id', user_id).execute()
            
            if response.data and len(response.data) > 0:
                profile = response.data[0]
                
                # Convert JSON fields back to lists
                if profile.get('content_categories'):
                    try:
                        profile['content_categories'] = json.loads(profile['content_categories'])
                    except:
                        profile['content_categories'] = []
                
                if profile.get('interests'):
                    try:
                        profile['interests'] = json.loads(profile['interests'])
                    except:
                        profile['interests'] = []
                
                return profile
            else:
                # If update failed, try to create the profile first
                profile_data_for_creation = {
                    'id': user_id,
                    'email': 'unknown@example.com',  # We'll update this later
                    'role': 'user',
                    'profile_completed': False,
                    **update_data
                }
                
                response = client.table('user_profiles').insert(profile_data_for_creation).execute()
                
                if response.data and len(response.data) > 0:
                    profile = response.data[0]
                    
                    # Convert JSON fields back to lists
                    if profile.get('content_categories'):
                        try:
                            profile['content_categories'] = json.loads(profile['content_categories'])
                        except:
                            profile['content_categories'] = []
                    
                    if profile.get('interests'):
                        try:
                            profile['interests'] = json.loads(profile['interests'])
                        except:
                            profile['interests'] = []
                    
                    return profile
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            raise e
    
    @classmethod
    async def get_user_profile(cls, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by ID"""
        try:
            client = SupabaseService.get_admin_client()
            
            response = client.table('user_profiles').select('*').eq('id', user_id).execute()
            
            if response.data and len(response.data) > 0:
                profile = response.data[0]
                
                # Convert JSON fields back to lists
                if profile.get('content_categories'):
                    try:
                        profile['content_categories'] = json.loads(profile['content_categories'])
                    except:
                        profile['content_categories'] = []
                
                if profile.get('interests'):
                    try:
                        profile['interests'] = json.loads(profile['interests'])
                    except:
                        profile['interests'] = []
                
                return profile
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            return None 