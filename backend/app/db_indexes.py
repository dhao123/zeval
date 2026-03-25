"""
Database index definitions for performance optimization.

Usage:
    Run from project root:
    python -m backend.app.db_indexes

Note:
    - For SQLite: Indexes are created automatically via SQLAlchemy
    - For PostgreSQL: Use CREATE INDEX CONCURRENTLY for production
"""

# Index definitions for synthetic_data table
SYNTHETIC_DATA_INDEXES = [
    # User data isolation + status + created_at (for list queries)
    {
        "name": "idx_synthetic_user_status_created",
        "table": "synthetic_data",
        "columns": ["created_by", "status", "created_at"],
        "unique": False,
    },
    # Category + status filter
    {
        "name": "idx_synthetic_category_status",
        "table": "synthetic_data",
        "columns": ["category_l4", "status"],
        "unique": False,
    },
    # Status + created_at for trend queries
    {
        "name": "idx_synthetic_status_created",
        "table": "synthetic_data",
        "columns": ["status", "created_at"],
        "unique": False,
    },
    # Keyword search index (partial match)
    {
        "name": "idx_synthetic_input",
        "table": "synthetic_data",
        "columns": ["input"],
        "unique": False,
    },
]

# Index definitions for data_pool table
DATA_POOL_INDEXES = [
    # User data isolation + pool_type + created_at
    {
        "name": "idx_datapool_user_type_created",
        "table": "data_pool",
        "columns": ["created_by", "pool_type", "created_at"],
        "unique": False,
    },
    # Pool type + category filter
    {
        "name": "idx_datapool_type_category",
        "table": "data_pool",
        "columns": ["pool_type", "category_l4"],
        "unique": False,
    },
    # Source ID lookup (for pool_location queries)
    {
        "name": "idx_datapool_source",
        "table": "data_pool",
        "columns": ["source_id"],
        "unique": False,
    },
    # Created at for trend queries
    {
        "name": "idx_datapool_created",
        "table": "data_pool",
        "columns": ["created_at"],
        "unique": False,
    },
]

# Combined index list
ALL_INDEXES = SYNTHETIC_DATA_INDEXES + DATA_POOL_INDEXES


async def create_indexes(db_session):
    """Create all defined indexes.
    
    Args:
        db_session: SQLAlchemy async session
    """
    from sqlalchemy import text
    
    for index in ALL_INDEXES:
        columns = ", ".join(index["columns"])
        sql = f"CREATE INDEX IF NOT EXISTS {index['name']} ON {index['table']} ({columns})"
        
        try:
            await db_session.execute(text(sql))
            print(f"Created index: {index['name']}")
        except Exception as e:
            print(f"Failed to create index {index['name']}: {e}")
    
    await db_session.commit()
    print("All indexes created successfully")


if __name__ == "__main__":
    import asyncio
    from app.core.database import AsyncSessionLocal
    
    async def main():
        async with AsyncSessionLocal() as session:
            await create_indexes(session)
    
    asyncio.run(main())
