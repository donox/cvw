from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class GroupLeader(Base):
    __tablename__ = "group_leaders"

    id        = Column(Integer, primary_key=True, index=True)
    group_id  = Column(Integer, ForeignKey("member_groups.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    role      = Column(String, default="overall")   # "overall" or "monthly"
    event_id  = Column(Integer, ForeignKey("org_events.id"), nullable=True)  # set for monthly role
    created_at = Column(DateTime, default=datetime.utcnow)

    group  = relationship("MemberGroup", backref="leaders")
    member = relationship("Member", backref="group_leader_roles")
    event  = relationship("OrgEvent", backref="monthly_leaders")
