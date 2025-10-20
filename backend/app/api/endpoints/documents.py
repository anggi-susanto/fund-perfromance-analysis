"""
Document API endpoints
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks, Form
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
from datetime import datetime
from app.db.session import get_db
from app.models.document import Document
from app.schemas.document import (
    Document as DocumentSchema,
    DocumentUploadResponse,
    DocumentStatus
)
from app.services.document_processor import DocumentProcessor
from app.core.config import settings

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    fund_id: int = Form(1),  # Use Form() for multipart form data
    db: Session = Depends(get_db)
):
    """Upload and process a PDF document"""
    
    print(f"[Upload] Received fund_id: {fund_id}, type: {type(fund_id)}")
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Validate file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE} bytes"
        )
    
    # Create upload directory if it doesn't exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Save file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create document record
    document = Document(
        fund_id=fund_id,
        file_name=file.filename,
        file_path=file_path,
        parsing_status="pending"
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Start background processing
    background_tasks.add_task(
        process_document_task,
        document.id,
        file_path,
        fund_id  # Use the fund_id from parameter
    )
    
    return DocumentUploadResponse(
        document_id=document.id,
        task_id=None,
        status="pending",
        message="Document uploaded successfully. Processing started."
    )


async def process_document_task(document_id: int, file_path: str, fund_id: int):
    """Background task to process document"""
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    
    try:
        # Update status to processing
        document = db.query(Document).filter(Document.id == document_id).first()
        document.parsing_status = "processing"
        db.commit()
        
        # Process document (now passing db session)
        processor = DocumentProcessor()
        result = await processor.process_document(file_path, document_id, fund_id, db)
        
        # Update document with results
        document.parsing_status = result["status"]
        stats = result.get("statistics", {})
        document.processing_stats = stats
        document.page_count = stats.get("total_pages")
        document.chunk_count = stats.get("text_chunks")
        
        # Set error_message based on status
        if result["status"] == "failed":
            document.error_message = result.get("error")
        elif result["status"] == "completed_with_errors" and stats.get("errors"):
            # For completed_with_errors, store first few errors as summary
            error_list = stats.get("errors", [])
            document.error_message = "; ".join(error_list[:3])  # First 3 errors
        
        db.commit()
        
        # Log summary
        print(f"\n[Document {document_id}] Processing complete:")
        print(f"  Status: {result['status']}")
        print(f"  Pages: {stats.get('total_pages', 0)}")
        print(f"  Tables: {stats.get('tables_found', 0)}")
        print(f"  Capital Calls: {stats.get('capital_calls', 0)}")
        print(f"  Distributions: {stats.get('distributions', 0)}")
        print(f"  Adjustments: {stats.get('adjustments', 0)}")
        print(f"  Text Chunks: {stats.get('text_chunks', 0)}")
        if stats.get("errors"):
            print(f"  Errors: {len(stats['errors'])}")
            for i, err in enumerate(stats["errors"][:3], 1):
                print(f"    {i}. {err}")
        
    except Exception as e:
        document = db.query(Document).filter(Document.id == document_id).first()
        document.parsing_status = "failed"
        document.error_message = str(e)
        db.commit()
        print(f"\n[Document {document_id}] Fatal error: {e}")
    finally:
        db.close()


@router.get("/{document_id}/status", response_model=DocumentStatus)
async def get_document_status(document_id: int, db: Session = Depends(get_db)):
    """Get document parsing status"""
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Extract errors from processing_stats for convenience
    errors = None
    if document.processing_stats and "errors" in document.processing_stats:
        errors = document.processing_stats["errors"]
    
    return DocumentStatus(
        document_id=document.id,
        status=document.parsing_status,
        error_message=document.error_message,
        processing_stats=document.processing_stats,
        page_count=document.page_count,
        chunk_count=document.chunk_count,
        errors=errors
    )


@router.get("/{document_id}", response_model=DocumentSchema)
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get document details"""
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document


@router.get("/", response_model=List[DocumentSchema])
async def list_documents(
    fund_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all documents"""
    query = db.query(Document)
    
    if fund_id:
        query = query.filter(Document.fund_id == fund_id)
    
    documents = query.offset(skip).limit(limit).all()
    return documents


@router.delete("/{document_id}")
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Delete a document"""
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file
    if document.file_path and os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    # Delete database record
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}
