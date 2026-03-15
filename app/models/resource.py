from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.database import Base


class Resource(Base):
    __tablename__ = "resources"

    id          = Column(Integer, primary_key=True)
    category    = Column(String(100), nullable=False, index=True)
    title       = Column(String(200), nullable=False)
    url         = Column(String(1000), nullable=False)
    description = Column(String(500))
    sort_order  = Column(Integer, default=0)
    active      = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
