from sqlalchemy import Column, DateTime, String, func

from app.database import Base


class SiteSetting(Base):
    """Key/value pairs for structured site facts (meeting time, dues, etc.)."""
    __tablename__ = "site_settings"

    key        = Column(String, primary_key=True)
    label      = Column(String, nullable=False)   # human-readable label for admin form
    value      = Column(String, default="")
    updated_at = Column(DateTime, onupdate=func.now())


class ContentBlock(Base):
    """Freeform Markdown text blocks for narrative sections of public pages."""
    __tablename__ = "content_blocks"

    key        = Column(String, primary_key=True)
    title      = Column(String, nullable=False)   # human-readable name for admin list
    body       = Column(String, default="")
    updated_at = Column(DateTime, onupdate=func.now())
