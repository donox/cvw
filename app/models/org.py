from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database import Base

EVENT_TYPES = [
    "Meeting",
    "Skill Session",
    "Member Drop-In",
    "Special Training",
    "Show",
    "Outreach",
    "Other",
]

REGISTRATION_RESTRICTIONS = [
    ("",                  "Open to all"),
    ("zoom_members_only", "Zoom restricted to members"),
    ("members_only",      "Members only"),
]

TODO_CATEGORIES = ["Planning", "Outreach", "Admin", "Program", "Membership", "Other"]
TODO_STATUSES = ["Open", "In Progress", "Done"]
TODO_PRIORITIES = ["Low", "Normal", "High"]


class OrgEvent(Base):
    __tablename__ = "org_events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(String)          # HH:MM
    end_time = Column(String)
    location = Column(String)
    description = Column(String)
    zoom_url                 = Column(String(500), nullable=True)
    registration_enabled     = Column(Boolean, default=False)
    capacity                 = Column(Integer,  nullable=True)   # None = unlimited
    registration_note        = Column(String(500), nullable=True)
    registration_restriction = Column(String(20),  nullable=True)  # None/"zoom_members_only"/"members_only"
    show_on_public           = Column(Boolean, default=False)
    activity_group_id        = Column(Integer, ForeignKey("member_groups.id"), nullable=True)
    planning_notes           = Column(Text, nullable=True)
    created_at               = Column(DateTime, server_default=func.now())

    activity_group = relationship("MemberGroup", backref="org_events")


class OrgTodo(Base):
    __tablename__ = "org_todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    category = Column(String)
    owner = Column(String)
    priority = Column(String, default="Normal")
    status = Column(String, default="Open")
    due_date = Column(Date)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
