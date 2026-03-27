# Defines the saved_papers table, stores papers
# Each row belongs to one user (via user_id foreign key) and contains
# the full analysis result: classification, summary, keywords, and recommendations

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class SavedPaper(Base):
    __tablename__ = "saved_papers"

    id = Column(Integer, primary_key=True, index=True)                  
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)   
    title = Column(String, nullable=False)                              
    main_category = Column(String, nullable=False)                      
    subcategory = Column(String, nullable=False)                         
    summary = Column(Text, nullable=False)                                  
    keywords = Column(String, nullable=False)                               
    recommendations = Column(Text, nullable=False)                          
    saved_at = Column(DateTime(timezone=True), server_default=func.now())