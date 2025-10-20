# Utility Scripts

This directory contains utility scripts for database migrations, debugging, and maintenance tasks.

## Available Scripts

### `migrate_documents.py`
Database migration script to add enhanced error reporting columns to the documents table.

**What it does:**
- Adds `processing_stats` (JSONB) column for detailed processing information
- Adds `page_count` (INTEGER) column for page tracking
- Adds `chunk_count` (INTEGER) column for chunk tracking

**Run from backend container:**
```bash
docker compose exec backend python scripts/migrate_documents.py
```

**Note:** This migration has already been run. Only needed if recreating the database.

---

### `view_document_details.py`
Debug script to view detailed information about uploaded documents.

**What it does:**
- Lists all documents in the database
- Shows processing status and statistics
- Displays error details if any
- Shows chunk and page counts

**Run from project root:**
```bash
python3 scripts/view_document_details.py
```

---

## Creating New Scripts

When adding utility scripts:

1. **Database migrations** - Name as `migrate_*.py`
2. **Debug scripts** - Name as `debug_*.py` or `view_*.py`
3. **Data scripts** - Name as `seed_*.py` or `generate_*.py`
4. **Maintenance** - Name as `cleanup_*.py` or `fix_*.py`

Always include:
- Clear docstring explaining purpose
- Usage instructions in comments
- Error handling
- Success/failure messages

## Example Script Template

```python
"""
Script description here
Run with: python scripts/my_script.py
"""
import sys
sys.path.insert(0, '/app')  # If running in Docker

from app.core.config import settings
from app.db.session import SessionLocal

def main():
    """Main function"""
    print("Starting script...")
    
    # Your code here
    
    print("✅ Script completed successfully!")

if __name__ == "__main__":
    main()
```
