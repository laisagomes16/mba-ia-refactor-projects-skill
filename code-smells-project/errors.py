from flask import jsonify


class AppError(Exception):
    def __init__(self, message, status=400, extra=None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.extra = extra or {}


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        payload = {"erro": err.message, "sucesso": False}
        payload.update(err.extra)
        return jsonify(payload), err.status

    @app.errorhandler(404)
    def handle_404(_err):
        return jsonify({"erro": "Não encontrado", "sucesso": False}), 404

    @app.errorhandler(405)
    def handle_405(_err):
        return jsonify({"erro": "Método não permitido", "sucesso": False}), 405

    @app.errorhandler(Exception)
    def handle_unexpected(_err):
        app.logger.exception("Unhandled error")
        return jsonify({"erro": "Erro interno"}), 500
