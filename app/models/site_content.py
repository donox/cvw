from sqlalchemy import Boolean, Column, DateTime, String, func

from app.database import Base


class PublicPage(Base):
    """A public site page that can be toggled to members-only access."""
    __tablename__ = "public_pages"

    slug         = Column(String, primary_key=True)   # e.g. "resources"
    label        = Column(String, nullable=False)      # human name for admin UI
    members_only = Column(Boolean, nullable=False, default=False)


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
