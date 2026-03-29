import csv
import io
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_permission
from app.models.financial import (
    AccountCategory,
    FinancialTransaction,
    INCOME_CATEGORIES,
    EXPENSE_CATEGORIES,
    TRANSACTION_TYPES,
)
from app.models.member import Member

router = APIRouter(prefix="/financial", tags=["financial"])
templates = Jinja2Templates(directory="app/templates")

auth = Depends(require_permission("financial"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_categories(db: Session) -> tuple[list[str], list[str]]:
    """Return (income_names, expense_names) from DB, falling back to constants."""
    cats = db.query(AccountCategory).filter(AccountCategory.active == True).order_by(AccountCategory.type, AccountCategory.name).all()
    if cats:
        income = [c.name for c in cats if c.type == "Income"]
        expense = [c.name for c in cats if c.type == "Expense"]
    else:
        income, expense = INCOME_CATEGORIES, EXPENSE_CATEGORIES
    return income, expense


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


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Dues
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Transactions — list, CSV export, create, edit, delete
# ---------------------------------------------------------------------------

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


@router.get("/transactions/export")
def export_transactions_csv(
    request: Request,
    type_filter: Optional[str] = None,
    _=auth,
    db: Session = Depends(get_db),
):
    q = db.query(FinancialTransaction)
    if type_filter in TRANSACTION_TYPES:
        q = q.filter(FinancialTransaction.type == type_filter)
    transactions = q.order_by(FinancialTransaction.date.desc()).all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Date", "Type", "Category", "Description", "Member", "Reference", "Amount"])
    for t in transactions:
        member = f"{t.member.last_name}, {t.member.first_name}" if t.member else ""
        writer.writerow([t.date, t.type, t.category, t.description or "", member, t.reference or "", f"{t.amount:.2f}"])

    filename = f"transactions{'_' + type_filter.lower() if type_filter in TRANSACTION_TYPES else ''}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/transactions/new", response_class=HTMLResponse)
def new_transaction_form(request: Request, _=auth, db: Session = Depends(get_db)):
    income_cats, expense_cats = _get_categories(db)
    members = db.query(Member).order_by(Member.last_name, Member.first_name).all()
    return templates.TemplateResponse("financial/transaction_form.html", {
        "request": request, "txn": None, "errors": [],
        "income_categories": income_cats,
        "expense_categories": expense_cats,
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
        income_cats, expense_cats = _get_categories(db)
        members = db.query(Member).order_by(Member.last_name).all()
        return templates.TemplateResponse("financial/transaction_form.html", {
            "request": request, "txn": None, "errors": errors,
            "income_categories": income_cats,
            "expense_categories": expense_cats,
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
    income_cats, expense_cats = _get_categories(db)
    members = db.query(Member).order_by(Member.last_name, Member.first_name).all()
    return templates.TemplateResponse("financial/transaction_form.html", {
        "request": request, "txn": txn, "errors": [],
        "income_categories": income_cats,
        "expense_categories": expense_cats,
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


# ---------------------------------------------------------------------------
# Chart of Accounts
# ---------------------------------------------------------------------------

@router.get("/accounts", response_class=HTMLResponse)
def account_list(request: Request, _=auth, db: Session = Depends(get_db)):
    cats = db.query(AccountCategory).order_by(AccountCategory.type, AccountCategory.name).all()
    return templates.TemplateResponse("financial/accounts.html", {
        "request": request, "categories": cats,
    })


@router.get("/accounts/new", response_class=HTMLResponse)
def new_account_form(request: Request, _=auth):
    return templates.TemplateResponse("financial/account_form.html", {
        "request": request, "cat": None, "errors": [],
        "types": ["Income", "Expense"],
    })


@router.post("/accounts", response_class=RedirectResponse)
def create_account(
    name: str = Form(...),
    type_: str = Form(..., alias="type"),
    description: Optional[str] = Form(None),
    _=auth,
    db: Session = Depends(get_db),
):
    cat = AccountCategory(name=name.strip(), type=type_, description=description or None)
    db.add(cat)
    db.commit()
    return RedirectResponse(url="/financial/accounts", status_code=303)


@router.get("/accounts/{cat_id}/edit", response_class=HTMLResponse)
def edit_account_form(cat_id: int, request: Request, _=auth, db: Session = Depends(get_db)):
    cat = db.get(AccountCategory, cat_id)
    if not cat:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse("financial/account_form.html", {
        "request": request, "cat": cat, "errors": [],
        "types": ["Income", "Expense"],
    })


@router.post("/accounts/{cat_id}/edit", response_class=RedirectResponse)
def update_account(
    cat_id: int,
    name: str = Form(...),
    type_: str = Form(..., alias="type"),
    description: Optional[str] = Form(None),
    active: Optional[str] = Form(None),
    _=Depends(require_permission("financial")),
    db: Session = Depends(get_db),
):
    cat = db.get(AccountCategory, cat_id)
    if not cat:
        raise HTTPException(status_code=404)
    cat.name = name.strip()
    cat.type = type_
    cat.description = description or None
    cat.active = active == "on"
    db.commit()
    return RedirectResponse(url="/financial/accounts", status_code=303)


@router.post("/accounts/{cat_id}/delete", response_class=RedirectResponse)
def delete_account(cat_id: int, _=Depends(require_permission("financial")), db: Session = Depends(get_db)):
    cat = db.get(AccountCategory, cat_id)
    if cat:
        db.delete(cat)
        db.commit()
    return RedirectResponse(url="/financial/accounts", status_code=303)
