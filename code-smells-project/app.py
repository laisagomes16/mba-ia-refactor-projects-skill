import logging

from flask import Flask
from flask_cors import CORS

from config import Config
from database import get_db, init_app
from errors import register_error_handlers
from routes import register_routes

logging.basicConfig(level=logging.INFO)


def create_app():
    application = Flask(__name__)
    application.config["SECRET_KEY"] = Config.SECRET_KEY
    application.config["DEBUG"] = Config.DEBUG
    CORS(application, origins=Config.CORS_ORIGINS)
    init_app(application)
    register_error_handlers(application)
    register_routes(application)
    return application


app = create_app()

if __name__ == "__main__":
    with app.app_context():
        get_db()
    print("=" * 50)
    print("SERVIDOR INICIADO")
    print("Rodando em http://%s:%s" % (Config.HOST, Config.PORT))
    print("=" * 50)
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
