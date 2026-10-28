"""Regras de agregação para os relatórios (`/reports/*`).

Centraliza cálculos que antes estavam duplicados entre `report_routes.py` e
`task_routes.py` (FINDING-011/016), reaproveitando `Task.is_overdue()`.
"""
from repositories.category_repository import CategoryRepository
from repositories.task_repository import TaskRepository
from repositories.user_repository import UserRepository
from utils.helpers import (
    HIGH_PRIORITY_THRESHOLD,
    PRIORITY_LABELS,
    STATUS_CANCELLED,
    STATUS_DONE,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
    calculate_percentage,
    iso_utc,
    utcnow,
)


class ReportService:
    @staticmethod
    def summary():
        tasks = TaskRepository.list_all()
        users = UserRepository.list_all()
        done = sum(1 for task in tasks if task.status == STATUS_DONE)
        overdue_tasks = [task for task in tasks if task.is_overdue()]

        productivity = []
        for user in users:
            user_tasks = [task for task in tasks if task.user_id == user.id]
            completed = sum(1 for task in user_tasks if task.status == STATUS_DONE)
            productivity.append({
                'user_id': user.id,
                'user_name': user.name,
                'total_tasks': len(user_tasks),
                'completed_tasks': completed,
                'completion_rate': calculate_percentage(completed, len(user_tasks)),
            })

        return {
            'generated_at': iso_utc(utcnow()),
            'overview': {
                'total_tasks': len(tasks),
                'total_users': len(users),
                'total_categories': CategoryRepository.count_all(),
            },
            'tasks_by_status': {
                'pending': ReportService._count(tasks, STATUS_PENDING),
                'in_progress': ReportService._count(tasks, STATUS_IN_PROGRESS),
                'done': done,
                'cancelled': ReportService._count(tasks, STATUS_CANCELLED),
            },
            'tasks_by_priority': ReportService._count_by_priority(tasks),
            'overdue': {
                'count': len(overdue_tasks),
                'tasks': [ReportService._overdue_entry(task) for task in overdue_tasks],
            },
            'recent_activity': TaskRepository.recent_activity_counts(),
            'user_productivity': productivity,
        }

    @staticmethod
    def _count(tasks, status):
        return sum(1 for task in tasks if task.status == status)

    @staticmethod
    def _count_by_priority(tasks):
        counts = {label: 0 for label in PRIORITY_LABELS.values()}
        for task in tasks:
            label = PRIORITY_LABELS.get(task.priority, 'medium')
            counts[label] = counts.get(label, 0) + 1
        return counts

    @staticmethod
    def _overdue_entry(task):
        return {
            'id': task.id,
            'title': task.title,
            'due_date': str(task.due_date),
            'days_overdue': task.days_overdue(),
        }

    @staticmethod
    def user_statistics(user):
        tasks = TaskRepository.list_by_user(user.id)
        total = len(tasks)
        done = ReportService._count(tasks, STATUS_DONE)
        return {
            'user': {'id': user.id, 'name': user.name, 'email': user.email},
            'statistics': {
                'total_tasks': total,
                'done': done,
                'pending': ReportService._count(tasks, STATUS_PENDING),
                'in_progress': ReportService._count(tasks, STATUS_IN_PROGRESS),
                'cancelled': ReportService._count(tasks, STATUS_CANCELLED),
                'overdue': sum(1 for task in tasks if task.is_overdue()),
                'high_priority': sum(1 for task in tasks
                                     if task.priority <= HIGH_PRIORITY_THRESHOLD),
                'completion_rate': calculate_percentage(done, total),
            },
        }
