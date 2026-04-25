import json

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Table, func
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
    is_dynamic = Column(Boolean, default=False)
    filter_criteria = Column(String)   # JSON: {status, membership_type, dues_paid, skill_level, volunteer_interest}
    # Activity group fields
    is_activity       = Column(Boolean, default=False)
    slug              = Column(String, unique=True, nullable=True)   # URL key e.g. "drop-in-saturday"
    meeting_day       = Column(String, nullable=True)                # e.g. "4th Saturday"
    meeting_frequency = Column(String, nullable=True)                # e.g. "Monthly"
    google_group_url  = Column(String, nullable=True)
    created_by = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    members = relationship("Member", secondary=member_group_assoc, backref="groups")

    def get_criteria(self) -> dict:
        if self.filter_criteria:
            try:
                return json.loads(self.filter_criteria)
            except (ValueError, TypeError):
                pass
        return {}


def resolve_members(group: MemberGroup, db):
    """Return members for a group — queries dynamically if is_dynamic, else static list."""
    if not group.is_dynamic:
        return group.members

    from app.models.member import Member
    criteria = group.get_criteria()
    q = db.query(Member)

    status = criteria.get("status")
    if status:
        q = q.filter(Member.status == status)

    membership_type = criteria.get("membership_type")
    if membership_type:
        q = q.filter(Member.membership_type == membership_type)

    dues_paid = criteria.get("dues_paid")
    if dues_paid == "yes":
        q = q.filter(Member.dues_paid == True)
    elif dues_paid == "no":
        q = q.filter(Member.dues_paid == False)

    skill_level = criteria.get("skill_level")
    if skill_level:
        q = q.filter(Member.skill_level == skill_level)

    volunteer_interest = criteria.get("volunteer_interest")
    if volunteer_interest == "yes":
        q = q.filter(Member.volunteer_interest == True)
    elif volunteer_interest == "no":
        q = q.filter(Member.volunteer_interest == False)

    return q.order_by(Member.last_name, Member.first_name).all()
