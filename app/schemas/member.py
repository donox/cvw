from pydantic import BaseModel, EmailStr


class MemberBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr


class MemberCreate(MemberBase):
    pass


class MemberUpdate(MemberBase):
    pass


class MemberRead(MemberBase):
    id: int

    model_config = {"from_attributes": True}
