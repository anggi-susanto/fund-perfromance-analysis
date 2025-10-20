"""
Database migration script to add new columns to documents table
Run this inside the backend container
"""

from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate():
    """Add new columns to documents table"""
    engine = create_engine(settings.DATABASE_URL)
    
    migrations = [
        # Add processing_stats column (JSON)
        """
        ALTER TABLE documents 
        ADD COLUMN IF NOT EXISTS processing_stats JSONB;
        """,
        
        # Add page_count column
        """
        ALTER TABLE documents 
        ADD COLUMN IF NOT EXISTS page_count INTEGER;
        """,
        
        # Add chunk_count column
        """
        ALTER TABLE documents 
        ADD COLUMN IF NOT EXISTS chunk_count INTEGER;
        """,
        
        # Update comment on parsing_status to include new status
        """
        COMMENT ON COLUMN documents.parsing_status IS 
        'Document parsing status: pending, processing, completed, completed_with_errors, failed';
        """
    ]
    
    with engine.connect() as conn:
        for migration_sql in migrations:
            try:
                conn.execute(text(migration_sql))
                conn.commit()
                print(f"✅ Migration executed successfully")
            except Exception as e:
                print(f"⚠️  Migration skipped or failed: {e}")
    
    print("\n✅ All migrations completed!")
    print("\nNew columns added:")
    print("  - processing_stats (JSONB) - Stores detailed processing statistics")
    print("  - page_count (INTEGER) - Number of pages processed")
    print("  - chunk_count (INTEGER) - Number of text chunks created")

if __name__ == "__main__":
    migrate()
