from contextlib import asynccontextmanager
from typing import Annotated
from datetime import UTC, datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exception_handlers import http_exception_handler
from sqlalchemy import select, func
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException as StarletteHTTPException

from config import settings
import models
from schemas import (UserCreate, 
                     UserPrivate, 
                     UserPublic, 
                     Token, 
                     ForgotPasswordResponse, 
                     ResetPasswordRequest, 
                     ForgotPasswordRequest, 
                     UserUpdate,
                     ProductPublic,
)
from database import Base, engine, get_db
from auth import verify_password, create_access_token, hash_password, CurrentUser, create_reset_token


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


api = FastAPI(lifespan=lifespan)


@api.get("/")
async def home():
    return {"Visit": "/docs"}


@api.get("/Users",response_model=list[UserPublic])
async def get_all_users(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User)
    )
    user_list = result.scalars().all()
    return user_list


@api.post("/Users", 
          response_model=UserPrivate, 
          status_code=status.HTTP_201_CREATED,
)
async def create_user(
    user: UserCreate, 
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(models.User).where(models.User.username == user.username)
    )
    old_user = result.scalars().first()
    if old_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Username already taken")
    new_user = models.User(
        username=user.username,
        email=user.email.lower(),
        hashed_password=hash_password(user.password)
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@api.get("/Users/Me", response_model=UserPrivate)
async def get_me(current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    return current_user


# @api.post("/Users/Me/Inventory", response_model=UserPrivate)
# async def get_me(body: ,current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
#     return current_user



@api.patch("/Users/{user_id}", response_model=UserPrivate)
async def update_user(user_id: int, current_user: CurrentUser, body: UserUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized to update user"
        )
    if body.email:
        current_user.email = body.email
    if body.username:
        current_user.username = body.username
    await db.commit()
    await db.refresh(current_user)
    return current_user


@api.get("/Users/{user_id}", response_model=UserPublic)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")
    return user


@api.delete("/Users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized to delete user"
        )
    
    result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")
    await db.delete(user)
    await db.commit()


@api.post("/Users/Token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(models.User).where(
            models.User.email == form_data.username,
        ),
    )

    user = result.scalars().first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # create access token
    time_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=time_expires,
    )
    return Token(access_token=access_token, token_type="bearer")


@api.post("/Users/ForgotPassword", response_model=ForgotPasswordResponse)
async def forgot_password(
    given_email: ForgotPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(models.User).where(given_email.email.lower() == models.User.email)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")
    
    # Create a token for pw reset (call auth method)
    token = models.PasswordResetToken(
        reset_token=create_reset_token(), 
        reset_token_expires=datetime.now(UTC) + timedelta(minutes=5),
        email=given_email.email,
    )
    db.add(token)
    await db.commit()
    await db.refresh(token)
    return ForgotPasswordResponse(mock_reset_token=token.reset_token)


@api.patch("/Users/ResetPassword", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    body: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(models.PasswordResetToken).where(
            models.PasswordResetToken.reset_token == body.token
        )
    )
    token_result = result.scalars().first()
    if not token_result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Invalid token")
    
    if token_result.reset_token_expires < datetime.now(UTC):
        await db.delete(token_result)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Reset token has expired")

    result = await db.execute(
        select(models.User).where(
            models.User.email == token_result.email
        )
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")

    user.hashed_password = hash_password(body.new_password)
    
    await db.delete(token_result)
    await db.commit()


@api.get("/products", response_model=list[ProductPublic])
async def list_all_products(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Product)
    )
    products = result.scalars().all()
    
    if not products:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="No products found")
    return products


# @api.get("/products/{product_id}", response_model=ProductPublic)
# async def show_product(product_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
#     pass


# @api.post("/products/{product_id}", response_model=ProductPublic)
# async def purchase_product(product_id: int, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
#     pass


@api.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(
    request: Request,
    exception: StarletteHTTPException,
):
    print(f"{request.method} {request.url} → {exception.status_code}")
    return await http_exception_handler(request, exception)
