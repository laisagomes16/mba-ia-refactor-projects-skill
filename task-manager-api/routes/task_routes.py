"""Controllers de Task - apenas mapeamento HTTP."""
from flask import Blueprint, jsonify, request

from middleware.auth import require_auth
from serializers import serialize_task, serialize_task_with_relations
from services.task_service import TaskService
from utils.helpers import paginated, parse_pagination

task_bp = Blueprint('tasks', __name__)


@task_bp.route('/tasks', methods=['GET'])
@require_auth
def list_tasks():
    pagination = parse_pagination(request.args)
    tasks = TaskService.list_all(pagination)
    result = [serialize_task_with_relations(task) for task in tasks]
    if pagination is not None:
        return jsonify(paginated(result, TaskService.count(pagination), pagination)), 200
    return jsonify(result), 200


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
@require_auth
def get_task(task_id):
    task = TaskService.get(task_id)
    return jsonify(serialize_task(task)), 200


@task_bp.route('/tasks', methods=['POST'])
@require_auth
def create_task():
    task = TaskService.create(request.get_json(silent=True) or {})
    return jsonify(serialize_task(task)), 201


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@require_auth
def update_task(task_id):
    task = TaskService.update(task_id, request.get_json(silent=True) or {})
    return jsonify(serialize_task(task)), 200


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@require_auth
def delete_task(task_id):
    TaskService.delete(task_id)
    return jsonify({'message': 'Task deletada com sucesso'}), 200


@task_bp.route('/tasks/search', methods=['GET'])
@require_auth
def search_tasks():
    pagination = parse_pagination(request.args)
    tasks = TaskService.search(request.args, pagination)
    result = [serialize_task(task) for task in tasks]
    if pagination is not None:
        total = TaskService.count(pagination, {'q': request.args.get('q')})
        return jsonify(paginated(result, total, pagination)), 200
    return jsonify(result), 200


@task_bp.route('/tasks/stats', methods=['GET'])
@require_auth
def task_stats():
    return jsonify(TaskService.statistics()), 200
