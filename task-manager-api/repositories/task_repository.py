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
    def list_all():
        return TaskRepository._base_query().all()

    @staticmethod
    def list_by_user(user_id):
        return TaskRepository._base_query().filter(Task.user_id == user_id).all()

    @staticmethod
    def search(status=None, user_id=None, priority=None, category_id=None):
        query = TaskRepository._base_query()
        if status:
            query = query.filter(Task.status == status)
        if user_id:
            query = query.filter(Task.user_id == user_id)
        if priority:
            query = query.filter(Task.priority == priority)
        if category_id:
            query = query.filter(Task.category_id == category_id)
        return query.all()

    @staticmethod
    def search_by_term(term):
        pattern = '%{}%'.format(term)
        return TaskRepository._base_query().filter(
            or_(Task.title.like(pattern), Task.description.like(pattern))
        ).all()

    @staticmethod
    def list_overdue():
        """Atrasadas: due_date no passado e status não terminal."""
        return TaskRepository._base_query().filter(
            Task.due_date.isnot(None),
            Task.due_date < utcnow(),
            Task.status.notin_(TERMINAL_STATUSES),
        ).all()

    @staticmethod
    def count_by_status():
        rows = db.session.query(Task.status, db.func.count(Task.id)).group_by(Task.status).all()
        return {status: count for status, count in rows}

    @staticmethod
    def count_completed_since(since):
        return Task.query.filter(Task.status == 'done', Task.updated_at >= since).count()

    @staticmethod
    def count_created_since(since):
        return Task.query.filter(Task.created_at >= since).count()

    @staticmethod
    def count_all():
        return Task.query.count()

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

    @staticmethod
    def recent_activity_counts():
        cutoff = recent_activity_cutoff()
        return {
            'tasks_created_last_7_days': TaskRepository.count_created_since(cutoff),
            'tasks_completed_last_7_days': TaskRepository.count_completed_since(cutoff),
        }
