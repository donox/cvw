from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Resource(Base):
    __tablename__ = "resources"

    id          = Column(Integer, primary_key=True)
    category    = Column(String(100), nullable=False, index=True)
    title       = Column(String(200), nullable=False)
    url         = Column(String(1000), nullable=True)   # null when file_path is set
    file_path   = Column(String(500), nullable=True)    # filename within static/resources/
    description = Column(String(500))
    sort_order  = Column(Integer, default=0)
    active      = Column(Boolean, default=True)
    group_id    = Column(Integer, ForeignKey("member_groups.id"), nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    group = relationship("MemberGroup", backref="resources")

    @property
    def href(self) -> str:
        """Resolved link — static path for uploads, raw url for external links."""
        if self.file_path:
            return f"/static/resources/{self.file_path}"
        return self.url or ""

    @property
    def is_upload(self) -> bool:
        return bool(self.file_path)
