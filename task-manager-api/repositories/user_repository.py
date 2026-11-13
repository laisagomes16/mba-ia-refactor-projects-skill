"""Repositório de User — único ponto com queries de User."""
from database import db
from models.task import Task
from models.user import User


class UserRepository:
    @staticmethod
    def get_by_id(user_id):
        return db.session.get(User, user_id)

    @staticmethod
    def get_by_email(email):
        return User.query.filter(User.email == email).first()

    @staticmethod
    def list_all(limit=None, offset=None):
        query = User.query
        if limit is None:
            return query.all()
        return query.limit(limit).offset(offset or 0).all()

    @staticmethod
    def count_all():
        return db.session.scalar(db.select(db.func.count(User.id)))

    @staticmethod
    def save(user):
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def delete(user):
        db.session.delete(user)
        db.session.commit()

    @staticmethod
    def task_count(user_id):
        return Task.query.filter(Task.user_id == user_id).count()

    @staticmethod
    def task_counts_by_user():
        """Contagem de tasks por usuário em uma única query (FINDING-013).

        Antes o controller fazia `len(user.tasks)` por linha de `/users`, o que
        disparava um lazy load por usuário (1 + N queries).
        """
        rows = (db.session.query(Task.user_id, db.func.count(Task.id))
                .filter(Task.user_id.isnot(None))
                .group_by(Task.user_id)
                .all())
        return {user_id: count for user_id, count in rows}

