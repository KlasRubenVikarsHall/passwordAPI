from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.exceptions import HTTPException as StarletteHTTPException

import models
from schemas import UserCreate, UserPrivate, UserPublic
from database import Base, engine, get_db


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
    return {"Hello": "World"}


@api.get("/Users")
async def get_all_users():
    pass


@api.post("/Users", 
          response_model=UserPrivate, 
          status_code=status.HTTP_201_CREATED
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
        hashed_password=user.password # TODO:Hash
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user
    


@api.get("/Users/{user_id}")
async def get_user(user_id: int):
    pass


@api.delete("/Users/{user_id}")
async def delete_user(user_id: int):
    pass
