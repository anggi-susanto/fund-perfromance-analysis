"""
Document database model
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Document(Base):
    """Document model"""
    
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    fund_id = Column(Integer, ForeignKey("funds.id"))
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500))
    upload_date = Column(DateTime, default=datetime.utcnow)
    parsing_status = Column(String(50), default="pending")  # pending, processing, completed, completed_with_errors, failed
    error_message = Column(Text)
    processing_stats = Column(JSON)  # Store detailed processing statistics including errors
    page_count = Column(Integer)
    chunk_count = Column(Integer)
    
    # Relationships
    fund = relationship("Fund", back_populates="documents")
