import asyncio
from database import engine, Base, AsyncSessionLocal
import models

products = [
    {"product_name": "Paper", "description": "Standard A4 sheet of paper", "cost": 10},
    {"product_name": "Ink pen", "description": None, "cost": 25},
]

async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        db.add_all([models.Product(**p) for p in products])
        await db.commit()

asyncio.run(seed())
