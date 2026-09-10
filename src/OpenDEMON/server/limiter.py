from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
import os

def get_auth_key(request: Request) -> str:
    """Rate limit Auth endpoints by IP + account identity."""
    ip = get_remote_address(request)
    identity = "anonymous"
    # Attempt to extract email or user id from body or headers for auth limits
    try:
        # If it's a login/register request, we might find email in JSON body.
        # But reading request.json() here in a sync function might be tricky,
        # so we rely on IP mostly, and if logged in, User ID.
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            identity = str(user_id)
    except Exception:
        pass
    return f"{ip}:{identity}"

def get_user_key(request: Request) -> str:
    """Rate limit authenticated actions by User ID."""
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    return get_remote_address(request)

# Extract config or default limits
RATELIMIT_PUBLIC = os.environ.get("RATELIMIT_PUBLIC", "60/minute")
RATELIMIT_AUTH = os.environ.get("RATELIMIT_AUTH", "5/minute")
RATELIMIT_USER = os.environ.get("RATELIMIT_USER", "120/minute")

# Multiple limiter instances or key functions
limiter = Limiter(key_func=get_remote_address)
auth_limiter = Limiter(key_func=get_auth_key)
user_limiter = Limiter(key_func=get_user_key)

