"""Controllers de User - apenas mapeamento HTTP."""
from flask import Blueprint, jsonify, request

from middleware.auth import require_auth, require_admin, require_self_or_admin
from serializers import serialize_task_summary, serialize_user, serialize_user_summary
from services.task_service import TaskService
from services.user_service import UserService
from utils.helpers import paginated, parse_pagination

user_bp = Blueprint('users', __name__)


@user_bp.route('/users', methods=['GET'])
@require_auth
def list_users():
    pagination = parse_pagination(request.args)
    users = UserService.list_all(pagination)
    task_counts = UserService.task_counts()
    result = []
    for user in users:
        data = serialize_user_summary(user)
        data['task_count'] = task_counts.get(user.id, 0)
        result.append(data)
    if pagination is not None:
        return jsonify(paginated(result, UserService.count(pagination), pagination)), 200
    return jsonify(result), 200


@user_bp.route('/users/<int:user_id>', methods=['GET'])
@require_auth
def get_user(user_id):
    user = UserService.get(user_id)
    return jsonify(serialize_user(user, include_tasks=True)), 200


@user_bp.route('/users', methods=['POST'])
@require_admin
def create_user():
    user = UserService.create(request.get_json(silent=True) or {})
    return jsonify(serialize_user(user)), 201


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@require_self_or_admin
def update_user(user_id):
    user = UserService.update(user_id, request.get_json(silent=True) or {})
    return jsonify(serialize_user(user)), 200


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@require_self_or_admin
def delete_user(user_id):
    UserService.delete(user_id)
    return jsonify({'message': 'Usuario deletado com sucesso'}), 200


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
@require_auth
def get_user_tasks(user_id):
    pagination = parse_pagination(request.args)
    tasks = TaskService.list_by_user(user_id, pagination)
    result = [serialize_task_summary(task) for task in tasks]
    if pagination is not None:
        total = TaskService.count(pagination, {'user_id': user_id})
        return jsonify(paginated(result, total, pagination)), 200
    return jsonify(result), 200


@user_bp.route('/login', methods=['POST'])
def login():
    payload = request.get_json(silent=True) or {}
    user, token = UserService.login(payload.get('email'), payload.get('password'))
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': serialize_user(user),
        'token': token,
    }), 200
