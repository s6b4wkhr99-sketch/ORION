"""Volume 14 — System administration API schemas."""

from pydantic import BaseModel, EmailStr, Field


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12)
    name: str = Field(min_length=1, max_length=128)
    role: str


class UserRoleRequest(BaseModel):
    role: str


class UserPasswordRequest(BaseModel):
    password: str = Field(min_length=12)
