"""Controllers de User - apenas mapeamento HTTP."""
from flask import Blueprint, jsonify, request

from serializers import serialize_task_summary, serialize_user, serialize_user_summary
from services.task_service import TaskService
from services.user_service import UserService

user_bp = Blueprint('users', __name__)


@user_bp.route('/users', methods=['GET'])
def list_users():
    users = UserService.list_all()
    result = []
    for user in users:
        data = serialize_user_summary(user)
        data['task_count'] = len(user.tasks)
        result.append(data)
    return jsonify(result), 200


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = UserService.get(user_id)
    return jsonify(serialize_user(user, include_tasks=True)), 200


@user_bp.route('/users', methods=['POST'])
def create_user():
    user = UserService.create(request.get_json(silent=True) or {})
    return jsonify(serialize_user(user)), 201


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = UserService.update(user_id, request.get_json(silent=True) or {})
    return jsonify(serialize_user(user)), 200


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    UserService.delete(user_id)
    return jsonify({'message': 'Usuario deletado com sucesso'}), 200


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    tasks = TaskService.list_by_user(user_id)
    return jsonify([serialize_task_summary(task) for task in tasks]), 200


@user_bp.route('/login', methods=['POST'])
def login():
    payload = request.get_json(silent=True) or {}
    user, token = UserService.login(payload.get('email'), payload.get('password'))
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': serialize_user(user),
        'token': token,
    }), 200
