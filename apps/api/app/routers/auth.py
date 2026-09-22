from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.errors import AppError
from app.core.ratelimit import SlidingWindow
from app.deps import ACCESS_COOKIE, REFRESH_COOKIE, current_user, current_user_any
from app.models import User
from app.schemas.auth import ChangePasswordIn, LoginIn, MeOut, SwitchOrgIn, me_out
from app.services import auth

router = APIRouter(prefix="/auth", tags=["auth"])
ip_limiter = SlidingWindow(get_settings().login_ip_per_minute, 60)


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    return fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "?")


def _set_cookies(response: Response, session: auth.Session_) -> None:
    s = get_settings()
    common = dict(httponly=True, samesite="lax", secure=s.cookie_secure)
    response.set_cookie(ACCESS_COOKIE, session.access_token, max_age=s.access_token_minutes * 60, path="/", **common)
    response.set_cookie(REFRESH_COOKIE, session.refresh_token, max_age=s.refresh_token_days * 86400, path="/api/auth", **common)


def _clear_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/api/auth")


@router.post("/login", response_model=MeOut)
def login(body: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    if not ip_limiter.hit(_client_ip(request)):
        raise AppError("locked", "Quá nhiều lần đăng nhập, thử lại sau 1 phút", 429)
    session = auth.login(db, body.org_code, body.username, body.password)
    _set_cookies(response, session)
    return me_out(session.user, session.org, session.role)


@router.post("/refresh", status_code=204)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    session = auth.refresh(db, request.cookies.get(REFRESH_COOKIE, ""))
    _set_cookies(response, session)
    response.status_code = 204
    return response


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    auth.logout(db, request.cookies.get(REFRESH_COOKIE))
    _clear_cookies(response)
    response.status_code = 204
    return response


@router.get("/me", response_model=MeOut)
def me(request: Request, user: User = Depends(current_user_any), db: Session = Depends(get_db)):
    from app.deps import _principal
    from app.models import Organization

    _, org_id, role = _principal(request, db)
    return me_out(user, db.get(Organization, org_id), role)


@router.post("/switch-org", response_model=MeOut)
def switch_org(body: SwitchOrgIn, request: Request, response: Response, user: User = Depends(current_user), db: Session = Depends(get_db)):
    session = auth.switch_org(db, db.merge(user), body.org_id, request.cookies.get(REFRESH_COOKIE))
    _set_cookies(response, session)
    return me_out(session.user, session.org, session.role)


@router.post("/change-password", status_code=204)
def change_password(body: ChangePasswordIn, response: Response, user: User = Depends(current_user_any), db: Session = Depends(get_db)):
    user = db.merge(user)
    auth.change_password(db, user, body.current_password, body.new_password)
    response.status_code = 204
    return response
