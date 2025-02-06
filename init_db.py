import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from models import Base  # Import your models
from database import DATABASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_db():
    try:
        engine = create_async_engine(DATABASE_URL, echo=True)
        
        async with engine.begin() as conn:
            logger.info("Dropping all tables...")
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("Creating all tables...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database initialization completed successfully")
        
        await engine.dispose()
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(init_db())