from typing import Optional
from pydantic import Field
from OpenDEMON.server.models import StrictBaseModel

class UserCreate(StrictBaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=3, max_length=255, pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    password: str = Field(..., min_length=8, max_length=255)

class UserLogin(StrictBaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=255)

class UserResponse(StrictBaseModel):
    id: str
    name: str
    email: str
    provider: Optional[str] = None

class Token(StrictBaseModel):
    access_token: str
    token_type: str
