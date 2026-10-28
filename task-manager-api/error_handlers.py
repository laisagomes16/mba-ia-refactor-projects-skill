"""Registro central de error handlers (FINDING-018)."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from errors import AppError

logger = logging.getLogger(__name__)

# Mensagens de fallback preservadas do comportamento anterior.
_HTTP_FALLBACKS = {
    400: "Dados inválidos",
    404: "Recurso não encontrado",
    405: "Método não permitido",
}


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        logger.warning("domain error (%s): %s", error.status_code, error.message)
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        message = _HTTP_FALLBACKS.get(error.code, error.description)
        return jsonify({"error": message}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        # Loga o stack trace no servidor; nunca devolve trace ao cliente.
        logger.exception("unhandled error: %s", error)
        return jsonify({"error": "Erro interno"}), 500
