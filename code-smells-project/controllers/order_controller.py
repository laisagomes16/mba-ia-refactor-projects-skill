from flask import jsonify, request, g

from auth import require_admin, require_auth
from controllers.pagination import parse_pagination
from services.order_service import OrderService
from services.report_service import ReportService

_orders = OrderService()
_reports = ReportService()


@require_auth
def criar_pedido():
    dados = request.get_json()
    resultado = _orders.criar(dados, g.current_user)
    if "erro" in resultado:
        return jsonify({"erro": resultado["erro"], "sucesso": False}), 400
    return jsonify({
        "dados": resultado,
        "sucesso": True,
        "mensagem": "Pedido criado com sucesso"
    }), 201


@require_auth
def listar_pedidos_usuario(usuario_id):
    limit, offset = parse_pagination()
    pedidos = _orders.listar_usuario(usuario_id, g.current_user, limit=limit, offset=offset)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


@require_auth
def listar_todos_pedidos():
    limit, offset = parse_pagination()
    pedidos = _orders.listar_todos(g.current_user, limit=limit, offset=offset)
    return jsonify({"dados": pedidos, "sucesso": True}), 200



@require_admin
def atualizar_status_pedido(pedido_id):
    dados = request.get_json()
    _orders.atualizar_status(pedido_id, dados)
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200


@require_admin
def relatorio_vendas():
    relatorio = _reports.vendas()
    return jsonify({"dados": relatorio, "sucesso": True}), 200
