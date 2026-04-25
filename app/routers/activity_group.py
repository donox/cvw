"""Activity Group router — leader dashboard for opt-in sub-group activities."""
from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.group import MemberGroup, member_group_assoc
from app.models.group_leader import GroupLeader
from app.models.member import Member
from app.models.org import OrgEvent, EVENT_TYPES
from app.models.resource import Resource
from app.models.user import User

router = APIRouter(prefix="/activity", tags=["activity"])
templates = Jinja2Templates(directory="app/templates")


# ── Auth helpers ──────────────────────────────────────────────────────────────

def _get_group_or_404(slug: str, db: Session) -> MemberGroup:
    group = db.query(MemberGroup).filter(
        MemberGroup.slug == slug,
        MemberGroup.is_activity == True,
    ).first()
    if not group:
        raise HTTPException(status_code=404)
    return group


def _is_overall_leader(user: User, group: MemberGroup, db: Session) -> bool:
    if user.role == "admin":
        return True
    if not user.member_id:
        return False
    return db.query(GroupLeader).filter(
        GroupLeader.group_id == group.id,
        GroupLeader.member_id == user.member_id,
        GroupLeader.role == "overall",
    ).first() is not None


def _require_leader(user: User, group: MemberGroup, db: Session):
    if not _is_overall_leader(user, group, db):
        raise HTTPException(status_code=403, detail="Overall leader access required.")


def _member_is_opted_in(member_id: int, group: MemberGroup, db: Session) -> bool:
    row = db.execute(
        member_group_assoc.select().where(
            member_group_assoc.c.group_id == group.id,
            member_group_assoc.c.member_id == member_id,
        )
    ).first()
    return row is not None


