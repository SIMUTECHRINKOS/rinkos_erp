"""
Endpoints FastAPI — Auth, Usuarios, Licencias y Permisos.
Prefijo: /api/v1/auth
"""
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user, require_superuser
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError, business_rule_error, conflict, not_found
from app.modules.auth.schemas import (
    AssignLicenseRequest,
    LicenseTypeResponse,
    LoginRequest,
    PermissionObjectResponse,
    SetPermissionRequest,
    TokenResponse,
    UserCreate,
    UserPasswordChange,
    UserResponse,
    UserUpdate,
)
from app.modules.auth.service import AuthService, LicenseService, PermissionService, UserService

router = APIRouter(prefix="/auth", tags=["Auth"])


# ─── Login ────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    try:
        return AuthService(db).login(data)
    except (BusinessRuleError, NotFoundError) as e:
        raise business_rule_error(str(e))


@router.get("/me", response_model=UserResponse)
def me(current: CurrentUser = Depends(get_current_user)):
    return current.user


# ─── Usuarios ─────────────────────────────────────────────────────────────────

@router.get("/usuarios", response_model=list[UserResponse])
def listar_usuarios(
    tenant_id: uuid.UUID,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return UserService(db).listar_usuarios(tenant_id)


@router.post("/usuarios", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    tenant_id: uuid.UUID,
    data: UserCreate,
    current: CurrentUser = Depends(require_superuser),
    db: Session = Depends(get_db),
):
    try:
        return UserService(db).crear_usuario(tenant_id, data, created_by=current.id)
    except ConflictError as e:
        raise conflict(str(e))
    except NotFoundError as e:
        raise not_found("Tenant", str(tenant_id))


@router.patch("/usuarios/{user_id}", response_model=UserResponse)
def actualizar_usuario(
    user_id: uuid.UUID,
    data: UserUpdate,
    current: CurrentUser = Depends(require_superuser),
    db: Session = Depends(get_db),
):
    try:
        return UserService(db).actualizar_usuario(user_id, data)
    except NotFoundError:
        raise not_found("Usuario", str(user_id))


@router.post("/usuarios/{user_id}/cambiar-password", status_code=status.HTTP_204_NO_CONTENT)
def cambiar_password(
    user_id: uuid.UUID,
    data: UserPasswordChange,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Solo el propio usuario puede cambiar su contraseña
    if current.id != user_id:
        raise business_rule_error("Solo puedes cambiar tu propia contraseña.")
    try:
        UserService(db).cambiar_password(user_id, data.current_password, data.new_password)
    except BusinessRuleError as e:
        raise business_rule_error(str(e))


@router.delete("/usuarios/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_usuario(
    user_id: uuid.UUID,
    current: CurrentUser = Depends(require_superuser),
    db: Session = Depends(get_db),
):
    try:
        UserService(db).eliminar_usuario(user_id)
    except NotFoundError:
        raise not_found("Usuario", str(user_id))


# ─── Licencias ────────────────────────────────────────────────────────────────

@router.get("/licencias/tipos", response_model=list[LicenseTypeResponse])
def listar_tipos_licencia(db: Session = Depends(get_db)):
    types = LicenseService(db).listar_tipos()
    return [
        LicenseTypeResponse(
            id=lt.id,
            code=lt.code,
            name=lt.name,
            modules_allowed=[m.strip() for m in lt.modules_allowed.split(",") if m.strip()],
        )
        for lt in types
    ]


@router.get("/licencias/resumen/{tenant_id}")
def resumen_licencias(
    tenant_id: uuid.UUID,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return LicenseService(db).resumen_licencias_tenant(tenant_id)
    except NotFoundError:
        raise not_found("Tenant", str(tenant_id))


@router.post("/licencias/asignar", status_code=status.HTTP_201_CREATED)
def asignar_licencia(
    data: AssignLicenseRequest,
    current: CurrentUser = Depends(require_superuser),
    db: Session = Depends(get_db),
):
    try:
        return LicenseService(db).asignar_licencia(data, assigned_by=current.id)
    except NotFoundError as e:
        raise not_found("Recurso", str(e))
    except ConflictError as e:
        raise conflict(str(e))
    except BusinessRuleError as e:
        raise business_rule_error(str(e))


@router.post("/licencias/revocar", status_code=status.HTTP_204_NO_CONTENT)
def revocar_licencia(
    user_id: uuid.UUID,
    company_id: uuid.UUID,
    license_type_code: str,
    current: CurrentUser = Depends(require_superuser),
    db: Session = Depends(get_db),
):
    try:
        LicenseService(db).revocar_licencia(user_id, company_id, license_type_code, current.id)
    except NotFoundError as e:
        raise not_found("Licencia", str(e))
    except BusinessRuleError as e:
        raise business_rule_error(str(e))


# ─── Permisos ─────────────────────────────────────────────────────────────────

@router.get("/permisos/objetos", response_model=list[PermissionObjectResponse])
def listar_objetos_permiso(
    module: str | None = None,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PermissionService(db).listar_objetos(module)


@router.get("/permisos/usuario/{user_id}/company/{company_id}")
def obtener_permisos_usuario(
    user_id: uuid.UUID,
    company_id: uuid.UUID,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return PermissionService(db).obtener_permisos_usuario(user_id, company_id)


@router.post("/permisos", status_code=status.HTTP_200_OK)
def establecer_permiso(
    data: SetPermissionRequest,
    current: CurrentUser = Depends(require_superuser),
    db: Session = Depends(get_db),
):
    try:
        return PermissionService(db).establecer_permiso(data, set_by=current.id)
    except NotFoundError as e:
        raise not_found("Objeto de permiso", str(e))
    except BusinessRuleError as e:
        raise business_rule_error(str(e))
