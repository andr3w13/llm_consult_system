from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100, examples=["john_doe"])
    email: EmailStr = Field(..., examples=["john@example.com"])
    password: str = Field(..., min_length=6, examples=["secret123"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
