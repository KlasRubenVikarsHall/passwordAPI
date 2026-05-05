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


class Token(BaseModel):
    access_token: str
    token_type:  str
    