from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.database import Base


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    subject = Column(String, nullable=False)
    body = Column(String, nullable=False)
    template_type = Column(String, default="simple")  # "simple" or "jinja2"
    created_by = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    scheduled_emails = relationship("ScheduledEmail", back_populates="template")


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    sent_at = Column(DateTime, server_default=func.now())
    subject = Column(String)
    recipient_count = Column(Integer, default=0)
    group_id = Column(Integer, ForeignKey("member_groups.id"), nullable=True)
    template_id = Column(Integer, ForeignKey("email_templates.id"), nullable=True)
    sent_by = Column(String)        # username of sender (or "scheduler")
    status = Column(String, default="sent")   # sent | failed | partial
    error_detail = Column(String)

    group = relationship("MemberGroup")
    template = relationship("EmailTemplate")


class ScheduledEmail(Base):
    __tablename__ = "scheduled_emails"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    template_id = Column(Integer, ForeignKey("email_templates.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("member_groups.id"), nullable=True)  # None = all active members
    # Cron schedule fields (all required together)
    cron_minute = Column(String, default="0")
    cron_hour = Column(String, default="8")
    cron_day = Column(String, default="*")
    cron_month = Column(String, default="*")
    cron_day_of_week = Column(String, default="*")
    active = Column(Boolean, default=True)
    last_run_at = Column(DateTime, nullable=True)

    template = relationship("EmailTemplate", back_populates="scheduled_emails")
    group = relationship("MemberGroup")
