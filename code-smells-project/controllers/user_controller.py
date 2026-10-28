from flask import jsonify, request, g

from auth import require_admin, require_auth
from controllers.pagination import parse_pagination
from errors import AppError
from services.user_service import UserService

_service = UserService()


@require_admin
def listar_usuarios():
    limit, offset = parse_pagination()
    usuarios = _service.listar(limit=limit, offset=offset)
    return jsonify({"dados": usuarios, "sucesso": True}), 200



@require_auth
def buscar_usuario(id):
    current = g.current_user
    if current.get("tipo") != "admin" and int(id) != int(current["id"]):
        raise AppError("Acesso negado", 403)
    usuario = _service.obter(id)
    return jsonify({"dados": usuario, "sucesso": True}), 200


def criar_usuario():
    dados = request.get_json()
    user_id = _service.criar(dados)
    return jsonify({"dados": {"id": user_id}, "sucesso": True}), 201


def login():
    dados = request.get_json()
    usuario = _service.login(dados)
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
