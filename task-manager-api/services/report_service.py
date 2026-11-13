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
        # Agregações em SQL (FINDING-014): nenhuma varredura full-table em memória.
        status_counts = TaskRepository.count_by_status()
        priority_counts = TaskRepository.count_by_priority()
        total_tasks = sum(status_counts.values())
        done = status_counts.get(STATUS_DONE, 0)
        overdue_rows = TaskRepository.list_overdue_projection()

        return {
            'generated_at': iso_utc(utcnow()),
            'overview': {
                'total_tasks': total_tasks,
                'total_users': UserRepository.count_all(),
                'total_categories': CategoryRepository.count_all(),
            },
            'tasks_by_status': {
                'pending': status_counts.get(STATUS_PENDING, 0),
                'in_progress': status_counts.get(STATUS_IN_PROGRESS, 0),
                'done': done,
                'cancelled': status_counts.get(STATUS_CANCELLED, 0),
            },
            'tasks_by_priority': ReportService._priority_breakdown(priority_counts),
            'overdue': {
                'count': len(overdue_rows),
                'tasks': [ReportService._overdue_entry(row) for row in overdue_rows],
            },
            'recent_activity': TaskRepository.recent_activity_counts(),
            'user_productivity': ReportService._user_productivity(),
        }

    @staticmethod
    def _priority_breakdown(priority_counts):
        """Mesmo formato de antes (`critical/high/medium/low/minimal`), via GROUP BY."""
        breakdown = {label: 0 for label in PRIORITY_LABELS.values()}
        for priority, count in priority_counts.items():
            label = PRIORITY_LABELS.get(priority, 'medium')
            breakdown[label] = breakdown.get(label, 0) + count
        return breakdown

    @staticmethod
    def _user_productivity():
        """Produtividade por usuário com duas agregações (FINDING-013).

        Antes: `[task for task in tasks if task.user_id == user.id]` por usuário
        depois de carregar a tabela inteira de tasks.
        """
        users = UserRepository.list_all()
        by_user_status = TaskRepository.count_by_user_status()
        productivity = []
        for user in users:
            total = sum(count for (user_id, _), count in by_user_status.items()
                        if user_id == user.id)
            completed = by_user_status.get((user.id, STATUS_DONE), 0)
            productivity.append({
                'user_id': user.id,
                'user_name': user.name,
                'total_tasks': total,
                'completed_tasks': completed,
                'completion_rate': calculate_percentage(completed, total),
            })
        return productivity

    @staticmethod
    def _overdue_entry(row):
        task_id, title, due_date = row
        return {
            'id': task_id,
            'title': title,
            'due_date': str(due_date),
            'days_overdue': ReportService._days_overdue(due_date),
        }

    @staticmethod
    def _days_overdue(due_date):
        """Mesma regra de `Task.days_overdue()` para uma linha já filtrada como atrasada."""
        if due_date is None:
            return 0
        return (utcnow() - due_date).days

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
