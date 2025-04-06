from pydantic import BaseModel, EmailStr
from typing import Optional, List


# User models (without any farm field)
class UserRegistration(BaseModel):
    user_id: Optional[int]
    email: EmailStr
    name: str

class UserCreate(BaseModel):
    password: str
    email: EmailStr
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    units: Optional[str] = None