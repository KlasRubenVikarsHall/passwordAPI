from pydantic import BaseModel, ConfigDict, Field, EmailStr


EMAIL_MIN_LENGTH = 5
EMAIL_MAX_LENGTH = 30
USERNAME_MIN_LENGTH = 5
USERNAME_MAX_LENGTH = 20
PASSWORD_MIN_LENGTH = 6


class UserBase(BaseModel):
    username: str = Field(min_length=USERNAME_MIN_LENGTH, max_length=USERNAME_MAX_LENGTH)


class UserCreate(UserBase):
    password: str = Field(min_length=PASSWORD_MIN_LENGTH)
    email: EmailStr = Field(min_length=EMAIL_MIN_LENGTH, max_length=30)


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:int
    username: str


class UserPrivate(UserPublic):
    email: EmailStr = Field(min_length=EMAIL_MIN_LENGTH, max_length=EMAIL_MAX_LENGTH)


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=USERNAME_MIN_LENGTH, max_length=USERNAME_MAX_LENGTH)
    email: EmailStr | None = Field(default=None, min_length=EMAIL_MIN_LENGTH, max_length=EMAIL_MAX_LENGTH)


class Token(BaseModel):
    access_token: str
    token_type:  str
    

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

    
class ForgotPasswordResponse(BaseModel):
    mock_reset_token: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=PASSWORD_MIN_LENGTH)


class ProductPublic(BaseModel):
    product_name: str = Field(default=None, min_length=1, max_length=50)
    description: str | None = Field(default=None, min_length=1, max_length=100)
    cost: float


# class InventoryItemPublic(BaseModel):
#     model_config = ConfigDict(from_attributes=True)
#     product_id: int
#     quantity: int

