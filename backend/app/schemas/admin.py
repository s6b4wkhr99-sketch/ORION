"""Volume 14 — System administration API schemas."""

from pydantic import BaseModel, EmailStr, Field


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12)
    name: str = Field(min_length=1, max_length=128)
    role: str
    allowed_modules: list[str] | None = Field(default=None, alias="allowedModules")

    model_config = {"populate_by_name": True}


class UserRoleRequest(BaseModel):
    role: str


class UserUpdateRequest(BaseModel):
    email: EmailStr | None = None
    name: str | None = Field(default=None, min_length=1, max_length=128)
    role: str | None = None
    allowed_modules: list[str] | None = Field(default=None, alias="allowedModules")
    menu_access_mode: str | None = Field(default=None, alias="menuAccessMode")

    model_config = {"populate_by_name": True}


class UserPasswordRequest(BaseModel):
    password: str = Field(min_length=12)
