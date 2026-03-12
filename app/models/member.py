from sqlalchemy import Boolean, Column, Date, Float, Integer, String, DateTime, func
from sqlalchemy.orm import relationship

from app.database import Base


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)

    # Personal
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    nickname = Column(String)
    email = Column(String, unique=True, index=True)
    birthday = Column(Date)
    significant_other = Column(String)

    # Address
    address = Column(String)
    city = Column(String)
    state = Column(String)
    zip_code = Column(String)

    # Phone
    home_phone = Column(String)
    work_phone = Column(String)
    mobile_phone = Column(String)

    # Membership
    membership_type = Column(String)   # Individual, Family, Secondary/Affiliate
    skill_level = Column(String)       # Beginner, Intermediate, Advanced, Professional
    years_turning = Column(String)     # Less than 1, 1-3, 3-5, 5-10, 10-20, 20+
    status = Column(String, default="Prospective")  # Prospective, Active, Former

    # Dues
    dues_paid = Column(Boolean, default=False)
    dues_paid_date = Column(Date)
    dues_amount = Column(Float)
    donation = Column(Float)
    payment_method = Column(String)  # PayPal, Cash, CK, Check

    # Volunteer
    volunteer_interest = Column(Boolean)
    volunteer_area = Column(String)

    # Other
    how_heard = Column(String)

    created_at = Column(DateTime, server_default=func.now())

    program_comments = relationship("ProgramComment", back_populates="member")
