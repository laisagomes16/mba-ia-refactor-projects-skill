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
    def list_all():
        return User.query.all()

    @staticmethod
    def count_all():
        return User.query.count()

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
