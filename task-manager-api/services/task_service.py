"""Regras de negócio de Task — sem HTTP, sem SQL."""
from errors import NotFoundError, ValidationError
from models.task import Task
from repositories.category_repository import CategoryRepository
from repositories.task_repository import TaskRepository
from repositories.user_repository import UserRepository
from utils.helpers import (
    DEFAULT_DESCRIPTION,
    DEFAULT_PRIORITY,
    MAX_TITLE_LENGTH,
    MIN_TITLE_LENGTH,
    STATUS_PENDING,
    parse_date,
)

MSG_TASK_NOT_FOUND = 'Task não encontrada'
MSG_USER_NOT_FOUND = 'Usuário não encontrado'
MSG_INVALID_DATE = 'Formato de data inválido. Use YYYY-MM-DD'
MSG_TITLE_TOO_SHORT = 'Título muito curto'
MSG_TITLE_TOO_LONG = 'Título deve ter no máximo {} caracteres'.format(MAX_TITLE_LENGTH)
MSG_INVALID_STATUS = 'Status inválido'
MSG_INVALID_PRIORITY = 'Prioridade deve ser entre 1 e 5'
MSG_INVALID_CATEGORY = 'Categoria não encontrada'


def _as_int(value):
    if value in (None, ''):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class TaskService:
    # ----- leitura -----

    @staticmethod
    def get(task_id):
        task = TaskRepository.get_by_id_with_relations(task_id)
        if not task:
            raise NotFoundError(MSG_TASK_NOT_FOUND)
        return task

    @staticmethod
    def list_all():
        return TaskRepository.list_all()

    @staticmethod
    def list_by_user(user_id):
        if not UserRepository.get_by_id(user_id):
            raise NotFoundError(MSG_USER_NOT_FOUND)
        return TaskRepository.list_by_user(user_id)

    @staticmethod
    def search(args):
        term = args.get('q')
        if term:
            return TaskRepository.search_by_term(term)
        return TaskRepository.search(
            status=args.get('status'),
            user_id=_as_int(args.get('user_id')),
            priority=_as_int(args.get('priority')),
            category_id=_as_int(args.get('category_id')),
        )

    # ----- validação -----

    @staticmethod
    def _validate_title(title):
        if not isinstance(title, str) or len(title) < MIN_TITLE_LENGTH:
            raise ValidationError(MSG_TITLE_TOO_SHORT)
        if len(title) > MAX_TITLE_LENGTH:
            raise ValidationError(MSG_TITLE_TOO_LONG)

    @staticmethod
    def _validate_status(status):
        if not Task.is_valid_status(status):
            raise ValidationError(MSG_INVALID_STATUS)

    @staticmethod
    def _validate_priority(priority):
        if not Task.is_valid_priority(priority):
            raise ValidationError(MSG_INVALID_PRIORITY)

    @staticmethod
    def _validate_due_date(raw):
        parsed = parse_date(raw)
        if parsed is None:
            raise ValidationError(MSG_INVALID_DATE)
        return parsed

    @staticmethod
    def _validate_user(user_id):
        if not UserRepository.get_by_id(user_id):
            raise NotFoundError(MSG_USER_NOT_FOUND)
        return user_id

    @staticmethod
    def _validate_category(category_id):
        if not CategoryRepository.get_by_id(category_id):
            raise NotFoundError(MSG_INVALID_CATEGORY)
        return category_id

    # ----- escrita -----

    @classmethod
    def create(cls, payload):
        title = payload.get('title')
        cls._validate_title(title)

        task = Task(
            title=title,
            description=payload.get('description', DEFAULT_DESCRIPTION),
            status=payload.get('status', STATUS_PENDING),
            priority=payload.get('priority', DEFAULT_PRIORITY),
            user_id=payload.get('user_id'),
            category_id=payload.get('category_id'),
        )
        cls._validate_status(task.status)
        cls._validate_priority(task.priority)

        if task.user_id is not None:
            cls._validate_user(task.user_id)
        if task.category_id is not None:
            cls._validate_category(task.category_id)

        if payload.get('due_date'):
            task.due_date = cls._validate_due_date(payload['due_date'])
        if 'tags' in payload:
            task.set_tags(payload['tags'])

        return TaskRepository.save(task)

    @classmethod
    def update(cls, task_id, payload):
        task = cls.get(task_id)

        if 'title' in payload:
            cls._validate_title(payload['title'])
            task.title = payload['title']
        if 'description' in payload:
            task.description = payload['description']
        if 'status' in payload:
            cls._validate_status(payload['status'])
            task.status = payload['status']
        if 'priority' in payload:
            cls._validate_priority(payload['priority'])
            task.priority = payload['priority']
        if 'user_id' in payload:
            if payload['user_id'] is not None:
                cls._validate_user(payload['user_id'])
            task.user_id = payload['user_id']
        if 'category_id' in payload:
            if payload['category_id'] is not None:
                cls._validate_category(payload['category_id'])
            task.category_id = payload['category_id']
        if 'due_date' in payload:
            task.due_date = (cls._validate_due_date(payload['due_date'])
                             if payload['due_date'] else None)
        if 'tags' in payload:
            task.set_tags(payload['tags'])

        return TaskRepository.save(task)

    @classmethod
    def delete(cls, task_id):
        task = cls.get(task_id)
        TaskRepository.delete(task)
        return task

    @staticmethod
    def delete_by_user(user_id):
        TaskRepository.delete_by_user(user_id)

    # ----- estatísticas -----

    @staticmethod
    def statistics():
        counts = TaskRepository.count_by_status()
        total = sum(counts.values())
        done = counts.get('done', 0)
        overdue = len(TaskRepository.list_overdue())
        return {
            'total': total,
            'pending': counts.get('pending', 0),
            'in_progress': counts.get('in_progress', 0),
            'done': done,
            'cancelled': counts.get('cancelled', 0),
            'overdue': overdue,
            'completion_rate': round((done / total) * 100, 2) if total else 0,
        }
