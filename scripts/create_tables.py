import asyncio

from shared.db.session import engine
from shared.db.base import Base

from shared.db.models.document import Document
from shared.db.models.chunk import Chunk


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

asyncio.run(main())
