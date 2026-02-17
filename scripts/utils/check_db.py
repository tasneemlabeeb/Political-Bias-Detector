import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check_tables():
    engine = create_async_engine(
        'postgresql+asyncpg://neondb_owner:npg_wThFDGHI1lt3@ep-quiet-rice-aij9k4rx-pooler.c-4.us-east-1.aws.neon.tech/neondb',
        connect_args={'ssl': True}
    )
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        tables = [row[0] for row in result]
        print('Tables in Neon PostgreSQL:')
        for table in tables:
            print(f'  - {table}')
        
        # Count sources if table exists
        if 'news_sources' in tables:
            result = await conn.execute(text('SELECT COUNT(*) FROM news_sources'))
            count = result.scalar()
            print(f'\nNumber of news sources: {count}')
    await engine.dispose()

asyncio.run(check_tables())
