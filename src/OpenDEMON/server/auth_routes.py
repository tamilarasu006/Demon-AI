import os
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from starlette.responses import RedirectResponse
import httpx

from OpenDEMON.server.auth_models import UserCreate, UserLogin, UserResponse, Token
from OpenDEMON.mongodb import create_user, get_user_by_email, get_user_by_id
from OpenDEMON.server.limiter import auth_limiter, user_limiter, RATELIMIT_AUTH, RATELIMIT_USER

router = APIRouter(prefix="/v1/auth", tags=["auth"])

JWT_SECRET = os.environ.get("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET environment variable is not set!")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

@router.post("/register", response_model=UserResponse)
@auth_limiter.limit(RATELIMIT_AUTH)
async def register(request: Request, user: UserCreate):
    existing = get_user_by_email(user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = hash_password(user.password)
    user_data = {
        "name": user.name,
        "email": user.email,
        "password_hash": hashed_pw,
        "provider": "local"
    }
    
    if not create_user(user_data):
        raise HTTPException(status_code=500, detail="Failed to create user")
        
    created = get_user_by_email(user.email)
    return UserResponse(
        id=str(created["_id"]),
        name=created["name"],
        email=created["email"],
        provider=created["provider"]
    )

@router.get("/me", response_model=UserResponse)
@user_limiter.limit(RATELIMIT_USER)
async def get_current_user(request: Request):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    db_user = get_user_by_id(user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return UserResponse(
        id=str(db_user["_id"]),
        name=db_user["name"],
        email=db_user["email"],
        provider=db_user.get("provider")
    )
@router.post("/login", response_model=Token)
@auth_limiter.limit(RATELIMIT_AUTH)
async def login(request: Request, user: UserLogin):
    db_user = get_user_by_email(user.email)
    if not db_user or "password_hash" not in db_user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    if not verify_password(user.password, db_user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(db_user["_id"])}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/forgot-password")
@auth_limiter.limit(RATELIMIT_AUTH)
async def forgot_password(request: Request):
    # Mock implementation for forgot password
    return {"status": "Recovery signal transmitted"}

@router.post("/otp")
@auth_limiter.limit(RATELIMIT_AUTH)
async def verify_otp(request: Request):
    # Mock implementation for OTP
    return {"status": "Sequence confirmed"}

# --- OAuth Endpoints ---

GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET")

@router.get("/github/login")
@auth_limiter.limit(RATELIMIT_AUTH)
async def github_login(request: Request):
    if not GITHUB_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured")
    redirect_uri = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&scope=user:email"
    return RedirectResponse(redirect_uri)

@router.get("/github/callback")
@auth_limiter.limit(RATELIMIT_AUTH)
async def github_callback(request: Request, code: str):
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured")
        
    async with httpx.AsyncClient() as client:
        # Get access token
        token_res = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code
            }
        )
        token_data = token_res.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get GitHub token")
            
        # Get user info
        user_res = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        github_user = user_res.json()
        
        email_res = await client.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        emails = email_res.json()
        primary_email = next((email["email"] for email in emails if email["primary"]), None)
        
        if not primary_email:
            raise HTTPException(status_code=400, detail="No primary email found")
            
        # Check if user exists
        db_user = get_user_by_email(primary_email)
        if not db_user:
            user_data = {
                "name": github_user.get("name") or github_user.get("login"),
                "email": primary_email,
                "provider": "github",
                "github_id": github_user.get("id")
            }
            create_user(user_data)
            db_user = get_user_by_email(primary_email)
            
        # Generate our JWT
        expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        jwt_token = create_access_token({"sub": str(db_user["_id"])}, expires_delta=expires)
        
        # In a real app we'd redirect back to frontend with the token, for example:
        # return RedirectResponse(f"http://localhost:5173/login/callback?token={jwt_token}")
        return {"access_token": jwt_token, "token_type": "bearer"}
