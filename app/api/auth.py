from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..services.supabase import SupabaseService
from ..middleware.auth import get_current_user, require_role
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

@router.post("/signup")
async def signup(user_data: dict):
    try:
        email = user_data.get("email")
        password = user_data.get("password") 
        role = user_data.get("role", "user")
        
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password required")
            
        logger.info(f"Signup attempt for email: {email}")
        user = await SupabaseService.sign_up(email, password, role)
        
        return {
            "id": user.user.id,
            "email": user.user.email,
            "role": role,
            "message": "User created successfully"
        }
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(user_data: dict):
    try:
        email = user_data.get("email")
        password = user_data.get("password")
        
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password required")
            
        logger.info(f"Login attempt for email: {email}")
        auth_response = await SupabaseService.sign_in(email, password)
        
        return {
            "access_token": auth_response.session.access_token,
            "token_type": "bearer",
            "user": {
                "id": auth_response.user.id,
                "email": auth_response.user.email,
                "role": "user"
            }
        }
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/google")
async def google_auth(token: dict):
    """Handle Google OAuth token from frontend"""
    try:
        google_token = token.get("access_token")
        if not google_token:
            raise HTTPException(status_code=400, detail="Google access token required")
        
        # Exchange Google token with Supabase
        auth_response = await SupabaseService.sign_in_with_oauth_token("google", google_token)
        
        return {
            "access_token": auth_response.session.access_token,
            "token_type": "bearer",
            "user": {
                "id": auth_response.user.id,
                "email": auth_response.user.email or "",
                "role": auth_response.user.user_metadata.get("role", "user")
            }
        }
    except Exception as e:
        logger.error(f"Google auth error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/google/callback")
async def google_oauth_callback(callback_data: dict):
    """Handle Google OAuth callback with authorization code"""
    try:
        logger.info(f"Received callback data: {callback_data}")
        
        # Handle both 'code' and 'access_token' for flexibility
        code = callback_data.get("code")
        access_token = callback_data.get("access_token")
        
        if access_token:
            # If we receive an access token directly, use it
            logger.info("Processing access token directly")
            auth_response = await SupabaseService.sign_in_with_oauth_token("google", access_token)
        elif code:
            # If we receive a code, try to exchange it
            logger.info(f"Processing Google OAuth callback with code: {code[:10]}...")
            auth_response = await SupabaseService.exchange_oauth_code("google", code)
        else:
            raise HTTPException(status_code=400, detail="Authorization code or access token required")
        
        return {
            "access_token": auth_response.session.access_token,
            "token_type": "bearer",
            "user": {
                "id": auth_response.user.id,
                "email": auth_response.user.email or "",
                "role": auth_response.user.user_metadata.get("role", "user")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google OAuth callback error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/google/url")
async def get_google_auth_url():
    """Get Google OAuth URL for frontend redirect (implicit flow)"""
    try:
        auth_url = SupabaseService.get_oauth_url("google", "http://localhost:3000/auth/callback")
        return {"url": auth_url}
    except Exception as e:
        logger.error(f"Error getting Google auth URL: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get auth URL")

@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        await SupabaseService.sign_out(credentials.credentials)
        return {"message": "Logged out successfully"}
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "role": current_user.get("role", "user")
    }

@router.post("/update-role")
async def update_user_role(role_data: dict, current_user: dict = Depends(get_current_user)):
    """Update user role - typically for new OAuth users"""
    try:
        new_role = role_data.get("role")
        user_id = role_data.get("user_id") or current_user["id"]
        
        if not new_role:
            raise HTTPException(status_code=400, detail="Role is required")
        
        if new_role not in ["user", "influencer", "brand", "admin"]:
            raise HTTPException(status_code=400, detail="Invalid role")
            
        logger.info(f"Updating role for user {user_id} to {new_role}")
        
        # Update user metadata in Supabase
        updated_user = await SupabaseService.update_user_metadata(user_id, {"role": new_role})
        
        return {
            "id": user_id,
            "email": current_user["email"],
            "role": new_role,
            "message": "Role updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update role error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Protected routes examples
@router.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {"message": "Protected route access granted", "user": current_user}

@router.get("/admin-only")
async def admin_only(current_user: dict = Depends(require_role("admin"))):
    return {"message": "Admin access granted", "user": current_user}

@router.get("/influencer-only")
async def influencer_only(current_user: dict = Depends(require_role("influencer"))):
    return {"message": "Influencer access granted", "user": current_user} 