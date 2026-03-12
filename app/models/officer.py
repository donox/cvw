from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base

OFFICER_TITLES = [
    "President",
    "Vice President",
    "Secretary",
    "Treasurer",
    "VP Membership",
    "Program Chair",
    "Webmaster",
    "Newsletter Editor",
    "Show Chair",
    "At-Large",
]


class Officer(Base):
    __tablename__ = "officers"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    title = Column(String, nullable=False)
    term_start = Column(Date)
    term_end = Column(Date)
    active = Column(Boolean, default=True)

    member = relationship("Member", backref="officer_roles")
