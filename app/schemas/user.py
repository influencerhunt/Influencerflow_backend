from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    BRAND = "brand"
    INFLUENCER = "influencer"


class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None
    role: Optional[UserRole] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    
    # Social media handles
    social_instagram: Optional[str] = None
    social_tiktok: Optional[str] = None
    social_youtube: Optional[str] = None
    social_twitter: Optional[str] = None
    
    # Influencer-specific fields
    experience_level: Optional[str] = None
    content_categories: Optional[List[str]] = None
    
    # Brand-specific fields
    company: Optional[str] = None
    budget_range: Optional[str] = None
    
    # Common fields
    interests: Optional[List[str]] = None


class UserProfile(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    role: UserRole
    profile_completed: bool = False
    
    # Profile information
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    
    # Social media handles
    social_instagram: Optional[str] = None
    social_tiktok: Optional[str] = None
    social_youtube: Optional[str] = None
    social_twitter: Optional[str] = None
    
    # Influencer-specific fields
    experience_level: Optional[str] = None
    content_categories: Optional[List[str]] = None
    
    # Brand-specific fields
    company: Optional[str] = None
    budget_range: Optional[str] = None
    
    # Common fields
    interests: Optional[List[str]] = None
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class User(UserProfile):
    pass


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None 