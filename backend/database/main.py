from asyncio import run
from database.driver import engine
from models import Base

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

run(main())