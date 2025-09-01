"""
Authentication middleware for FastAPI using Supabase Auth.
"""

import os
import logging
from typing import Optional
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client
from utils.supabase_config import get_supabase_client

logger = logging.getLogger(__name__)

# HTTP Bearer security scheme
security = HTTPBearer()


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verify the JWT token using Supabase Auth.
    
    Args:
        credentials: HTTP Bearer credentials containing the JWT token
        
    Returns:
        User data from the verified token
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
    try:
        # Get Supabase client
        supabase: Client = get_supabase_client()
        
        # Verify the token
        user = supabase.auth.get_user(token)
        
        if not user or not user.user:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials"
            )
        
        return {
            "user_id": user.user.id,
            "email": user.user.email,
            "user_metadata": user.user.user_metadata
        }
        
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials"
        )


async def get_current_user(user_data: dict = Depends(verify_token)) -> dict:
    """
    Get the current authenticated user.
    
    Args:
        user_data: User data from verified token
        
    Returns:
        Current user information
    """
    return user_data


async def optional_auth(request: Request) -> Optional[dict]:
    """
    Optional authentication - returns user data if authenticated, None otherwise.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User data if authenticated, None otherwise
    """
    authorization = request.headers.get("Authorization")
    logger.info(f"🔐 Optional auth called. Authorization header: {authorization[:50] if authorization else 'None'}...")
    
    if not authorization:
        logger.info("⚠️ No Authorization header found")
        return None
    
    try:
        # Extract token from Authorization header
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
        
        # Get Supabase client
        supabase: Client = get_supabase_client()
        
        # Verify the token
        user = supabase.auth.get_user(token)
        
        if user and user.user:
            user_data = {
                "user_id": user.user.id,
                "email": user.user.email,
                "user_metadata": user.user.user_metadata
            }
            logger.info(f"✅ 成功认证用户: {user.user.email}")
            return user_data
        else:
            logger.warning("⚠️ Supabase返回的用户信息为空")
        
    except Exception as e:
        logger.warning(f"❌ Optional auth失败: {str(e)}")
    
    return None


