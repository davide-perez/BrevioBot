from typing import Optional
from pydantic import BaseModel

class User(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    password: Optional[str] = None

    def __str__(self) -> str:
        return f"User(id={self.id}, username='{self.username}', email='{self.email}')"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active
        }

    model_config = {"from_attributes": True}