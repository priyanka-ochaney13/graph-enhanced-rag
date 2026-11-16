from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

security = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    user_id: str
    roles: list[str]


# Demo users. Replace with a real user store / JWT validation.
_DEMO_USERS = {
    "token-public": CurrentUser(user_id="u-public", roles=["public"]),
    "token-employee": CurrentUser(user_id="u-emp", roles=["public", "employee"]),
    "token-exec": CurrentUser(user_id="u-exec", roles=["public", "employee", "executive"]),
}


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    user = _DEMO_USERS.get(creds.credentials)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user