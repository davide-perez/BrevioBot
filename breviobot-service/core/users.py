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

    model_config = {"from_attributes": True}