"""
Document processing service using pdfplumber
"""
from typing import Dict, List, Any, Optional
import pdfplumber
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.config import settings
from app.services.table_parser import TableParser
from app.services.vector_store import VectorStore
from app.models.transaction import CapitalCall, Distribution, Adjustment
from app.db.session import SessionLocal


class DocumentProcessor:
    """Process PDF documents and extract structured data"""
    
    def __init__(self):
        self.table_parser = TableParser()
        self.vector_store = VectorStore()
    
    async def process_document(self, file_path: str, document_id: int, fund_id: int) -> Dict[str, Any]:
        """
        Process a PDF document
        
        Args:
            file_path: Path to the PDF file
            document_id: Database document ID
            fund_id: Fund ID
            
        Returns:
            Processing result with statistics
        """
        try:
            # Open PDF with pdfplumber
            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)
                
                # Statistics
                stats = {
                    "total_pages": total_pages,
                    "tables_found": 0,
                    "capital_calls": 0,
                    "distributions": 0,
                    "adjustments": 0,
                    "text_chunks": 0,
                    "errors": []
                }
                
                all_text_content = []
                
                # Process each page
                for page_num, page in enumerate(pdf.pages, start=1):
                    print(f"Processing page {page_num}/{total_pages}...")
                    
                    try:
                        # Extract tables from page
                        tables = page.extract_tables()
                        
                        print(f"  Found {len(tables)} tables on page {page_num}")
                        
                        if tables:
                            stats["tables_found"] += len(tables)
                            
                            # Process each table
                            for table_idx, table in enumerate(tables):
                                if not table or len(table) < 2:
                                    print(f"  Skipping empty table {table_idx}")
                                    continue
                                
                                try:
                                    # Parse and classify table
                                    parsed_table = self.table_parser.parse_table(table)
                                    print(f"  Table {table_idx}: Type={parsed_table['type']}, Rows={len(parsed_table.get('rows', []))}")
                                    
                                    # Store table data in database
                                    stored_count = await self._store_table_data(
                                        parsed_table, 
                                        fund_id, 
                                        document_id
                                    )
                                    
                                    print(f"  Stored {stored_count} records from table {table_idx}")
                                    
                                    # Update statistics
                                    if parsed_table["type"] == "capital_call":
                                        stats["capital_calls"] += stored_count
                                    elif parsed_table["type"] == "distribution":
                                        stats["distributions"] += stored_count
                                    elif parsed_table["type"] == "adjustment":
                                        stats["adjustments"] += stored_count
                                    
                                except Exception as e:
                                    error_msg = f"Error processing table {table_idx} on page {page_num}: {str(e)}"
                                    print(error_msg)
                                    stats["errors"].append(error_msg)
                        
                        # Extract text content from page
                        text = page.extract_text()
                        if text and text.strip():
                            all_text_content.append({
                                "page": page_num,
                                "text": text.strip()
                            })
                    
                    except Exception as e:
                        error_msg = f"Error processing page {page_num}: {str(e)}"
                        print(error_msg)
                        stats["errors"].append(error_msg)
                
                # Chunk and store text for vector search
                if all_text_content:
                    try:
                        chunks = self._chunk_text(all_text_content)
                        stats["text_chunks"] = len(chunks)
                        
                        # Store chunks in vector database
                        for chunk in chunks:
                            await self.vector_store.add_document(
                                content=chunk["text"],
                                metadata={
                                    "document_id": document_id,
                                    "fund_id": fund_id,
                                    "page": chunk["page"],
                                    "chunk_index": chunk["chunk_index"]
                                }
                            )
                    
                    except Exception as e:
                        error_msg = f"Error storing text chunks: {str(e)}"
                        print(error_msg)
                        stats["errors"].append(error_msg)
                
                # Determine final status
                if stats["errors"]:
                    status = "completed_with_errors" if (stats["capital_calls"] + stats["distributions"] + stats["adjustments"]) > 0 else "failed"
                else:
                    status = "completed"
                
                return {
                    "status": status,
                    "statistics": stats,
                    "message": f"Processed {total_pages} pages, found {stats['tables_found']} tables"
                }
        
        except Exception as e:
            error_msg = f"Fatal error processing document: {str(e)}"
            print(error_msg)
            return {
                "status": "failed",
                "error": error_msg,
                "statistics": {}
            }
    
    async def _store_table_data(
        self, 
        parsed_table: Dict[str, Any], 
        fund_id: int, 
        document_id: int
    ) -> int:
        """
        Store parsed table data in the database
        
        Args:
            parsed_table: Parsed table data
            fund_id: Fund ID
            document_id: Document ID
            
        Returns:
            Number of rows stored
        """
        db = SessionLocal()
        stored_count = 0
        
        try:
            table_type = parsed_table.get("type")
            rows = parsed_table.get("rows", [])
            
            for row in rows:
                try:
                    if table_type == "capital_call":
                        # Create capital call record
                        capital_call = CapitalCall(
                            fund_id=fund_id,
                            call_date=datetime.strptime(row["call_date"], '%Y-%m-%d').date(),
                            call_type=row.get("call_type"),
                            amount=row["amount"],
                            description=row.get("description")
                        )
                        db.add(capital_call)
                        stored_count += 1
                    
                    elif table_type == "distribution":
                        # Create distribution record
                        distribution = Distribution(
                            fund_id=fund_id,
                            distribution_date=datetime.strptime(row["distribution_date"], '%Y-%m-%d').date(),
                            distribution_type=row.get("distribution_type"),
                            is_recallable=row.get("is_recallable", False),
                            amount=row["amount"],
                            description=row.get("description")
                        )
                        db.add(distribution)
                        stored_count += 1
                    
                    elif table_type == "adjustment":
                        # Create adjustment record
                        adjustment = Adjustment(
                            fund_id=fund_id,
                            adjustment_date=datetime.strptime(row["adjustment_date"], '%Y-%m-%d').date(),
                            adjustment_type=row.get("adjustment_type"),
                            category=row.get("category"),
                            amount=row["amount"],
                            is_contribution_adjustment=row.get("is_contribution_adjustment", False),
                            description=row.get("description")
                        )
                        db.add(adjustment)
                        stored_count += 1
                
                except Exception as e:
                    print(f"Error storing row: {row}, Error: {e}")
                    continue
            
            # Commit all records
            db.commit()
        
        except Exception as e:
            db.rollback()
            print(f"Error storing table data: {e}")
        
        finally:
            db.close()
        
        return stored_count
    
    def _chunk_text(self, text_content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Chunk text content for vector storage
        
        Args:
            text_content: List of text content with metadata
            
        Returns:
            List of text chunks with metadata
        """
        chunks = []
        chunk_index = 0
        
        for content in text_content:
            page = content["page"]
            text = content["text"]
            
            # Split text into chunks with overlap
            chunk_size = settings.CHUNK_SIZE
            overlap = settings.CHUNK_OVERLAP
            
            # Simple chunking by character count
            start = 0
            while start < len(text):
                end = start + chunk_size
                chunk_text = text[start:end]
                
                # Try to break at sentence boundary
                if end < len(text):
                    # Look for sentence ending punctuation
                    last_period = chunk_text.rfind('.')
                    last_newline = chunk_text.rfind('\n')
                    break_point = max(last_period, last_newline)
                    
                    if break_point > chunk_size * 0.5:  # At least 50% of chunk size
                        chunk_text = text[start:start + break_point + 1]
                        end = start + break_point + 1
                
                # Add chunk
                if chunk_text.strip():
                    chunks.append({
                        "text": chunk_text.strip(),
                        "page": page,
                        "chunk_index": chunk_index
                    })
                    chunk_index += 1
                
                # Move to next chunk with overlap
                start = end - overlap
                
                # Prevent infinite loop
                if start <= end - chunk_size:
                    start = end
        
        return chunks
