"""Controllers de relatorios - apenas mapeamento HTTP."""
from flask import Blueprint, jsonify

from services.report_service import ReportService
from services.user_service import UserService

report_bp = Blueprint('reports', __name__)


@report_bp.route('/reports/summary', methods=['GET'])
def summary_report():
    return jsonify(ReportService.summary()), 200


@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
def user_report(user_id):
    user = UserService.get(user_id)
    return jsonify(ReportService.user_statistics(user)), 200
