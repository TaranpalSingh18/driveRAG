"""Authentication API routes."""
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse

try:
    from ...core.auth import get_auth_redirect_url, exchange_code_for_token, get_user_profile, get_drive_user
    from ...app.config import FRONTEND_URL
except ImportError:
    from core.auth import get_auth_redirect_url, exchange_code_for_token, get_user_profile, get_drive_user
    from app.config import FRONTEND_URL

router = APIRouter(prefix="/auth", tags=["authentication"])
legacy_router = APIRouter(tags=["authentication-legacy"])


def _login(request: Request):
    auth_url, state = get_auth_redirect_url()
    request.session["oauth_state"] = state
    return RedirectResponse(auth_url)


def _callback(request: Request, code: str, state: str = ""):
    expected_state = request.session.get("oauth_state")
    if not expected_state or state != expected_state:
        return JSONResponse(status_code=400, content={"error": "Invalid OAuth state"})

    token_json = exchange_code_for_token(code)
    if not token_json:
        return JSONResponse(status_code=400, content={"error": "Token exchange failed"})

    access_token = token_json.get("access_token")
    if not access_token:
        return JSONResponse(
            status_code=400,
            content={"error": "Auth failed", "details": token_json}
        )

    request.session["google_access_token"] = access_token
    profile = get_user_profile(access_token)
    drive_user = get_drive_user(access_token)
    user_id = (
        profile.get("sub")
        or profile.get("email")
        or drive_user.get("permissionId")
        or drive_user.get("emailAddress")
    )
    if user_id:
        request.session["google_user_id"] = str(user_id)
    request.session.pop("oauth_state", None)

    return RedirectResponse(f"{FRONTEND_URL}?auth=success")


def _logout(request: Request):
    request.session.clear()
    return {"status": "logged_out"}


@router.get("/login")
def login(request: Request):
    """Redirect user to Google OAuth login."""
    return _login(request)


@router.get("/callback")
def callback(request: Request, code: str, state: str = ""):
    """Handle OAuth callback from Google."""
    return _callback(request, code, state)


@router.get("/status")
def auth_status(request: Request):
    """Check authentication status."""
    return {"authenticated": bool(request.session.get("google_access_token"))}


@router.post("/logout")
def logout(request: Request):
    """Logout user."""
    return _logout(request)


# Legacy compatibility routes for old frontend/env configs.
@legacy_router.get("/login")
def legacy_login(request: Request):
    return _login(request)


@legacy_router.get("/callback")
def legacy_callback(request: Request, code: str, state: str = ""):
    return _callback(request, code, state)


@legacy_router.post("/logout")
def legacy_logout(request: Request):
    return _logout(request)
