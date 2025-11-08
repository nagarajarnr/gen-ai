"""Authentication middleware and dependencies."""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.models.user import User, UserResponse
from app.utils.auth import decode_access_token

logger = logging.getLogger(__name__)

# Security scheme for JWT Bearer token
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> UserResponse:
    """
    Dependency to get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials with JWT token
        db: Database connection
        
    Returns:
        Current user information
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_expired_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token has expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    
    # Decode token
    payload = decode_access_token(token)
    if payload is None:
        logger.warning("Invalid token provided")
        raise credentials_exception
    
    # Check if token is expired
    from datetime import datetime
    exp = payload.get("exp")
    if exp:
        exp_datetime = datetime.fromtimestamp(exp)
        if exp_datetime < datetime.utcnow():
            logger.warning("Expired token used")
            raise token_expired_exception
    
    # Get user ID from token
    user_id: str = payload.get("user_id")
    if user_id is None:
        logger.warning("Token missing user_id")
        raise credentials_exception
    
    # Fetch user from database
    try:
        user_doc = await db.users.find_one({"_id": user_id})
        if user_doc is None:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user is active
        if not user_doc.get("is_active", True):
            logger.warning(f"Inactive user attempted access: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # Convert to UserResponse
        user = UserResponse(**user_doc)
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


async def get_current_active_user(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """
    Dependency to ensure user is active.
    
    Args:
        current_user: Current user from token
        
    Returns:
        Active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> Optional[UserResponse]:
    """
    Optional authentication - returns user if token provided, None otherwise.
    
    Args:
        credentials: Optional HTTP Bearer credentials
        db: Database connection
        
    Returns:
        User if authenticated, None otherwise
    """
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        payload = decode_access_token(token)
        if payload is None:
            return None
        
        user_id = payload.get("user_id")
        if user_id is None:
            return None
        
        user_doc = await db.users.find_one({"_id": user_id})
        if user_doc is None or not user_doc.get("is_active", True):
            return None
        
        return UserResponse(**user_doc)
    except Exception as e:
        logger.debug(f"Optional auth failed: {e}")
        return None


