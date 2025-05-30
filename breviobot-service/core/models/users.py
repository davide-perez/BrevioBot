from typing import Optional
from pydantic import BaseModel

class User(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False
    password: Optional[str] = None

    def __str__(self) -> str:
        return f"User(id={self.id}, username='{self.username}', email='{self.email}')"

    def get_role(self) -> str:
        return "admin" if self.is_admin else "user"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "role": self.get_role(),
        }

    model_config = {"from_attributes": True}