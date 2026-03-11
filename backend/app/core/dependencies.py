"""
Dependencias FastAPI para autenticación y autorización.

Uso en endpoints:
    current_user = Depends(get_current_user)
    require_module("accounting")(current_user)
"""
import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.modules.auth.repository import PermissionRepository, UserRepository
from app.modules.tenants.models import TenantUser

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class CurrentUser:
    """Datos del usuario autenticado extraídos del JWT."""
    def __init__(
        self,
        user: TenantUser,
        company_id: uuid.UUID,
        modules: list[str],
    ):
        self.user = user
        self.company_id = company_id
        self.modules = modules

    @property
    def id(self) -> uuid.UUID:
        return self.user.id

    @property
    def tenant_id(self) -> uuid.UUID:
        return self.user.tenant_id

    @property
    def is_superuser(self) -> bool:
        return self.user.is_superuser

    def has_module(self, module: str) -> bool:
        return module in self.modules

    def check_permission(self, db: Session, permission_object_code: str, min_level: int) -> None:
        """
        Verifica que el usuario tiene al menos min_level sobre el objeto.
        Lanza 403 si no tiene permiso.
        """
        repo = PermissionRepository(db)
        obj = repo.get_object_by_code(permission_object_code)
        if not obj:
            return  # si el objeto no existe, no hay restricción

        perm = repo.get_user_permission(self.id, self.company_id, obj.id)
        level = perm.level if perm else 0
        if level < min_level:
            labels = {0: "NINGUNO", 1: "LECTURA", 2: "TOTAL"}
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permiso insuficiente sobre '{permission_object_code}'. "
                       f"Requerido: {labels[min_level]}.",
            )


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> CurrentUser:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id = uuid.UUID(payload["sub"])
        company_id = uuid.UUID(payload["company_id"])
        modules: list[str] = payload.get("modules", [])
    except (JWTError, KeyError, ValueError):
        raise credentials_error

    user = UserRepository(db).get_by_id(user_id)
    if not user or not user.is_active:
        raise credentials_error

    return CurrentUser(user=user, company_id=company_id, modules=modules)


def require_module(module: str):
    """Dependencia que exige que el usuario tenga acceso al módulo indicado."""
    def _check(current: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not current.has_module(module):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tiene licencia para acceder al módulo '{module}'.",
            )
        return current
    return _check


def require_superuser(current: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Dependencia que exige SuperUsuario Profesional."""
    if not current.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere SuperUsuario para esta operación.",
        )
    return current
