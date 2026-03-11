from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr


class MemberBase(BaseModel):
    first_name: str
    last_name: str
    nickname: Optional[str] = None
    email: EmailStr
    birthday: Optional[date] = None
    significant_other: Optional[str] = None

    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None

    home_phone: Optional[str] = None
    work_phone: Optional[str] = None
    mobile_phone: Optional[str] = None

    membership_type: Optional[str] = None
    skill_level: Optional[str] = None
    years_turning: Optional[str] = None
    status: Optional[str] = "Prospective"

    dues_paid: Optional[bool] = False
    dues_paid_date: Optional[date] = None

    volunteer_interest: Optional[bool] = None
    volunteer_area: Optional[str] = None

    how_heard: Optional[str] = None


class MemberCreate(MemberBase):
    pass


class MemberUpdate(MemberBase):
    pass


class MemberRead(MemberBase):
    id: int

    model_config = {"from_attributes": True}
