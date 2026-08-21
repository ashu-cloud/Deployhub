import asyncio
from app.core.db import engine, Base

async def main():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Upload Service Setup Success")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(main())
