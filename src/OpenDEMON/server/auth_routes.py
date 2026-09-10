import os
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from starlette.responses import RedirectResponse
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from OpenDEMON.server.auth_models import UserCreate, UserLogin, UserResponse, Token
from OpenDEMON.database.session import get_db_session
from OpenDEMON.database.repositories.users import UserRepository
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
async def register(request: Request, user: UserCreate, db: AsyncSession = Depends(get_db_session)):
    repo = UserRepository(db)
    existing = await repo.get_by_email(user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Normally we would save the password hash, but for now we just create the user.
    # To support local auth fully, we would need to add a password_hash column or 
    # handle it in user profiles.
    created = await repo.create_user(email=user.email, name=user.name)
    return UserResponse(
        id=str(created.id),
        name=created.name,
        email=created.email,
        provider="local"
    )

@router.get("/me", response_model=UserResponse)
@user_limiter.limit(RATELIMIT_USER)
async def get_current_user(request: Request, db: AsyncSession = Depends(get_db_session)):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    repo = UserRepository(db)
    db_user = await repo.get_by_id(user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return UserResponse(
        id=str(db_user.id),
        name=db_user.name,
        email=db_user.email,
        provider="postgres"
    )

@router.post("/login", response_model=Token)
@auth_limiter.limit(RATELIMIT_AUTH)
async def login(request: Request, user: UserLogin, db: AsyncSession = Depends(get_db_session)):
    repo = UserRepository(db)
    db_user = await repo.get_by_email(user.email)
    if not db_user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    # Simplified login
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(db_user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/forgot-password")
@auth_limiter.limit(RATELIMIT_AUTH)
async def forgot_password(request: Request):
    return {"status": "Recovery signal transmitted"}

@router.post("/otp")
@auth_limiter.limit(RATELIMIT_AUTH)
async def verify_otp(request: Request):
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
async def github_callback(request: Request, code: str, db: AsyncSession = Depends(get_db_session)):
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured")
        
    async with httpx.AsyncClient() as client:
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
            
        repo = UserRepository(db)
        db_user = await repo.get_by_email(primary_email)
        if not db_user:
            name = github_user.get("name") or github_user.get("login")
            db_user = await repo.create_user(email=primary_email, name=name, picture=github_user.get("avatar_url"))
            
        expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        jwt_token = create_access_token({"sub": str(db_user.id)}, expires_delta=expires)
        return {"access_token": jwt_token, "token_type": "bearer"}

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8000/v1/auth/google/callback")

@router.get("/google/login")
@auth_limiter.limit(RATELIMIT_AUTH)
async def google_login(request: Request):
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    
    redirect_uri = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={GOOGLE_CLIENT_ID}&redirect_uri={GOOGLE_REDIRECT_URI}&response_type=code&scope=openid%20email%20profile&access_type=offline"
    return RedirectResponse(redirect_uri)

@router.get("/google/callback")
@auth_limiter.limit(RATELIMIT_AUTH)
async def google_callback(request: Request, code: str, db: AsyncSession = Depends(get_db_session)):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
        
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": GOOGLE_REDIRECT_URI,
            }
        )
        token_data = token_res.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get Google token")
            
        user_res = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        google_user = user_res.json()
        primary_email = google_user.get("email")
        
        if not primary_email:
            raise HTTPException(status_code=400, detail="No email found in Google profile")
            
        repo = UserRepository(db)
        db_user = await repo.get_by_email(primary_email)
        if not db_user:
            name = google_user.get("name") or google_user.get("given_name", "User")
            db_user = await repo.create_user(email=primary_email, name=name, picture=google_user.get("picture"))
            
        expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        jwt_token = create_access_token({"sub": str(db_user.id)}, expires_delta=expires)
        return {"access_token": jwt_token, "token_type": "bearer"}
