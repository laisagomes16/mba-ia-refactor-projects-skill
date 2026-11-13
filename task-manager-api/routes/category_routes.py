"""Controllers de Category - extraidos de report_routes.py (FINDING-010)."""
from flask import Blueprint, jsonify, request

from middleware.auth import require_admin, require_auth
from serializers import serialize_category
from services.category_service import CategoryService
from utils.helpers import paginated, parse_pagination

category_bp = Blueprint('categories', __name__)


@category_bp.route('/categories', methods=['GET'])
@require_auth
def list_categories():
    pagination = parse_pagination(request.args)
    categories = CategoryService.list_all(pagination)
    result = []
    for category in categories:
        data = serialize_category(category)
        data['task_count'] = len(category.tasks)
        result.append(data)
    if pagination is not None:
        return jsonify(paginated(result, CategoryService.count(pagination), pagination)), 200
    return jsonify(result), 200


@category_bp.route('/categories', methods=['POST'])
@require_admin
def create_category():
    category = CategoryService.create(request.get_json(silent=True) or {})
    return jsonify(serialize_category(category)), 201


@category_bp.route('/categories/<int:cat_id>', methods=['PUT'])
@require_admin
def update_category(cat_id):
    category = CategoryService.update(cat_id, request.get_json(silent=True) or {})
    return jsonify(serialize_category(category)), 200


@category_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
@require_admin
def delete_category(cat_id):
    CategoryService.delete(cat_id)
    return jsonify({'message': 'Categoria deletada'}), 200
