from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_permission
from app.models.financial import FinancialTransaction, INCOME_CATEGORIES, EXPENSE_CATEGORIES, TRANSACTION_TYPES
from app.models.member import Member

router = APIRouter(prefix="/financial", tags=["financial"])
templates = Jinja2Templates(directory="app/templates")

auth = Depends(require_permission("financial"))


def _summary(db: Session, year: int) -> dict:
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    txns = db.query(FinancialTransaction).filter(
        FinancialTransaction.date >= start,
        FinancialTransaction.date <= end,
    ).all()
    income = sum(t.amount for t in txns if t.type == "Income")
    expenses = sum(t.amount for t in txns if t.type == "Expense")
    by_cat: dict[str, float] = {}
    for t in txns:
        by_cat[t.category] = by_cat.get(t.category, 0) + t.amount
    return {"income": income, "expenses": expenses, "net": income - expenses,
            "by_category": by_cat, "count": len(txns)}


@router.get("/", response_class=HTMLResponse)
def financial_index(request: Request, _=auth, db: Session = Depends(get_db)):
    year = datetime.now().year
    summary = _summary(db, year)
    recent = db.query(FinancialTransaction).order_by(
        FinancialTransaction.date.desc()
    ).limit(10).all()
    return templates.TemplateResponse("financial/index.html", {
        "request": request, "year": year, "summary": summary, "recent": recent
    })


@router.get("/dues", response_class=HTMLResponse)
def dues_status(request: Request, _=auth, db: Session = Depends(get_db)):
    subject_members = (
        db.query(Member)
        .filter(Member.status == "Active", Member.membership_type != "Life")
        .order_by(Member.last_name, Member.first_name)
        .all()
    )
    paid = [m for m in subject_members if m.dues_paid]
    unpaid = [m for m in subject_members if not m.dues_paid]
    return templates.TemplateResponse("financial/dues.html", {
        "request": request,
        "paid": paid,
        "unpaid": unpaid,
    })


@router.get("/transactions", response_class=HTMLResponse)
def transaction_list(
    request: Request,
    type_filter: Optional[str] = None,
    _=auth,
    db: Session = Depends(get_db),
):
    q = db.query(FinancialTransaction)
    if type_filter in TRANSACTION_TYPES:
        q = q.filter(FinancialTransaction.type == type_filter)
    transactions = q.order_by(FinancialTransaction.date.desc()).all()
    return templates.TemplateResponse("financial/transactions.html", {
        "request": request, "transactions": transactions,
        "type_filter": type_filter, "transaction_types": TRANSACTION_TYPES,
    })


@router.get("/transactions/new", response_class=HTMLResponse)
def new_transaction_form(request: Request, _=auth, db: Session = Depends(get_db)):
    members = db.query(Member).order_by(Member.last_name, Member.first_name).all()
    return templates.TemplateResponse("financial/transaction_form.html", {
        "request": request, "txn": None, "errors": [],
        "income_categories": INCOME_CATEGORIES,
        "expense_categories": EXPENSE_CATEGORIES,
        "members": members,
    })


@router.post("/transactions", response_class=RedirectResponse)
def create_transaction(
    request: Request,
    date_: str = Form(..., alias="date"),
    type_: str = Form(..., alias="type"),
    category: str = Form(...),
    amount: str = Form(...),
    description: Optional[str] = Form(None),
    reference: Optional[str] = Form(None),
    member_id: Optional[str] = Form(None),
    _=auth,
    db: Session = Depends(get_db),
):
    errors = []
    try:
        parsed_date = date.fromisoformat(date_)
    except ValueError:
        errors.append("Invalid date.")
        parsed_date = None
    try:
        parsed_amount = float(amount)
        if parsed_amount <= 0:
            errors.append("Amount must be greater than zero.")
    except ValueError:
        errors.append("Invalid amount.")
        parsed_amount = None

    if errors:
        members = db.query(Member).order_by(Member.last_name).all()
        return templates.TemplateResponse("financial/transaction_form.html", {
            "request": request, "txn": None, "errors": errors,
            "income_categories": INCOME_CATEGORIES,
            "expense_categories": EXPENSE_CATEGORIES,
            "members": members,
        }, status_code=422)

    txn = FinancialTransaction(
        date=parsed_date, type=type_, category=category,
        amount=parsed_amount, description=description or None,
        reference=reference or None,
        member_id=int(member_id) if member_id else None,
    )
    db.add(txn)
    db.commit()
    return RedirectResponse(url="/financial/", status_code=303)


@router.get("/transactions/{txn_id}/edit", response_class=HTMLResponse)
def edit_transaction_form(txn_id: int, request: Request, _=auth, db: Session = Depends(get_db)):
    txn = db.get(FinancialTransaction, txn_id)
    if not txn:
        raise HTTPException(status_code=404)
    members = db.query(Member).order_by(Member.last_name, Member.first_name).all()
    return templates.TemplateResponse("financial/transaction_form.html", {
        "request": request, "txn": txn, "errors": [],
        "income_categories": INCOME_CATEGORIES,
        "expense_categories": EXPENSE_CATEGORIES,
        "members": members,
    })


@router.post("/transactions/{txn_id}/edit", response_class=RedirectResponse)
def update_transaction(
    txn_id: int,
    date_: str = Form(..., alias="date"),
    type_: str = Form(..., alias="type"),
    category: str = Form(...),
    amount: str = Form(...),
    description: Optional[str] = Form(None),
    reference: Optional[str] = Form(None),
    member_id: Optional[str] = Form(None),
    _=Depends(require_permission("financial")),
    db: Session = Depends(get_db),
):
    txn = db.get(FinancialTransaction, txn_id)
    if not txn:
        raise HTTPException(status_code=404)
    txn.date = date.fromisoformat(date_)
    txn.type = type_
    txn.category = category
    txn.amount = float(amount)
    txn.description = description or None
    txn.reference = reference or None
    txn.member_id = int(member_id) if member_id else None
    db.commit()
    return RedirectResponse(url="/financial/transactions", status_code=303)


@router.post("/transactions/{txn_id}/delete", response_class=RedirectResponse)
def delete_transaction(txn_id: int, _=Depends(require_permission("financial")), db: Session = Depends(get_db)):
    txn = db.get(FinancialTransaction, txn_id)
    if txn:
        db.delete(txn)
        db.commit()
    return RedirectResponse(url="/financial/transactions", status_code=303)