# ── List all activity groups ──────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
def activity_list(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    groups = db.query(MemberGroup).filter(MemberGroup.is_activity == True).order_by(MemberGroup.name).all()
    # For each group, note if current user is an overall leader
    member_id = user.member_id
    led_ids = set()
    if member_id:
        rows = db.query(GroupLeader.group_id).filter(
            GroupLeader.member_id == member_id,
            GroupLeader.role == "overall",
        ).all()
        led_ids = {r[0] for r in rows}

    return templates.TemplateResponse("activity/list.html", {
        "request": request,
        "groups": groups,
        "led_ids": led_ids,
        "is_admin": user.role == "admin",
    })


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/{slug}/", response_class=HTMLResponse)
def dashboard(
    slug: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _get_group_or_404(slug, db)
    is_leader = _is_overall_leader(user, group, db)

    today = date.today()
    upcoming = (
        db.query(OrgEvent)
        .filter(OrgEvent.activity_group_id == group.id, OrgEvent.date >= today)
        .order_by(OrgEvent.date)
        .limit(5)
        .all()
    )
    overall_leaders = (
        db.query(GroupLeader)
        .filter(GroupLeader.group_id == group.id, GroupLeader.role == "overall")
        .all()
    )
    artifacts = (
        db.query(Resource)
        .filter(Resource.group_id == group.id, Resource.active == True)
        .order_by(Resource.sort_order, Resource.title)
        .all()
    )
    member_count = len(group.members)

    # Monthly leader per upcoming event
    monthly_leaders = {}
    for evt in upcoming:
        gl = db.query(GroupLeader).filter(
            GroupLeader.event_id == evt.id,
            GroupLeader.role == "monthly",
        ).first()
        monthly_leaders[evt.id] = gl.member if gl else None

    # Self opt-in status
    opted_in = False
    if user.member_id:
        opted_in = _member_is_opted_in(user.member_id, group, db)

    return templates.TemplateResponse("activity/dashboard.html", {
        "request": request,
        "group": group,
        "is_leader": is_leader,
        "upcoming": upcoming,
        "overall_leaders": overall_leaders,
        "monthly_leaders": monthly_leaders,
        "artifacts": artifacts,
        "member_count": member_count,
        "opted_in": opted_in,
    })


# ── Members ───────────────────────────────────────────────────────────────────

@router.get("/{slug}/members", response_class=HTMLResponse)
def members_view(
    slug: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _get_group_or_404(slug, db)
    _require_leader(user, group, db)
    all_active = db.query(Member).filter(Member.status == "Active").order_by(Member.last_name, Member.first_name).all()
    member_ids = {m.id for m in group.members}
    overall_leaders = db.query(GroupLeader).filter(
        GroupLeader.group_id == group.id, GroupLeader.role == "overall"
    ).all()
    leader_member_ids = {gl.member_id for gl in overall_leaders}
    return templates.TemplateResponse("activity/members.html", {
        "request": request,
        "group": group,
        "members": sorted(group.members, key=lambda m: (m.last_name, m.first_name)),
        "all_active": all_active,
        "member_ids": member_ids,
        "overall_leaders": overall_leaders,
        "leader_member_ids": leader_member_ids,
    })


@router.post("/{slug}/members/add", response_class=RedirectResponse)
def add_member(
    slug: str,
    member_id: int = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _get_group_or_404(slug, db)
    _require_leader(user, group, db)
    member = db.get(Member, member_id)
    if member and member not in group.members:
        group.members.append(member)
        db.commit()
    return RedirectResponse(url=f"/activity/{slug}/members", status_code=303)


@router.post("/{slug}/members/remove", response_class=RedirectResponse)
def remove_member(
    slug: str,
    member_id: int = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _get_group_or_404(slug, db)
    _require_leader(user, group, db)
    member = db.get(Member, member_id)
    if member and member in group.members:
        group.members.remove(member)
        db.commit()
    return RedirectResponse(url=f"/activity/{slug}/members", status_code=303)


# ── Overall leaders ───────────────────────────────────────────────────────────

@router.post("/{slug}/leaders/add", response_class=RedirectResponse)
def add_leader(
    slug: str,
    member_id: int = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _get_group_or_404(slug, db)
    _require_leader(user, group, db)
    existing = db.query(GroupLeader).filter(
        GroupLeader.group_id == group.id,
        GroupLeader.member_id == member_id,
        GroupLeader.role == "overall",
    ).first()
    if not existing:
        db.add(GroupLeader(group_id=group.id, member_id=member_id, role="overall"))
        db.commit()
    return RedirectResponse(url=f"/activity/{slug}/members", status_code=303)


@router.post("/{slug}/leaders/remove", response_class=RedirectResponse)
def remove_leader(
    slug: str,
    leader_id: int = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _get_group_or_404(slug, db)
    _require_leader(user, group, db)
    gl = db.get(GroupLeader, leader_id)
    if gl and gl.group_id == group.id and gl.role == "overall":
        db.delete(gl)
        db.commit()
    return RedirectResponse(url=f"/activity/{slug}/members", status_code=303)


# ── Self opt-in / opt-out ─────────────────────────────────────────────────────

@router.post("/{slug}/join", response_class=RedirectResponse)
def join_group(
    slug: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _get_group_or_404(slug, db)
    if user.member_id:
        member = db.get(Member, user.member_id)
        if member and member not in group.members:
            group.members.append(member)
            db.commit()
    return RedirectResponse(url=f"/activity/{slug}/", status_code=303)


@router.post("/{slug}/leave", response_class=RedirectResponse)
def leave_group(
    slug: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _get_group_or_404(slug, db)
    if user.member_id:
        member = db.get(Member, user.member_id)
        if member and member in group.members:
            group.members.remove(member)
            db.commit()
    return RedirectResponse(url=f"/activity/{slug}/", status_code=303)


# ── Events ────────────────────────────────────────────────────────────────────

@router.get("/{slug}/events/new", response_class=HTMLResponse)
def new_event_form(
    slug: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _get_group_or_404(slug, db)
    _require_leader(user, group, db)
    return templates.TemplateResponse("activity/event_form.html", {
        "request": request,
        "group": group,
        "event": None,
        "errors": [],
        "event_types": EVENT_TYPES,
        "members": sorted(group.members, key=lambda m: (m.last_name, m.first_name)),
    })


@router.post("/{slug}/events/new", response_class=RedirectResponse)
def create_event(
    slug: str,
    request: Request,
    title: str = Form(...),
    event_type: str = Form("Member Drop-In"),
    event_date: str = Form(...),
    start_time: str = Form(""),
    end_time: str = Form(""),
    location: str = Form(""),
    description: str = Form(""),
    zoom_url: str = Form(""),
    planning_notes: str = Form(""),
    monthly_leader_id: str = Form(""),
    registration_enabled: str = Form(""),
    capacity: str = Form(""),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _get_group_or_404(slug, db)
    _require_leader(user, group, db)

    errors = []
    if not title.strip():
        errors.append("Title is required.")
    if not event_date:
        errors.append("Date is required.")

    if errors:
        return templates.TemplateResponse("activity/event_form.html", {
            "request": request, "group": group, "event": None, "errors": errors,
            "event_types": EVENT_TYPES,
            "members": sorted(group.members, key=lambda m: (m.last_name, m.first_name)),
        }, status_code=422)

    from datetime import date as date_type
    parsed_date = date_type.fromisoformat(event_date)
    cap = int(capacity) if capacity.strip().isdigit() else None

    evt = OrgEvent(
        title=title.strip(),
        event_type=event_type,
        date=parsed_date,
        start_time=start_time.strip() or None,
        end_time=end_time.strip() or None,
        location=location.strip() or None,
        description=description.strip() or None,
        zoom_url=zoom_url.strip() or None,
        planning_notes=planning_notes.strip() or None,
        registration_enabled=(registration_enabled == "on"),
        capacity=cap,
        activity_group_id=group.id,
    )
    db.add(evt)
    db.flush()

    if monthly_leader_id.strip().isdigit():
        db.add(GroupLeader(
            group_id=group.id,
            member_id=int(monthly_leader_id),
            role="monthly",
            event_id=evt.id,
        ))

    db.commit()
    return RedirectResponse(url=f"/activity/{slug}/", status_code=303)


@router.post("/{slug}/events/{event_id}/leader", response_class=RedirectResponse)
def set_monthly_leader(
    slug: str,
    event_id: int,
    monthly_leader_id: int = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _get_group_or_404(slug, db)
    _require_leader(user, group, db)
    # Replace existing monthly leader for this event
    db.query(GroupLeader).filter(
        GroupLeader.event_id == event_id,
        GroupLeader.role == "monthly",
    ).delete()
    db.add(GroupLeader(
        group_id=group.id,
        member_id=monthly_leader_id,
        role="monthly",
        event_id=event_id,
    ))
    db.commit()
    return RedirectResponse(url=f"/activity/{slug}/", status_code=303)


# ── Resources / Artifacts ─────────────────────────────────────────────────────

@router.get("/{slug}/resources", response_class=HTMLResponse)
def resources_view(
    slug: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _get_group_or_404(slug, db)
    _require_leader(user, group, db)
    resources = (
        db.query(Resource)
        .filter(Resource.group_id == group.id)
        .order_by(Resource.sort_order, Resource.title)
        .all()
    )
    return templates.TemplateResponse("activity/resources.html", {
        "request": request,
        "group": group,
        "resources": resources,
    })


@router.post("/{slug}/resources/add", response_class=RedirectResponse)
def add_resource(
    slug: str,
    title: str = Form(...),
    url: str = Form(""),
    description: str = Form(""),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _get_group_or_404(slug, db)
    _require_leader(user, group, db)
    if title.strip() and url.strip():
        db.add(Resource(
            category="Activity",
            title=title.strip(),
            url=url.strip(),
            description=description.strip() or None,
            group_id=group.id,
            active=True,
        ))
        db.commit()
    return RedirectResponse(url=f"/activity/{slug}/resources", status_code=303)


@router.post("/{slug}/resources/{res_id}/delete", response_class=RedirectResponse)
def delete_resource(
    slug: str,
    res_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _get_group_or_404(slug, db)
    _require_leader(user, group, db)
    res = db.get(Resource, res_id)
    if res and res.group_id == group.id:
        db.delete(res)
        db.commit()
    return RedirectResponse(url=f"/activity/{slug}/resources", status_code=303)
