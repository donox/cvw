from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.database import Base


class GroupDocument(Base):
    __tablename__ = "group_documents"

    id         = Column(Integer, primary_key=True)
    group_id   = Column(Integer, ForeignKey("member_groups.id"), nullable=False)
    title      = Column(String(200), nullable=False)
    body       = Column(Text, nullable=False, default="")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
