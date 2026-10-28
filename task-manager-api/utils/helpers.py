"""Constantes de domínio e utilidades compartilhadas.

Substitui o antigo `utils/helpers.py`, que acumulava funções duplicadas e órfãs
(FINDING-021) e não era usado pelas rotas.
"""
from datetime import datetime, timedelta, timezone

# Status de task (antes repetidos como literais em 5 arquivos).
STATUS_PENDING = 'pending'
STATUS_IN_PROGRESS = 'in_progress'
STATUS_DONE = 'done'
STATUS_CANCELLED = 'cancelled'

TERMINAL_STATUSES = (STATUS_DONE, STATUS_CANCELLED)

VALID_STATUSES = [STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED]

ROLE_USER = 'user'
ROLE_ADMIN = 'admin'
ROLE_MANAGER = 'manager'
VALID_ROLES = [ROLE_USER, ROLE_ADMIN, ROLE_MANAGER]

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
MIN_PASSWORD_LENGTH = 4
MAX_TAGS_LENGTH = 500

MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3

# Faixas de prioridade usadas pelos relatórios (magic numbers → constantes).
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}
HIGH_PRIORITY_THRESHOLD = 2

DEFAULT_COLOR = '#000000'
COLOR_LENGTH = 7
DEFAULT_DESCRIPTION = ''

EMAIL_PATTERN = r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$'
DATE_FORMAT = '%Y-%m-%d'
RECENT_ACTIVITY_WINDOW_DAYS = 7


def utcnow():
    """UTC atual.

    Retorna **naive** (UTC) para ser comparável às colunas `DateTime` já
    existentes no banco. Evita o `datetime.utcnow()` depreciado sem introduzir
    o erro "can't compare offset-naive and offset-aware datetimes".
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_naive_utc(moment):
    """Normaliza datetimes aware para naive-UTC (compatível com as colunas atuais)."""
    if moment is None:
        return None
    if moment.tzinfo is not None:
        return moment.astimezone(timezone.utc).replace(tzinfo=None)
    return moment


def iso_utc(moment):
    """Formata um datetime naive-UTC como ISO-8601 com sufixo Z."""
    if moment is None:
        return None
    return to_naive_utc(moment).isoformat() + 'Z'


def parse_date(date_string, fmt=DATE_FORMAT):
    """Converte string em datetime naive; retorna None se inválida."""
    try:
        return datetime.strptime(date_string, fmt)
    except (TypeError, ValueError):
        return None


def calculate_percentage(part, total):
    if not total:
        return 0
    return round((part / total) * 100, 2)


def recent_activity_cutoff():
    return to_naive_utc(utcnow() - timedelta(days=RECENT_ACTIVITY_WINDOW_DAYS))

