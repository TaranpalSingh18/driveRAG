"""Google OAuth authentication module."""
import hashlib
import uuid
from typing import Optional
import requests
from fastapi import Request, HTTPException
try:
    from ..app.config import (
        CLIENT_ID,
        CLIENT_SECRET,
        AUTH_URL,
        TOKEN_URL,
        SCOPE,
        REDIRECT_URI,
    )
except ImportError:
    from app.config import (
        CLIENT_ID,
        CLIENT_SECRET,
        AUTH_URL,
        TOKEN_URL,
        SCOPE,
        REDIRECT_URI,
    )


def get_auth_redirect_url() -> tuple[str, str]:
    """
    Generate Google OAuth authorization URL and state.
    
    Returns:
        Tuple of (auth_url, state)
    """
    state = str(uuid.uuid4())
    auth_redirect_url = (
        f"{AUTH_URL}"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={SCOPE}"
        f"&access_type=offline"
        f"&prompt=consent"
        f"&state={state}"
    )
    return auth_redirect_url, state


def exchange_code_for_token(code: str) -> Optional[dict]:
    """
    Exchange authorization code for access token.
    
    Args:
        code: Authorization code from Google callback
        
    Returns:
        Token response dict or None if failed
    """
    data = {
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    
    try:
        token_res = requests.post(TOKEN_URL, data=data)
        return token_res.json()
    except Exception as e:
        print(f"Error exchanging code for token: {e}")
        return None


def get_access_token(request: Request) -> str:
    """
    Extract and validate access token from session.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Access token string
        
    Raises:
        HTTPException: If not authenticated
    """
    token = request.session.get("google_access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated. Please login.")
    return token


def get_user_profile(access_token: str) -> dict:
    """Fetch Google user profile for the authenticated token."""
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        res = requests.get("https://www.googleapis.com/oauth2/v3/userinfo", headers=headers, timeout=10)
        if not res.ok:
            return {}
        return res.json()
    except Exception:
        return {}


def get_drive_user(access_token: str) -> dict:
    """Fetch Drive user info using drive.readonly scope."""
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        res = requests.get(
            "https://www.googleapis.com/drive/v3/about",
            headers=headers,
            params={"fields": "user(permissionId,emailAddress,displayName)"},
            timeout=10,
        )
        if not res.ok:
            return {}
        payload = res.json()
        return payload.get("user", {}) if isinstance(payload, dict) else {}
    except Exception:
        return {}


def get_user_identity(request: Request) -> str:
    """Return a stable per-user identity used for vector store partitioning."""
    cached = request.session.get("google_user_id")
    if cached:
        return str(cached)

    token = get_access_token(request)
    profile = get_user_profile(token)
    drive_user = get_drive_user(token)

    user_id = (
        profile.get("sub")
        or profile.get("email")
        or drive_user.get("permissionId")
        or drive_user.get("emailAddress")
    )
    if not user_id:
        # Last-resort fallback to avoid hard-failing indexing on limited scopes.
        user_id = f"token_{hashlib.sha256(token.encode()).hexdigest()[:24]}"

    request.session["google_user_id"] = str(user_id)
    return str(user_id)
