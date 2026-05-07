from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, unique=False, nullable=False)
    inventory: Mapped[list[Inventory]] = relationship(back_populates="owner", cascade="all, delete-orphan")


# class Inventory(Base):
#     __tablename__ = "inventory"
#     id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
#     user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
#     product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
#     quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String, unique=False, nullable=True)
    cost: Mapped[float] = mapped_column(Float, unique=False, nullable=False)


class PasswordResetToken(Base):
    __tablename__ = "password_tokens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    reset_token: Mapped[str | None] = mapped_column(String, nullable=False)
    reset_token_expires: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=False)
                                