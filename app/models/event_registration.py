"""Models for event registration (sign-up with waitlist) and attendance tracking."""
import secrets
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base

ATTENDANCE_TYPES = ["In Person", "Remote"]


class EventRegistration(Base):
    """Advance sign-up for a capacity-limited OrgEvent."""
    __tablename__ = "event_registrations"

    id              = Column(Integer, primary_key=True)
    org_event_id    = Column(Integer, ForeignKey("org_events.id"), nullable=False)
    member_id       = Column(Integer, ForeignKey("members.id"),    nullable=True)
    name            = Column(String(100), nullable=False)
    email           = Column(String(200), nullable=False)
    attendance_type = Column(String(20),  default="In Person")
    # status: "confirmed" | "waitlist" | "cancelled"
    status          = Column(String(20),  default="confirmed")
    waitlist_position = Column(Integer,   nullable=True)
    cancel_token    = Column(String(64),  unique=True, nullable=True)
    registered_at   = Column(DateTime,    default=datetime.utcnow)
    confirmed_at    = Column(DateTime,    nullable=True)   # set when promoted from waitlist
    notes           = Column(String(500), nullable=True)

    org_event = relationship("OrgEvent", backref="registrations")
    member    = relationship("Member",   backref="event_registrations")

    @staticmethod
    def new_token() -> str:
        return secrets.token_urlsafe(32)


class Attendance(Base):
    """Who actually showed up at an OrgEvent (entered by an officer)."""
    __tablename__ = "attendance"

    id              = Column(Integer, primary_key=True)
    org_event_id    = Column(Integer, ForeignKey("org_events.id"), nullable=False)
    member_id       = Column(Integer, ForeignKey("members.id"),    nullable=True)
    visitor_name    = Column(String(100), nullable=True)
    visitor_email   = Column(String(200), nullable=True)
    attendance_type = Column(String(20),  default="In Person")
    checked_in_at   = Column(DateTime,    default=datetime.utcnow)
    # recorded_by is None for future kiosk self-check-in; officer username otherwise
    recorded_by     = Column(String(100), nullable=True)

    org_event = relationship("OrgEvent", backref="attendance_records")
    member    = relationship("Member",   backref="attendance_records")
