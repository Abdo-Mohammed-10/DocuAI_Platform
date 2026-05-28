import asyncio

from shared.db.base import Base
from shared.db.session import engine


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


asyncio.run(main())
