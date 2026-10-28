from flask import jsonify, request

from auth import require_auth
from controllers.pagination import parse_pagination
from errors import AppError
from services.product_service import ProductService

_service = ProductService()


def listar_produtos():
    limit, offset = parse_pagination()
    produtos = _service.listar(limit=limit, offset=offset)
    return jsonify({"dados": produtos, "sucesso": True}), 200



def buscar_produto(id):
    produto = _service.obter(id)
    return jsonify({"dados": produto, "sucesso": True}), 200


@require_auth
def criar_produto():
    dados = request.get_json()
    product_id = _service.criar(dados)
    return jsonify({"dados": {"id": product_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


@require_auth
def atualizar_produto(id):
    dados = request.get_json()
    _service.atualizar(id, dados)
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


@require_auth
def deletar_produto(id):
    _service.deletar(id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


def buscar_produtos():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria", None)
    preco_min = request.args.get("preco_min", None)
    preco_max = request.args.get("preco_max", None)
    try:
        preco_min = float(preco_min) if preco_min else None
        preco_max = float(preco_max) if preco_max else None
    except ValueError:
        raise AppError("Filtro de preço inválido")
    resultados = _service.buscar(termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
