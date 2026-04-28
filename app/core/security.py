from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from uuid import UUID
import os

# Initialize security scheme
security = HTTPBearer(auto_error=True)


class CurrentUser:
    """Simple class to hold authenticated user information"""
    def __init__(self, id: str, org_id: UUID, zone_id: UUID | None, role: str | None):
        self.id = id
        self.org_id = org_id
        self.zone_id = zone_id
        self.role = role


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    """
    Decode JWT token and return CurrentUser object
    """
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            os.getenv("SECRET_KEY"),
            algorithms=["HS256"]
        )

        user_id = payload.get("sub")
        org_id_str = payload.get("org_id")
        zone_id_str = payload.get("zone_id")
        role = payload.get("role")

        if not user_id or not org_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials: missing org_id",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Convert string to UUID
        org_uuid = UUID(org_id_str)
        zone_uuid = UUID(zone_id_str) if zone_id_str else None

        return CurrentUser(
            id=user_id,
            org_id=org_uuid,
            zone_id=zone_uuid,
            role=role.lower() if role else None
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid UUID format in token",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {str(e)}"
        )