"""Authentication endpoints for user registration and login."""

import logging
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from app.database import get_database
from app.models.user import TokenResponse, UserCreate, UserLogin, UserResponse
from app.utils.auth import (
    create_access_token,
    get_password_hash,
    validate_password_strength,
    verify_password,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/auth/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    user_data: UserCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Register a new user account.
    
    **Required Fields:**
    - **username**: Unique username (3-50 characters)
    - **email**: Valid email address
    - **phone**: Phone number (10-15 characters)
    - **password**: Strong password (min 8 characters)
    
    **Returns:**
    - JWT access token
    - User information
    
    **Error Codes:**
    - **400**: Invalid input (weak password, invalid format)
    - **409**: User already exists (duplicate username/email/phone)
    - **500**: Internal server error
    """
    try:
        # Validate password strength
        is_valid, error_msg = validate_password_strength(user_data.password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password validation failed: {error_msg}"
            )
        
        # Check if username already exists
        existing_user = await db.users.find_one({"username": user_data.username})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already registered"
            )
        
        # Check if email already exists
        existing_email = await db.users.find_one({"email": user_data.email})
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        # Check if phone already exists
        existing_phone = await db.users.find_one({"phone": user_data.phone})
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Phone number already registered"
            )
        
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Create user document
        user_id = str(uuid.uuid4())
        user_doc = {
            "_id": user_id,
            "username": user_data.username,
            "email": user_data.email,
            "phone": user_data.phone,
            "hashed_password": hashed_password,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": None,
        }
        
        # Insert into database
        try:
            await db.users.insert_one(user_doc)
            logger.info(f"New user registered: {user_data.username}")
        except DuplicateKeyError as e:
            logger.warning(f"Duplicate key error during user registration: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this information already exists"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=1440)  # 24 hours
        access_token = create_access_token(
            data={"user_id": user_id, "username": user_data.username},
            expires_delta=access_token_expires
        )
        
        # Prepare user response
        user_response = UserResponse(**user_doc)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=86400,  # 24 hours in seconds
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during user registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user. Please try again."
        )


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Authenticate user and generate access token.
    
    **Required Fields:**
    - **username**: Username or email address
    - **password**: User password
    
    **Returns:**
    - JWT access token (valid for 24 hours)
    - User information
    
    **Error Codes:**
    - **401**: Invalid credentials
    - **403**: Account is inactive
    - **500**: Internal server error
    """
    try:
        # Find user by username or email
        user_doc = await db.users.find_one({
            "$or": [
                {"username": credentials.username},
                {"email": credentials.username}
            ]
        })
        
        if not user_doc:
            logger.warning(f"Login attempt with non-existent user: {credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Verify password
        if not verify_password(credentials.password, user_doc["hashed_password"]):
            logger.warning(f"Failed login attempt for user: {credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Check if user is active
        if not user_doc.get("is_active", True):
            logger.warning(f"Inactive user login attempt: {credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive. Please contact support."
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=1440)  # 24 hours
        access_token = create_access_token(
            data={"user_id": user_doc["_id"], "username": user_doc["username"]},
            expires_delta=access_token_expires
        )
        
        logger.info(f"User logged in successfully: {user_doc['username']}")
        
        # Prepare user response
        user_response = UserResponse(**user_doc)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=86400,  # 24 hours in seconds
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )


@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Get current authenticated user information.
    
    **Requires:** Valid JWT token in Authorization header
    
    **Returns:**
    - Current user information
    
    **Error Codes:**
    - **401**: Unauthorized (invalid or missing token)
    - **404**: User not found
    - **500**: Internal server error
    """
    # This endpoint will be protected by the authentication middleware
    # For now, return a placeholder
    # This will be properly implemented when we apply auth to routes
    from app.middleware.auth import get_current_user
    from fastapi.security import HTTPBearer
    
    security = HTTPBearer()
    
    async def protected_endpoint(
        current_user: UserResponse = Depends(get_current_user),
    ):
        return current_user
    
    return await protected_endpoint()


