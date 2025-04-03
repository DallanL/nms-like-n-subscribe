import logging
from contextlib import asynccontextmanager
from typing import Dict, List, Type, Any, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from fastapi import HTTPException

from .config import Config

logger = logging.getLogger(__name__)

# Create a new async engine
engine = create_async_engine(
    Config.POSTGRESQL_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=False,  # Set to False in production for less verbose logging
    future=True,
)

# Create a new async session factory.
async_session = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a new asynchronous session for interacting with the database.

    This session management function includes proper error handling and
    rollback logic. If an error occurs during the session, it rolls back the
    transaction, logs the error, and raises an HTTPException.
    """
    session = async_session()
    try:
        yield session
        await session.commit()
    except SQLAlchemyError as e:
        logger.exception(f"Database error during session: {e}\n; rolling back.")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Database session error") from e
    except Exception as e:
        logger.exception("Unexpected error during session; rolling back.")
        await session.rollback()
        raise HTTPException(
            status_code=500, detail="Unexpected database session error"
        ) from e
    finally:
        await session.close()


async def read_from_table(model: Type[Any], filters: Dict = {}) -> List[Any]:
    """
    Generic function to read rows from a table.

    :param model: SQLAlchemy model class.
    :param filters: Dictionary of filters to apply (e.g., {"team_id": "T123"}).
    :return: List of model instances.
    """
    try:
        async with get_session() as session:
            query = select(model).filter_by(**filters)
            result = await session.execute(query)
            rows = result.scalars().all()
            logger.info(
                f"Read {len(rows)} rows from {model.__tablename__} with filters: {filters}"
            )
            return list(rows)
    except SQLAlchemyError as e:
        logger.exception(f"Database error while reading from table: {e}")
        raise HTTPException(status_code=500, detail="Failed to read from database")


async def update_table(model: Type[Any], filters: Dict, update_data: Dict) -> None:
    """
    Generic function to update rows in a table, performing an upsert:
      - If rows matching `filters` exist, they are updated with `update_data`.
      - If no rows match, a new row is inserted using the combined filters and update_data.

    :param model: SQLAlchemy model class.
    :param filters: Dictionary of filters to locate rows.
    :param update_data: Dictionary of column updates.
    """
    try:
        async with get_session() as session:
            query = select(model).filter_by(**filters)
            result = await session.execute(query)
            rows = result.scalars().all()
            if not rows:
                # No record found; perform an insert (upsert behavior)
                data = {**filters, **update_data}
                new_instance = model(**data)
                session.add(new_instance)
                logger.info(
                    f"No rows found in {model.__tablename__} for filters: {filters}; "
                    f"inserted new record with data: {data}"
                )
            else:
                # Update all matching rows
                for row in rows:
                    for key, value in update_data.items():
                        setattr(row, key, value)
                logger.info(
                    f"Updated {len(rows)} rows in {model.__tablename__} with data: {update_data}"
                )
    except SQLAlchemyError as e:
        logger.exception(f"Database error while updating/upserting table: {e}")
        raise HTTPException(status_code=500, detail="Failed to update database") from e


async def delete_from_table(model: Type[Any], filters: Dict) -> None:
    """
    Generic function to delete rows from a table.

    :param model: SQLAlchemy model class.
    :param filters: Dictionary of filters to identify rows to delete.
    """
    try:
        async with get_session() as session:
            query = select(model).filter_by(**filters)
            result = await session.execute(query)
            rows = result.scalars().all()
            if not rows:
                logger.warning(
                    f"No rows found in {model.__tablename__} for filters: {filters}"
                )
                raise HTTPException(status_code=404, detail="Record not found")
            for row in rows:
                await session.delete(row)
            logger.info(
                f"Deleted {len(rows)} rows from {model.__tablename__} with filters: {filters}"
            )
    except SQLAlchemyError as e:
        logger.exception(f"Database error while deleting from table: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete from database")
