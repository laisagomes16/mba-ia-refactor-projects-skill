"""Controllers de Category - extraidos de report_routes.py (FINDING-010)."""
from flask import Blueprint, jsonify, request

from serializers import serialize_category
from services.category_service import CategoryService

category_bp = Blueprint('categories', __name__)


@category_bp.route('/categories', methods=['GET'])
def list_categories():
    categories = CategoryService.list_all()
    result = []
    for category in categories:
        data = serialize_category(category)
        data['task_count'] = len(category.tasks)
        result.append(data)
    return jsonify(result), 200


@category_bp.route('/categories', methods=['POST'])
def create_category():
    category = CategoryService.create(request.get_json(silent=True) or {})
    return jsonify(serialize_category(category)), 201


@category_bp.route('/categories/<int:cat_id>', methods=['PUT'])
def update_category(cat_id):
    category = CategoryService.update(cat_id, request.get_json(silent=True) or {})
    return jsonify(serialize_category(category)), 200


@category_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    CategoryService.delete(cat_id)
    return jsonify({'message': 'Categoria deletada'}), 200
