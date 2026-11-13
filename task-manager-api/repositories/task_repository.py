"""Repositório de Task — único ponto com queries de Task."""
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from database import db
from models.task import Task
from utils.helpers import TERMINAL_STATUSES, recent_activity_cutoff, utcnow


class TaskRepository:
    @staticmethod
    def _base_query():
        # joinedload evita N+1 ao serializar user_name/category_name (FINDING-012).
        return Task.query.options(joinedload(Task.user), joinedload(Task.category))

    @staticmethod
    def get_by_id(task_id):
        return db.session.get(Task, task_id)

    @staticmethod
    def get_by_id_with_relations(task_id):
        return TaskRepository._base_query().filter(Task.id == task_id).first()

    @staticmethod
    def list_all(limit=None, offset=None):
        return TaskRepository._page(TaskRepository._base_query(), limit, offset).all()

    @staticmethod
    def count_filtered(status=None, user_id=None, priority=None, category_id=None):
        query = Task.query
        if status:
            query = query.filter(Task.status == status)
        if user_id:
            query = query.filter(Task.user_id == user_id)
        if priority:
            query = query.filter(Task.priority == priority)
        if category_id:
            query = query.filter(Task.category_id == category_id)
        return query.count()

    @staticmethod
    def _page(query, limit=None, offset=None):
        """Aplica `LIMIT/OFFSET` apenas quando paginado (FINDING-015)."""
        if limit is None:
            return query
        return query.limit(limit).offset(offset or 0)

    @staticmethod
    def list_by_user(user_id, limit=None, offset=None):
        query = TaskRepository._base_query().filter(Task.user_id == user_id)
        return TaskRepository._page(query, limit, offset).all()

    @staticmethod
    def search(status=None, user_id=None, priority=None, category_id=None,
               limit=None, offset=None):
        query = TaskRepository._base_query()
        if status:
            query = query.filter(Task.status == status)
        if user_id:
            query = query.filter(Task.user_id == user_id)
        if priority:
            query = query.filter(Task.priority == priority)
        if category_id:
            query = query.filter(Task.category_id == category_id)
        return TaskRepository._page(query, limit, offset).all()

    @staticmethod
    def search_by_term(term, limit=None, offset=None):
        pattern = '%{}%'.format(term)
        query = TaskRepository._base_query().filter(
            or_(Task.title.like(pattern), Task.description.like(pattern))
        )
        return TaskRepository._page(query, limit, offset).all()

    @staticmethod
    def count_by_term(term):
        pattern = '%{}%'.format(term)
        return Task.query.filter(
            or_(Task.title.like(pattern), Task.description.like(pattern))
        ).count()

    @staticmethod
    def list_overdue():
        """Atrasadas: due_date no passado e status não terminal."""
        return TaskRepository._base_query().filter(
            Task.due_date.isnot(None),
            Task.due_date < utcnow(),
            Task.status.notin_(TERMINAL_STATUSES),
        ).all()

    @staticmethod
    def list_overdue_projection():
        """Atrasadas sem os relacionamentos — só o necessário para o relatório.

        Evita carregar o grafo inteiro (user/category) que `list_overdue()`
        traz via `joinedload` apenas para montar `id/title/due_date`
        (FINDING-014). A regra de atraso continua vindo de `TERMINAL_STATUSES`.
        """
        return Task.query.with_entities(
            Task.id, Task.title, Task.due_date
        ).filter(
            Task.due_date.isnot(None),
            Task.due_date < utcnow(),
            Task.status.notin_(TERMINAL_STATUSES),
        ).all()

    @staticmethod
    def count_by_status():
        rows = db.session.query(Task.status, db.func.count(Task.id)).group_by(Task.status).all()
        return {status: count for status, count in rows}

    @staticmethod
    def count_by_priority():
        rows = (db.session.query(Task.priority, db.func.count(Task.id))
                .group_by(Task.priority)
                .all())
        return {priority: count for priority, count in rows}

    @staticmethod
    def count_overdue():
        """Contagem de atrasadas direto no banco (FINDING-014)."""
        return db.session.scalar(
            db.select(db.func.count(Task.id)).where(
                Task.due_date.isnot(None),
                Task.due_date < utcnow(),
                Task.status.notin_(TERMINAL_STATUSES),
            )
        )

    @staticmethod
    def count_by_user_status():
        """Agregação `(user_id, status) -> count` em uma query (FINDING-013)."""
        rows = (db.session.query(Task.user_id, Task.status, db.func.count(Task.id))
                .filter(Task.user_id.isnot(None))
                .group_by(Task.user_id, Task.status)
                .all())
        return {(user_id, status): count for user_id, status, count in rows}


    @staticmethod
    def count_completed_since(since):
        # Agregação escalar (FINDING-014): `Query.count()` envolve um
        # `SELECT count(*) FROM (SELECT ...)`; aqui o banco conta direto.
        return db.session.scalar(
            db.select(db.func.count(Task.id)).where(Task.status == 'done', Task.updated_at >= since)
        )

    @staticmethod
    def count_created_since(since):
        return db.session.scalar(
            db.select(db.func.count(Task.id)).where(Task.created_at >= since)
        )

    @staticmethod
    def count_all():
        return db.session.scalar(db.select(db.func.count(Task.id)))

    @staticmethod
    def save(task):
        db.session.add(task)
        db.session.commit()
        return task

    @staticmethod
    def delete(task):
        db.session.delete(task)
        db.session.commit()

    @staticmethod
    def delete_by_user(user_id):
        Task.query.filter(Task.user_id == user_id).delete(synchronize_session=False)
        db.session.commit()

    @staticmethod
    def recent_activity_counts():
        cutoff = recent_activity_cutoff()
        return {
            'tasks_created_last_7_days': TaskRepository.count_created_since(cutoff),
            'tasks_completed_last_7_days': TaskRepository.count_completed_since(cutoff),
        }
