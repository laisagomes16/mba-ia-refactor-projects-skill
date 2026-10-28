"""Camada de controllers (blueprints Flask)."""
from routes.category_routes import category_bp
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp

__all__ = ['category_bp', 'report_bp', 'task_bp', 'user_bp']


