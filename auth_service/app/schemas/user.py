from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserPublic(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}
