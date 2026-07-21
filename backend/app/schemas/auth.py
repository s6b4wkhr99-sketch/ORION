from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenData(BaseModel):
    token: str
    expires: str


class RefreshRequest(BaseModel):
    token: str
