# CVW Financial Management — Enhancement Plan

**Status:** Proposed — for officer discussion
**Prepared:** 2026-03-15
**Audience:** Treasurer, President, Executive Committee

---

## Background

CVWdata currently records income and expense transactions and displays a
year-to-date summary on the financial dashboard. The Treasurer can enter
transactions, view a filtered list, and check dues payment status for each
member.

This document proposes a set of straightforward enhancements to make the
financial console more useful for day-to-day club management and year-end
reporting — without introducing the complexity of double-entry accounting
software.

---

## What Works Well Today

| Feature | Status |
|---|---|
| Income / expense transaction entry | ✅ Working |
| Year-to-date income, expenses, net | ✅ Dashboard summary |
| Transaction list with Income/Expense filter | ✅ Working |
| Dues paid / unpaid status by member | ✅ Working |
| Member linked to transaction (e.g. dues payment) | ✅ Working |

---

## Proposed Enhancements

### 1 — Chart of Accounts

**What:** Replace the current hardcoded income and expense category lists
with a small database table managed by the Treasurer.

**Current categories (hardcoded):**
- Income: Dues, Show Income, Store Sale, Donation, Other Income
- Expense: Venue, Supplies, Program Cost, Printing, Equipment, Website, Other Expense

**With this change the Treasurer can:**
- Add new categories as needs evolve (e.g. "AnchorSeal Sales", "Symposium")
- Retire old categories without losing historical transaction data
- Add a description to each category to clarify its intended use

**Implementation:** Small `AccountCategory` table (name, type, description,
active flag). The transaction form draws its category dropdown from this
table. Existing transaction history is unaffected — category is stored as a
string in each transaction record.

**Discussion questions:**
- Are the current categories sufficient, or are there gaps?
- Should categories be locked once transactions reference them, or freely
  renameable?

---

### 2 — Fiscal Year Awareness

**What:** CVW's financial year may not align with the calendar year. Add a
configurable fiscal year start (e.g. July 1) so that dashboard summaries,
reports, and the dues cycle all reflect the correct period.

**With this change:**
- The dashboard defaults to the current fiscal year rather than calendar year
- A year selector lets the Treasurer view any past fiscal year
- Reports clearly label the period they cover

**Discussion questions:**
- What is CVW's fiscal year? Calendar year (Jan–Dec) or another period?
- Does the dues renewal cycle align with the fiscal year?

---

### 3 — Reports Page

**What:** A dedicated `/financial/reports` page with three built-in reports.
All computed directly from the transaction data — no external library needed.

#### Report A: Income & Expense Summary
A one-page summary for a selected fiscal year:

| Category | Budget | Actual | Variance |
|---|---|---|---|
| Dues | $2,400 | $2,150 | -$250 |
| Store Sale | $500 | $620 | +$120 |
| … | | | |
| **Total Income** | | | |
| Venue | $1,200 | $1,100 | +$100 |
| … | | | |
| **Total Expenses** | | | |
| **Net** | | | |

Suitable for presenting at the annual meeting or submitting to AAW.
Print-friendly layout included.

#### Report B: Month-by-Month
12-row table showing income, expenses, and net for each month of the fiscal
year. Helps identify seasonal patterns (e.g. dues rush in January, show
income in spring).

#### Report C: Transaction Ledger
The full transaction list for a date range, sortable and printable. Suitable
for reconciling against bank statements.

**Discussion questions:**
- Are there other reports the Treasurer currently produces manually that
  could be automated?
- Should reports be exportable to PDF? (Infrastructure already exists via
  fpdf2.)

---

### 4 — Budget

**What:** Allow the Treasurer to enter a budget amount for each category and
fiscal year. The Income & Expense Summary report then shows actual vs. budget
with variance.

**Implementation:** A small `Budget` table (category, fiscal year, amount).
Entirely optional — reports work without a budget entered; the Budget and
Variance columns simply show "—" if no budget has been set.

**Discussion questions:**
- Does CVW currently prepare a formal annual budget?
- If yes, who approves it? (Typically the full membership at the annual
  meeting — the system could store it as read-only once approved.)

---

### 5 — CSV Export

**What:** A single "Export CSV" button on the transaction list page.
Downloads the currently filtered transactions as a spreadsheet-compatible
file.

Useful for:
- Giving the accountant / auditor a clean export
- Importing into Excel or Google Sheets for ad-hoc analysis
- Year-end record keeping

**Implementation:** ~10 lines of Python using the standard library. No
additional dependencies.

---

## What Is Deliberately Out of Scope

| Item | Reason |
|---|---|
| Double-entry / debits & credits | Unnecessary complexity for a club; single-entry is sufficient and auditable |
| Bank reconciliation workflow | Treasurer reconciles against statements manually; automating this adds little value at CVW's scale |
| PayPal / online dues payment | Requires a publicly accessible server and PayPal developer account — deferred to public website Phase 3 |
| Payroll | CVW has no employees |
| Tax filing integration | Out of scope for a membership system |

---

## Suggested Implementation Order

| Priority | Item | Effort | Value |
|---|---|---|---|
| 1 | Chart of Accounts | Low | Immediate — flexible categories |
| 2 | Reports page (A + B) | Medium | High — replaces manual spreadsheet work |
| 3 | Fiscal year support | Low | Medium — correctness |
| 4 | CSV export | Very low | High — easy win |
| 5 | Budget | Medium | Optional — only if CVW uses formal budgets |
| 6 | PDF reports | Low | Nice to have — print/archive |

---

## Questions for Discussion

1. **Fiscal year:** What period does CVW use? Does it match the dues renewal cycle?
2. **Budget:** Does CVW prepare a formal annual budget that gets member approval?
3. **Categories:** Are the current income/expense categories complete? Any missing?
4. **Reports:** What does the Treasurer currently produce manually (spreadsheets, etc.) that we could replace?
5. **Audit trail:** Should edited or deleted transactions be logged for audit purposes, or is the current edit/delete approach acceptable?
6. **Access:** Should the exec role have read-only access to financial reports, or is financial data strictly Treasurer + President only?

---

## Dependencies

- No new Python packages required for items 1–5
- PDF export (item 6) uses fpdf2, which is already installed
- All changes are backward-compatible with existing transaction data
