"""Autenticação/autorização na borda (FINDING-008).

Centraliza a política de acesso em um único lugar (decorators), em vez de
espalhar `if` de permissão pelas rotas. Usa `AuthService.decode_token`, que
antes existia mas nunca era chamado — o token emitido no `/login` era, na
prática, decorativo.

Contrato preservado: `/, /health, /login` continuam públicos; nenhuma resposta
de sucesso muda de formato. O que muda é que as rotas protegidas agora
respondem 401 sem token válido e 403 sem permissão.
"""
from functools import wraps

from flask import g, request

from errors import AuthenticationError, ForbiddenError
from services.auth_service import AuthService

MSG_UNAUTHENTICATED = 'Autenticação necessária'
MSG_INVALID_TOKEN = 'Token inválido ou expirado'
MSG_INSUFFICIENT_ROLE = 'Acesso negado'
MSG_INSUFFICIENT_OWNERSHIP = 'Você só pode alterar o próprio usuário'

BEARER_PREFIX = 'Bearer '


def _bearer_token():
    """Extrai o token do header `Authorization: Bearer <token>`."""
    header = request.headers.get('Authorization', '')
    if header.startswith(BEARER_PREFIX):
        return header[len(BEARER_PREFIX):].strip()
    return None


def _load_current_user():
    """Valida o token e devolve o User correspondente, ou levanta 401."""
    token = _bearer_token()
    if not token:
        raise AuthenticationError(MSG_UNAUTHENTICATED)

    payload = AuthService.decode_token(token)  # assinatura + expiração
    user = AuthService.user_from_payload(payload)
    if user is None:
        raise AuthenticationError(MSG_INVALID_TOKEN)
    if not user.is_active_user():
        raise ForbiddenError(MSG_INSUFFICIENT_ROLE)
    return user


def require_auth(view):
    """Exige um token válido; disponibiliza o usuário em `g.current_user`."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        g.current_user = _load_current_user()
        return view(*args, **kwargs)

    return wrapper


def require_admin(view):
    """Exige token válido **e** papel de administrador."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        current = _load_current_user()
        if not current.is_admin():
            raise ForbiddenError(MSG_INSUFFICIENT_ROLE)
        g.current_user = current
        return view(*args, **kwargs)

    return wrapper


def require_self_or_admin(view):
    """Exige token válido e que o `user_id` da URL seja o próprio ou um admin.

    Fecha o IDOR apontado na auditoria (`DELETE /users/<id>` de qualquer pessoa)
    sem inventar um novo protocolo de autenticação.
    """

    @wraps(view)
    def wrapper(*args, **kwargs):
        current = _load_current_user()
        target_id = kwargs.get('user_id')
        if not current.is_admin() and current.id != target_id:
            raise ForbiddenError(MSG_INSUFFICIENT_OWNERSHIP)
        g.current_user = current
        return view(*args, **kwargs)

    return wrapper
