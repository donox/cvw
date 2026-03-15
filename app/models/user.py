from passlib.context import CryptContext
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.database import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ROLES = ["admin", "membership", "program", "financial", "exec", "librarian"]


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)       # see ROLES
    hashed_password = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    must_change_password = Column(Boolean, default=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    member = relationship("Member", backref="user_account")

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.hashed_password)

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)
