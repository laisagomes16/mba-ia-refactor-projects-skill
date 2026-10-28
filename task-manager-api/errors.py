"""Exceções de domínio — mapeadas para HTTP por um handler central."""


class AppError(Exception):
    status_code = 400
    default_message = "Erro na requisição"

    def __init__(self, message=None, status_code=None, details=None):
        super().__init__(message or self.default_message)
        self.message = message or self.default_message
        if status_code is not None:
            self.status_code = status_code
        self.details = details

    def to_dict(self):
        return {"error": self.message}


class ValidationError(AppError):
    status_code = 400
    default_message = "Dados inválidos"


class NotFoundError(AppError):
    status_code = 404
    default_message = "Recurso não encontrado"


class ConflictError(AppError):
    status_code = 409
    default_message = "Recurso já existe"


class AuthenticationError(AppError):
    status_code = 401
    default_message = "Credenciais inválidas"


class ForbiddenError(AppError):
    status_code = 403
    default_message = "Acesso negado"
