# in_memory_repository.py
from typing import Dict, Optional, List, TypeVar, Generic
from uuid import UUID
from datetime import datetime

T = TypeVar('T')

class InMemoryRepository(Generic[T]):
    def __init__(self):
        self._storage: Dict[UUID, T] = {}
        
    async def create(self, entity: T) -> T:
        if hasattr(entity, 'id'):
            if entity.id in self._storage:
                raise ValueError(f"Entity with ID {entity.id} already exists")
            self._storage[entity.id] = entity
        return entity

    async def read(self, id: UUID) -> Optional[T]:
        return self._storage.get(id)

    async def update(self, entity: T) -> T:
        if not hasattr(entity, 'id') or entity.id not in self._storage:
            raise ValueError(f"Entity not found")
        if hasattr(entity, 'updated_at'):
            entity.updated_at = datetime.now()
        self._storage[entity.id] = entity
        return entity

    async def delete(self, id: UUID) -> bool:
        if id in self._storage:
            del self._storage[id]
            return True
        return False

    async def list_all(self) -> List[T]:
        return list(self._storage.values())