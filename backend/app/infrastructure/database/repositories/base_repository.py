"""
Base Repository Pattern Implementation
Provides common database operations for all repositories.
"""
from typing import TypeVar, Generic, List, Optional, Dict, Any
from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.sql import Select

from ....models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType], ABC):
    """Base repository class providing common database operations."""

    def __init__(self, session: AsyncSession, model: type[ModelType]):
        """Initialize repository with database session and model."""
        self.session = session
        self.model = model

    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """Get a record by its ID."""
        stmt = select(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> List[ModelType]:
        """Get all records with optional filtering and pagination."""
        stmt = select(self.model)

        # Apply filters
        if filters:
            stmt = self._apply_filters(stmt, filters)

        # Apply ordering
        if order_by:
            if hasattr(self.model, order_by):
                stmt = stmt.order_by(getattr(self.model, order_by))

        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filters."""
        from sqlalchemy import func

        stmt = select(func.count()).select_from(self.model)

        if filters:
            stmt = self._apply_filters(stmt, filters)

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def create(self, **kwargs) -> ModelType:
        """Create a new record."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def update(self, id: UUID, **kwargs) -> Optional[ModelType]:
        """Update a record by ID."""
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**kwargs)
            .execution_options(synchronize_session="evaluate")
        )

        await self.session.execute(stmt)
        await self.session.commit()

        # Return updated record
        return await self.get_by_id(id)

    async def delete(self, id: UUID) -> bool:
        """Delete a record by ID."""
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def soft_delete(self, id: UUID) -> bool:
        """Soft delete a record if it has is_deleted field."""
        if hasattr(self.model, 'is_deleted'):
            from datetime import datetime
            update_data = {'is_deleted': True, 'deleted_at': datetime.utcnow()}
            result = await self.update(id, **update_data)
            return result is not None
        return False

    async def exists(self, **kwargs) -> bool:
        """Check if a record exists with given conditions."""
        stmt = select(self.model)

        for key, value in kwargs.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)

        result = await self.session.execute(stmt)
        return result.first() is not None

    def _apply_filters(self, stmt: Select, filters: Dict[str, Any]) -> Select:
        """Apply filters to a query statement."""
        for key, value in filters.items():
            if hasattr(self.model, key):
                if isinstance(value, list):
                    stmt = stmt.where(getattr(self.model, key).in_(value))
                elif isinstance(value, dict):
                    # Handle operators like {"gte": 10, "lte": 20}
                    for op, val in value.items():
                        column = getattr(self.model, key)
                        if op == "gte":
                            stmt = stmt.where(column >= val)
                        elif op == "lte":
                            stmt = stmt.where(column <= val)
                        elif op == "gt":
                            stmt = stmt.where(column > val)
                        elif op == "lt":
                            stmt = stmt.where(column < val)
                        elif op == "like":
                            stmt = stmt.where(column.like(f"%{val}%"))
                        elif op == "ilike":
                            stmt = stmt.where(column.ilike(f"%{val}%"))
                        elif op == "ne":
                            stmt = stmt.where(column != val)
                else:
                    stmt = stmt.where(getattr(self.model, key) == value)

        return stmt

    @abstractmethod
    def get_model(self) -> type[ModelType]:
        """Return the model class for this repository."""
        pass