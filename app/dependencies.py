from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User


class NotAuthenticatedException(Exception):
    pass


class PermissionDeniedException(Exception):
    pass


# Which areas each role can access (admin implicitly gets all)
ROLE_PERMISSIONS: dict[str, list[str]] = {
    "membership": ["members", "groups", "email", "dashboard"],
    "program":    ["programs", "members", "groups", "email", "dashboard"],
    "financial":  ["financial", "members", "groups", "email", "dashboard"],
    "exec":       ["exec", "members", "groups", "programs", "email", "dashboard", "activity"],
    "librarian":  ["librarian", "dashboard"],
    "admin":      ["*"],
}


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise NotAuthenticatedException()
    user = db.get(User, user_id)
    if not user or not user.active:
        raise NotAuthenticatedException()
    return user


def require_permission(area: str):
    """Dependency factory: requires login and that the user's role covers `area`."""
    def check(user: User = Depends(get_current_user)) -> User:
        perms = ROLE_PERMISSIONS.get(user.role, [])
        if "*" in perms or area in perms:
            return user
        raise PermissionDeniedException(area)
    return check
