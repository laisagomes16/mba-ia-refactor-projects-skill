from flask import jsonify

from auth import require_admin
from controllers import (
    health_controller,
    order_controller,
    product_controller,
    user_controller,
)


def register_routes(app):
    app.add_url_rule("/produtos", "listar_produtos", product_controller.listar_produtos, methods=["GET"])
    app.add_url_rule("/produtos/busca", "buscar_produtos", product_controller.buscar_produtos, methods=["GET"])
    app.add_url_rule("/produtos/<int:id>", "buscar_produto", product_controller.buscar_produto, methods=["GET"])
    app.add_url_rule("/produtos", "criar_produto", product_controller.criar_produto, methods=["POST"])
    app.add_url_rule("/produtos/<int:id>", "atualizar_produto", product_controller.atualizar_produto, methods=["PUT"])
    app.add_url_rule("/produtos/<int:id>", "deletar_produto", product_controller.deletar_produto, methods=["DELETE"])

    app.add_url_rule("/usuarios", "listar_usuarios", user_controller.listar_usuarios, methods=["GET"])
    app.add_url_rule("/usuarios/<int:id>", "buscar_usuario", user_controller.buscar_usuario, methods=["GET"])
    app.add_url_rule("/usuarios", "criar_usuario", user_controller.criar_usuario, methods=["POST"])
    app.add_url_rule("/login", "login", user_controller.login, methods=["POST"])

    app.add_url_rule("/pedidos", "criar_pedido", order_controller.criar_pedido, methods=["POST"])
    app.add_url_rule("/pedidos", "listar_todos_pedidos", order_controller.listar_todos_pedidos, methods=["GET"])
    app.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario", order_controller.listar_pedidos_usuario, methods=["GET"])
    app.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido", order_controller.atualizar_status_pedido, methods=["PUT"])

    app.add_url_rule("/relatorios/vendas", "relatorio_vendas", order_controller.relatorio_vendas, methods=["GET"])
    app.add_url_rule("/health", "health_check", health_controller.health_check, methods=["GET"])

    app.add_url_rule(
        "/admin/reset-db",
        "reset_database",
        require_admin(health_controller.reset_database),
        methods=["POST"],
    )
    app.add_url_rule(
        "/admin/query",
        "executar_query",
        require_admin(health_controller.executar_query),
        methods=["POST"],
    )

    @app.route("/")
    def index():
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": "1.0.0",
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health"
            }
        })
