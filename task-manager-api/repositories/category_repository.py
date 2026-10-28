"""Repositório de Category — único ponto com queries de Category."""
from sqlalchemy.orm import joinedload

from database import db
from models.category import Category


class CategoryRepository:
    @staticmethod
    def get_by_id(category_id):
        return db.session.get(Category, category_id)

    @staticmethod
    def get_by_name(name):
        return Category.query.filter(Category.name == name).first()

    @staticmethod
    def list_all_with_tasks():
        # joinedload evita N+1 no contador de tasks por categoria (FINDING-012).
        return Category.query.options(joinedload(Category.tasks)).all()

    @staticmethod
    def count_all():
        return Category.query.count()

    @staticmethod
    def save(category):
        db.session.add(category)
        db.session.commit()
        return category

    @staticmethod
    def delete(category):
        db.session.delete(category)
        db.session.commit()
