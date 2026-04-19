"""Process Library — renders YAML-frontmatter Markdown process docs."""
from pathlib import Path

import markdown as md
import yaml
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User

PROCESSES_DIR = Path("docs/processes")

router = APIRouter(prefix="/processes", tags=["processes"])
templates = Jinja2Templates(directory="app/templates")


def _parse_process_file(path: Path) -> dict:
    """Split YAML frontmatter from Markdown body and return both parsed."""
    text = path.read_text()
    if not text.startswith("---"):
        return {"meta": {}, "body_html": md.markdown(text, extensions=["tables", "toc"])}

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {"meta": {}, "body_html": ""}

    meta = yaml.safe_load(parts[1]) or {}
    body_html = md.markdown(parts[2].strip(), extensions=["tables", "toc", "fenced_code"])
    return {"meta": meta, "body_html": body_html}


def _resolve_paths(meta: dict) -> dict:
    """Build a per-trigger ordered step list for the path-selector UI."""
    triggers = meta.get("triggers", [])
    steps = meta.get("steps", [])
    paths = {}
    for trigger in triggers:
        tid = trigger["id"]
        path_steps = []
        for step in steps:
            if "trigger_variants" in step:
                variant = step["trigger_variants"].get(tid)
                if variant:
                    path_steps.append({
                        "label": step["label"],
                        "actor": step.get("actor", ""),
                        "action": variant.get("action", ""),
                    })
            elif "variants" in step:
                for variant in step["variants"].values():
                    vtrigger = variant.get("trigger", [])
                    if isinstance(vtrigger, str):
                        vtrigger = [vtrigger]
                    if tid in vtrigger:
                        path_steps.append({
                            "label": step["label"],
                            "actor": variant.get("actor", step.get("actor", "")),
                            "action": variant.get("action", ""),
                        })
                        break
            else:
                path_steps.append({
                    "label": step["label"],
                    "actor": step.get("actor", ""),
                    "action": step.get("action", ""),
                })
        paths[tid] = path_steps
    return paths


def _officer_names(db: Session) -> dict[str, str]:
    """Return {officer_title: member_full_name} for all active officers with a member linked."""
    from app.models.officer import Officer
    from app.models.member import Member
    rows = (
        db.query(Officer.title, Member.first_name, Member.last_name)
        .join(Member, Officer.member_id == Member.id)
        .filter(Officer.active == True)
        .all()
    )
    return {title: f"{first} {last}" for title, first, last in rows}


def _generate_mermaid(meta: dict, paths: dict) -> str:
    """Build a Mermaid flowchart from process paths with convergence detection."""
    triggers = meta.get("triggers", [])
    if not triggers or not paths:
        return ""

    roles = {r["id"]: r["title"] for r in meta.get("roles", [])}

    def actor_label(actor_id: str) -> str:
        return roles.get(actor_id, actor_id.replace("-", " ").title()) if actor_id else ""

    def node_text(step: dict) -> str:
        label = step["label"].replace('"', "'")
        actor = actor_label(step.get("actor", ""))
        return f'"{label}\\n({actor})"' if actor else f'"{label}"'

    all_steps = [paths.get(t["id"], []) for t in triggers]

    # Detect shared suffix steps across all paths
    common = 0
    if all_steps:
        min_len = min(len(p) for p in all_steps)
        for i in range(1, min_len + 1):
            if all(
                p[-i]["label"] == all_steps[0][-i]["label"]
                and p[-i].get("actor") == all_steps[0][-i].get("actor")
                for p in all_steps
            ):
                common = i
            else:
                break

    shared = all_steps[0][-common:] if common else []
    first_shared = "shared_0" if shared else "DONE"

    lines = ["flowchart TD"]
    lines.append('    START(["▶ Start"])')

    if len(triggers) > 1:
        lines.append('    DEC{"How is it\\nsubmitted?"}')
        lines.append("    START --> DEC")
        prev_default = "DEC"
    else:
        prev_default = "START"

    for trigger, tsteps in zip(triggers, all_steps):
        tid = trigger["id"].replace("-", "_")
        tlabel = trigger["label"].replace('"', "'")
        unique = tsteps[:len(tsteps) - common]
        prev = prev_default

        for i, step in enumerate(unique):
            nid = f"{tid}_{i}"
            lines.append(f'    {nid}[{node_text(step)}]')
            if i == 0 and len(triggers) > 1:
                lines.append(f'    {prev} -->|"{tlabel}"| {nid}')
            else:
                lines.append(f'    {prev} --> {nid}')
            prev = nid

        # Connect this path's last node to shared section
        target = first_shared
        if not unique and len(triggers) > 1:
            lines.append(f'    {prev} -->|"{tlabel}"| {target}')
        else:
            lines.append(f'    {prev} --> {target}')

    # Shared convergence steps
    for i, step in enumerate(shared):
        nid = f"shared_{i}"
        lines.append(f'    {nid}[{node_text(step)}]')
        if i > 0:
            lines.append(f'    shared_{i-1} --> {nid}')

    if shared:
        lines.append(f'    shared_{len(shared)-1} --> DONE')

    lines.append('    DONE(["✅ Complete"])')
    return "\n".join(lines)


def _list_processes() -> list[dict]:
    if not PROCESSES_DIR.exists():
        return []
    processes = []
    for f in sorted(PROCESSES_DIR.glob("*.md")):
        parsed = _parse_process_file(f)
        meta = parsed["meta"]
        processes.append({
            "slug": f.stem,
            "title": meta.get("process", f.stem).replace("-", " ").title(),
            "owner": meta.get("owner", ""),
            "status": meta.get("status", "draft"),
            "last_updated": meta.get("last_updated", ""),
            "open_issues": meta.get("open_issues", []),
        })
    return processes


@router.get("/", response_class=HTMLResponse)
def processes_index(request: Request, user: User = Depends(get_current_user)):
    return templates.TemplateResponse("processes/list.html", {
        "request": request,
        "processes": _list_processes(),
    })


@router.get("/{slug}", response_class=HTMLResponse)
def process_detail(
    slug: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    path = (PROCESSES_DIR / f"{slug}.md").resolve()
    if not path.exists() or not path.is_relative_to(PROCESSES_DIR.resolve()):
        raise HTTPException(status_code=404)
    parsed = _parse_process_file(path)
    meta = parsed["meta"]

    names = _officer_names(db)
    roles = []
    for r in meta.get("roles", []):
        db_title = r.get("db_title", "")
        roles.append({**r, "current_person": names.get(db_title, "") if db_title else ""})

    resolved = _resolve_paths(meta)
    return templates.TemplateResponse("processes/detail.html", {
        "request": request,
        "slug": slug,
        "title": meta.get("process", slug).replace("-", " ").title(),
        "meta": meta,
        "roles": roles,
        "triggers": meta.get("triggers", []),
        "open_issues": meta.get("open_issues", []),
        "paths": resolved,
        "mermaid_diagram": _generate_mermaid(meta, resolved),
        "body_html": parsed["body_html"],
    })
