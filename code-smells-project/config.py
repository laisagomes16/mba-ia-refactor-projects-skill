import os
import secrets


def _bool_env(name, default=False):
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _cors_origins():
    raw = os.environ.get("CORS_ORIGINS", "http://127.0.0.1:5000,http://localhost:5000")
    return [item.strip() for item in raw.split(",") if item.strip()]


class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY") or os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = _bool_env("FLASK_DEBUG", False)
    HOST = os.environ.get("FLASK_HOST", "127.0.0.1")
    PORT = int(os.environ.get("FLASK_PORT", "5000"))
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
    CORS_ORIGINS = _cors_origins()
    TOKEN_MAX_AGE = int(os.environ.get("TOKEN_MAX_AGE", "86400"))
    APP_VERSION = "1.0.0"
