from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError
from app.core.security import decode_access_token
from app.db.database import get_db_session
from app.db.models.user import User
from app.services.auth import AuthService

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials,
        Depends(bearer_scheme),
    ],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception

    user_id_str: str | None = payload.get("sub")
    tenant_id_str: str | None = payload.get("tenant_id")

    if user_id_str is None or tenant_id_str is None:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
        tenant_id = int(tenant_id_str)
    except ValueError:
        raise credentials_exception

    service = AuthService(db)
    try:
        user = await service.get_current_user(user_id, tenant_id)
    except AuthenticationError:
        raise credentials_exception

    return user


async def get_current_tenant(
    current_user: Annotated[User, Depends(get_current_user)],
) -> int:
    return current_user.tenant_id


CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentTenant = Annotated[int, Depends(get_current_tenant)]
