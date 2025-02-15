from database import engine

async def test_connection():
    async with engine.begin() as conn:
        print("PostgreSQL connection successful!")

import asyncio
asyncio.run(test_connection())
