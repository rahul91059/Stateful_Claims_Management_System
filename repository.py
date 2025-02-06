#repository.py
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase

# Modify type variable to extend DeclarativeBase
T = TypeVar('T', bound=DeclarativeBase)

class PostgresRepository(Generic[T]):
    """Generic repository for handling database operations with PostgreSQL"""
    
    def __init__(self, session: AsyncSession, model: Type[T]):
        """
        Initialize repository with session and model
        
        Args:
            session: AsyncSession - SQLAlchemy async session
            model: Type[T] - SQLAlchemy model class that extends DeclarativeBase
        """
        self._session = session
        self._model = model

    async def create(self, entity: T) -> T:
        """
        Create a new entity in the database
        
        Args:
            entity: T - Entity to create
            
        Returns:
            T - Created entity
            
        Raises:
            ValueError: If creation fails
        """
        try:
            if hasattr(entity, 'created_at'):
                setattr(entity, 'created_at', datetime.now(timezone.utc))
            
            self._session.add(entity)
            await self._session.flush()
            await self._session.refresh(entity)
            return entity
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise ValueError(f"Failed to create entity: {str(e)}")

    async def read(self, id: UUID) -> Optional[T]:
        """
        Read an entity by its ID
        
        Args:
            id: UUID - Entity ID
            
        Returns:
            Optional[T] - Found entity or None
            
        Raises:
            ValueError: If read operation fails
        """
        try:
            stmt = select(self._model).where(self._model.id == id)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise ValueError(f"Failed to read entity: {str(e)}")

    async def update(self, entity: T) -> Optional[T]:
        """
        Update an existing entity
        
        Args:
            entity: T - Entity to update
            
        Returns:
            Optional[T] - Updated entity or None
            
        Raises:
            ValueError: If update fails
        """
        try:
            if hasattr(entity, 'updated_at'):
                setattr(entity, 'updated_at', datetime.now(timezone.utc))
            
            merged_entity = self._session.merge(entity)
            await self._session.flush()
            await self._session.refresh(merged_entity)
            return merged_entity
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise ValueError(f"Failed to update entity: {str(e)}")

    async def delete(self, id: UUID) -> bool:
        """
        Delete an entity by its ID
        
        Args:
            id: UUID - Entity ID
            
        Returns:
            bool - True if deleted, False if not found
            
        Raises:
            ValueError: If deletion fails
        """
        try:
            stmt = delete(self._model).where(self._model.id == id)
            result = await self._session.execute(stmt)
            await self._session.flush()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            await self._session.rollback()
            raise ValueError(f"Failed to delete entity: {str(e)}")

    async def list_all(self) -> List[T]:
        """
        List all entities
        
        Returns:
            List[T] - List of all entities
            
        Raises:
            ValueError: If listing fails
        """
        try:
            stmt = select(self._model)
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise ValueError(f"Failed to list entities: {str(e)}")

    async def find_by_field(self, field: str, value: Any) -> List[T]:
        """
        Find entities by a specific field value
        
        Args:
            field: str - Field name to search by
            value: Any - Value to search for
            
        Returns:
            List[T] - List of matching entities
            
        Raises:
            ValueError: If search fails or field doesn't exist
        """
        try:
            if not hasattr(self._model, field):
                raise ValueError(f"Field '{field}' does not exist on model {self._model.__name__}")
            
            stmt = select(self._model).where(getattr(self._model, field) == value)
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise ValueError(f"Failed to find entities by field: {str(e)}")

    async def exists(self, id: UUID) -> bool:
        """
        Check if an entity exists by its ID
        
        Args:
            id: UUID - Entity ID to check
            
        Returns:
            bool - True if exists, False otherwise
            
        Raises:
            ValueError: If check fails
        """
        try:
            stmt = select(self._model).where(self._model.id == id)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError as e:
            raise ValueError(f"Failed to check entity existence: {str(e)}")

    async def count(self) -> int:
        """
        Count total number of entities
        
        Returns:
            int - Total count of entities
            
        Raises:
            ValueError: If count fails
        """
        try:
            stmt = select(self._model)
            result = await self._session.execute(stmt)
            return len(result.scalars().all())
        except SQLAlchemyError as e:
            raise ValueError(f"Failed to count entities: {str(e)}")

    async def find_by_fields(self, filters: Dict[str, Any]) -> List[T]:
        """
        Find entities matching multiple field criteria
        
        Args:
            filters: Dict[str, Any] - Dictionary of field names and values to filter by
            
        Returns:
            List[T] - List of matching entities
            
        Raises:
            ValueError: If search fails or any field doesn't exist
        """
        try:
            conditions = []
            for field, value in filters.items():
                if not hasattr(self._model, field):
                    raise ValueError(f"Field '{field}' does not exist on model {self._model.__name__}")
                conditions.append(getattr(self._model, field) == value)
            
            stmt = select(self._model).where(*conditions)
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise ValueError(f"Failed to find entities by fields: {str(e)}")