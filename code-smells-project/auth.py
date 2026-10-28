from functools import wraps

from flask import request, g
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from errors import AppError


def hash_password(plain):
    return generate_password_hash(plain)


def verify_password(stored, plain):
    if not stored or not plain:
        return False
    if stored.startswith("pbkdf2:") or stored.startswith("scrypt:"):
        return check_password_hash(stored, plain)
    return stored == plain


def _serializer(app):
    return URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="loja-auth")


def create_token(app, user_id):
    return _serializer(app).dumps({"uid": user_id})


def user_from_token(app, token):
    try:
        data = _serializer(app).loads(token, max_age=Config.TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
    return data.get("uid")


def _bearer_token():
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:].strip()
    return None


def get_current_user_id(app):
    token = _bearer_token()
    if not token:
        return None
    return user_from_token(app, token)


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        from flask import current_app
        from repositories.user_repository import UserRepository

        user_id = get_current_user_id(current_app._get_current_object())
        if user_id is None:
            raise AppError("Não autenticado", 401)
        user = UserRepository().get_by_id(user_id)
        if user is None:
            raise AppError("Não autenticado", 401)
        g.current_user = user
        return fn(*args, **kwargs)

    return wrapper


def require_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        from flask import current_app
        from repositories.user_repository import UserRepository

        user_id = get_current_user_id(current_app._get_current_object())
        if user_id is None:
            raise AppError("Não autenticado", 401)
        user = UserRepository().get_by_id(user_id)
        if user is None or user.get("tipo") != "admin":
            raise AppError("Acesso negado", 403)
        g.current_user = user
        return fn(*args, **kwargs)

    return wrapper
