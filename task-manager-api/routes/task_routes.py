"""Controllers de Task - apenas mapeamento HTTP."""
from flask import Blueprint, jsonify, request

from serializers import serialize_task, serialize_task_with_relations
from services.task_service import TaskService

task_bp = Blueprint('tasks', __name__)


@task_bp.route('/tasks', methods=['GET'])
def list_tasks():
    tasks = TaskService.list_all()
    return jsonify([serialize_task_with_relations(task) for task in tasks]), 200


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = TaskService.get(task_id)
    return jsonify(serialize_task(task)), 200


@task_bp.route('/tasks', methods=['POST'])
def create_task():
    task = TaskService.create(request.get_json(silent=True) or {})
    return jsonify(serialize_task(task)), 201


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = TaskService.update(task_id, request.get_json(silent=True) or {})
    return jsonify(serialize_task(task)), 200


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    TaskService.delete(task_id)
    return jsonify({'message': 'Task deletada com sucesso'}), 200


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    tasks = TaskService.search(request.args)
    return jsonify([serialize_task(task) for task in tasks]), 200


@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    return jsonify(TaskService.statistics()), 200
