from flask import jsonify

from config import Config
from database import health_counts, reset_all_tables
from errors import AppError


def health_check():
    produtos, usuarios, pedidos = health_counts()
    return jsonify({
        "status": "ok",
        "database": "connected",
        "counts": {
            "produtos": produtos,
            "usuarios": usuarios,
            "pedidos": pedidos
        },
        "versao": Config.APP_VERSION
    }), 200


def reset_database():
    reset_all_tables()
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


def executar_query():
    raise AppError("Execução de SQL arbitrário desativada", 403)
