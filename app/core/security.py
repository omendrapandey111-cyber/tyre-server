from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from uuid import UUID
import os

security = HTTPBearer(auto_error=True)


class CurrentUser:
    def __init__(self, id: str, org_id: UUID, zone_id: UUID | None, role: str | None):
        self.id = id
        self.org_id = org_id
        self.zone_id = zone_id
        self.role = role


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token, os.getenv("SECRET_KEY"), algorithms=["HS256"]
        )

        user_id = payload.get("sub")
        org_id_str = payload.get("org_id")
        zone_id_str = payload.get("zone_id")
        role = payload.get("role")

        if not user_id or not org_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing org_id",
            )

        org_uuid = UUID(org_id_str)

        # Handle zone_id safely
        zone_uuid = None
        if zone_id_str and str(zone_id_str).lower() != "none":
            try:
                zone_uuid = UUID(zone_id_str)
            except ValueError:
                zone_uuid = None

        return CurrentUser(
            id=user_id,
            org_id=org_uuid,
            zone_id=zone_uuid,
            role=role.lower() if role else None,
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )