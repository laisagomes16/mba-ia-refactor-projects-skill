"""Regras de negócio de Category."""
from errors import NotFoundError, ValidationError
from models.category import Category
from repositories.category_repository import CategoryRepository
from utils.helpers import DEFAULT_COLOR, DEFAULT_DESCRIPTION

MSG_CATEGORY_NOT_FOUND = 'Categoria não encontrada'
MSG_INVALID_DATA = 'Dados inválidos'
MSG_NAME_REQUIRED = 'Nome é obrigatório'
MSG_INVALID_COLOR = 'Cor inválida'


class CategoryService:
    @staticmethod
    def get(category_id):
        category = CategoryRepository.get_by_id(category_id)
        if not category:
            raise NotFoundError(MSG_CATEGORY_NOT_FOUND)
        return category

    @staticmethod
    def list_all():
        return CategoryRepository.list_all_with_tasks()

    @staticmethod
    def _validate_name(name):
        if not name:
            raise ValidationError(MSG_NAME_REQUIRED)
        return name

    @staticmethod
    def _validate_color(color):
        if not Category.is_valid_color(color):
            raise ValidationError(MSG_INVALID_COLOR)
        return color

    @classmethod
    def create(cls, payload):
        if not payload:
            raise ValidationError(MSG_INVALID_DATA)

        category = Category(
            name=cls._validate_name(payload.get('name')),
            description=payload.get('description', DEFAULT_DESCRIPTION),
            color=payload.get('color', DEFAULT_COLOR),
        )
        cls._validate_color(category.color)
        return CategoryRepository.save(category)

    @classmethod
    def update(cls, category_id, payload):
        category = cls.get(category_id)

        if 'name' in payload:
            category.name = cls._validate_name(payload['name'])
        if 'description' in payload:
            category.description = payload['description']
        if 'color' in payload:
            category.color = cls._validate_color(payload['color'])

        return CategoryRepository.save(category)

    @classmethod
    def delete(cls, category_id):
        category = cls.get(category_id)
        CategoryRepository.delete(category)
        return category
