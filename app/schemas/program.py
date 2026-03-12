from datetime import date
from typing import Optional

from pydantic import BaseModel


class ProgramCreate(BaseModel):
    date: date
    subject: str
    presenter: Optional[str] = None
    cost: Optional[float] = None
    attendee_count: Optional[int] = None
    notes: Optional[str] = None


class ProgramUpdate(ProgramCreate):
    pass


class ProgramCommentCreate(BaseModel):
    program_id: int
    member_id: Optional[int] = None
    anonymous: bool = False
    rating: Optional[int] = None
    relevance: Optional[int] = None
    learned_something: Optional[bool] = None
    improvements: Optional[str] = None
