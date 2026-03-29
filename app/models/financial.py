from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.database import Base

# Legacy constants kept for fallback / migration seeding only
INCOME_CATEGORIES = ["Dues", "Show Income", "Store Sale", "Donation", "Other Income"]
EXPENSE_CATEGORIES = ["Venue", "Supplies", "Program Cost", "Printing", "Equipment", "Website", "Other Expense"]
TRANSACTION_TYPES = ["Income", "Expense"]


class AccountCategory(Base):
    __tablename__ = "account_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)        # "Income" or "Expense"
    description = Column(String)
    active = Column(Boolean, default=True, nullable=False)


class FinancialTransaction(Base):
    __tablename__ = "financial_transactions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    type = Column(String, nullable=False)        # Income, Expense
    category = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String)
    reference = Column(String)                   # check #, receipt #, etc.
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    member = relationship("Member", backref="transactions")
