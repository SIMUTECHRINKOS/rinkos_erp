from fastapi import HTTPException, status


class RinkosError(Exception):
    """Error base de RINKOS ERP."""
    pass


class NotFoundError(RinkosError):
    pass


class ConflictError(RinkosError):
    pass


class BusinessRuleError(RinkosError):
    """Violación de regla de negocio — operación rechazada."""
    pass


def not_found(recurso: str, id: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{recurso} con id '{id}' no encontrado.",
    )


def conflict(mensaje: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=mensaje,
    )


def business_rule_error(mensaje: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=mensaje,
    )
