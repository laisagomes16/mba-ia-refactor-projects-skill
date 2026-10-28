"""Bootstrap da aplicação — app factory sem efeitos colaterais no import."""
from flask import Flask
from flask_cors import CORS

from config import Config
from database import db
from error_handlers import register_error_handlers
from routes.category_routes import category_bp
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from utils.helpers import iso_utc, utcnow


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    CORS(app)
    db.init_app(app)

    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(category_bp)

    register_error_handlers(app)

    @app.route('/health')
    def health():
        return {'status': 'ok', 'timestamp': iso_utc(utcnow())}

    @app.route('/')
    def index():
        return {'message': 'Task Manager API', 'version': '1.0'}

    return app


def init_database(app):
    """Cria o schema de forma explícita (não como efeito colateral do import)."""
    with app.app_context():
        db.create_all()


if __name__ == '__main__':
    application = create_app()
    init_database(application)
    application.run(
        debug=application.config['DEBUG'],
        host=application.config['HOST'],
        port=application.config['PORT'],
    )

