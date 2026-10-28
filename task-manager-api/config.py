"""Configuração da aplicação — nenhum segredo fica no código-fonte."""
import os


def _env_bool(name, default=False):
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    # SECRET_KEY vem do ambiente. Sem valor, um segredo aleatório é gerado em
    # memória por processo (seguro por padrão: nunca é um literal no repositório).
    SECRET_KEY = (os.environ.get("FLASK_SECRET_KEY")
                  or os.environ.get("SECRET_KEY")
                  or os.urandom(32).hex())

    SQLALCHEMY_DATABASE_URI = os.environ.get("TASK_MANAGER_DATABASE_URI",
                                             "sqlite:///tasks.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEBUG = _env_bool("FLASK_DEBUG", False)
    HOST = os.environ.get("TASK_MANAGER_HOST", "0.0.0.0")
    PORT = int(os.environ.get("TASK_MANAGER_PORT", "5000"))

    # SMTP: sem credenciais no código.
    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")


class DevelopmentConfig(Config):
    DEBUG = _env_bool("FLASK_DEBUG", True)


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    DEBUG = False
