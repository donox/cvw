from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


OFFICER_CATEGORIES = ["Elected", "Volunteer"]

OFFICER_TITLES = [
    # Elected
    "President",
    "VP Program Coordinator",
    "VP Member Services",
    "Treasurer",
    "Secretary",
    "Skills Center Director",
    # Volunteer
    "AnchorSeal Manager",
    "Assistant Skills Center Director",
    "Cheese Shop Coordinator",
    "Librarian",
    "Newsletter Editor",
    "Photographer",
    "Store Manager",
    "Shenandoah Valley Arts Center Coordinator",
    "VA Symposium Board Member",
    "Video Team",
    "Webmaster",
]


class Officer(Base):
    __tablename__ = "officers"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    title = Column(String, nullable=False)
    category = Column(String, default="Elected")   # Elected / Volunteer
    notes = Column(String)
    term_start = Column(Date)
    term_end = Column(Date)
    active = Column(Boolean, default=True)

    member = relationship("Member", backref="officer_roles")
