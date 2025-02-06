import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from contextlib import asynccontextmanager
from typing import AsyncGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get DATABASE_URL from environment variable with fallback to local development URL
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    "postgresql+asyncpg://postgres:4i$TEM1234@localhost/claims_db1"
)

# Replace postgres:// with postgresql:// for SQLAlchemy compatibility
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Log database connection attempt (without sensitive info)
logger.info(f"Attempting to connect to database at: {DATABASE_URL.split('@')[-1]}")

# Create async engine with error handling
try:
    engine = create_async_engine(
        DATABASE_URL,
        echo=True,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10
    )
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {str(e)}")
    raise

# Create async session maker
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Create base class for declarative models
Base = declarative_base()

@asynccontextmanager
async def get_session() -> AsyncSession:
    """
    Async context manager for database sessions
    """
    async with async_session_maker() as session:
        try:
            logger.debug("Database session created")
            yield session
        except Exception as e:
            logger.error(f"Database session error: {str(e)}")
            await session.rollback()
            raise
        finally:
            logger.debug("Database session closed")
            await session.close()

# Function to get a new session
async def get_db_session():
    async with async_session_maker() as session:
        yield session

# Optional: Add health check function
async def check_database_connection() -> bool:
    """
    Check if database connection is working
    """
    try:
        async with async_session_maker() as session:
            await session.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return False