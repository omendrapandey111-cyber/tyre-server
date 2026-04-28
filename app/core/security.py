from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from uuid import UUID
import os

security = HTTPBearer()


class CurrentUser:
    def __init__(self, id: str, org_id: UUID, zone_id: UUID | None, role: str | None):
        self.id = id
        self.org_id = org_id
        self.zone_id = zone_id
        self.role = role


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token, 
            os.getenv("SECRET_KEY"), 
            algorithms=["HS256"]
        )

        org_id_str = payload.get("org_id")
        zone_id_str = payload.get("zone_id")
        role = payload.get("role")

        if not org_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing organization in token"
            )

        return CurrentUser(
            id=payload.get("sub"),
            org_id=UUID(org_id_str),
            zone_id=UUID(zone_id_str) if zone_id_str else None,
            role=role.lower() if role else None
        )

    except (JWTError, ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )