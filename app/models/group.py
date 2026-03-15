from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, func
from sqlalchemy.orm import relationship

from app.database import Base

member_group_assoc = Table(
    "member_group_members",
    Base.metadata,
    Column("group_id", Integer, ForeignKey("member_groups.id"), primary_key=True),
    Column("member_id", Integer, ForeignKey("members.id"), primary_key=True),
)


class MemberGroup(Base):
    __tablename__ = "member_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)
    created_by = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    members = relationship("Member", secondary=member_group_assoc, backref="groups")
