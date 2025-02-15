# schemas.py

from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        orm_mode = True  # Allows compatibility with ORM objects
