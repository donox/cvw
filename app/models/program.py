from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.database import Base


class Program(Base):
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    subject = Column(String, nullable=False)
    presenter = Column(String)
    cost = Column(Float)
    attendee_count = Column(Integer)
    notes = Column(String)
    show_on_public = Column(Boolean, default=False)
    org_event_id = Column(Integer, ForeignKey("org_events.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    org_event = relationship("OrgEvent", backref="programs")

    comments = relationship(
        "ProgramComment", back_populates="program", cascade="all, delete-orphan"
    )


class ProgramComment(Base):
    __tablename__ = "program_comments"

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    anonymous = Column(Boolean, default=False)

    rating = Column(Integer)        # 1–5
    relevance = Column(Integer)     # 1–5
    learned_something = Column(Boolean)
    improvements = Column(String)

    created_at = Column(DateTime, server_default=func.now())

    program = relationship("Program", back_populates="comments")
    member = relationship("Member", back_populates="program_comments")
