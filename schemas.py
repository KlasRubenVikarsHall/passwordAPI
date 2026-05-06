from pydantic import BaseModel, ConfigDict, Field, EmailStr
from datetime import datetime


class UserBase(BaseModel):
    username: str = Field(min_length=5, max_length=20)


class UserCreate(UserBase):
    password: str = Field(min_length=6)
    email: EmailStr = Field(min_length=6, max_length=30)


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:int
    username: str


class UserPrivate(UserPublic):
    email: EmailStr = Field(min_length=6, max_length=30)


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr | None = Field(default=None, max_length=120)


class Token(BaseModel):
    access_token: str
    token_type:  str
    

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

    
class ForgotPasswordResponse(BaseModel):
    mock_reset_token: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=6)
