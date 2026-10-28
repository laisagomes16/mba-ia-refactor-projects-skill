from errors import AppError
from models.constants import STATUS_PEDIDO_VALIDOS
from repositories.order_repository import OrderRepository
from repositories.product_repository import ProductRepository
from services.notification_service import NotificationService


class OrderService:
    def __init__(self, order_repo=None, product_repo=None, notifications=None):
        self.order_repo = order_repo or OrderRepository()
        self.product_repo = product_repo or ProductRepository()
        self.notifications = notifications or NotificationService()

    def criar(self, dados, current_user=None):
        if not dados:
            raise AppError("Dados inválidos")
        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens", [])
        if not usuario_id:
            raise AppError("Usuario ID é obrigatório")
        if not itens or len(itens) == 0:
            raise AppError("Pedido deve ter pelo menos 1 item")

        if current_user and current_user.get("tipo") != "admin":
            if int(usuario_id) != int(current_user["id"]):
                raise AppError("Acesso negado", 403)

        for item in itens:
            if "produto_id" not in item or "quantidade" not in item:
                raise AppError("Cada item precisa de produto_id e quantidade")

        ids = [item["produto_id"] for item in itens]
        rows = self.product_repo.list_by_ids(ids)
        by_id = {row["id"]: row for row in rows}

        total = 0
        items_data = []
        for item in itens:
            produto = by_id.get(item["produto_id"])
            if produto is None:
                return {"erro": "Produto " + str(item["produto_id"]) + " não encontrado"}
            if produto["estoque"] < item["quantidade"]:
                return {"erro": "Estoque insuficiente para " + produto["nome"]}
            total = total + (produto["preco"] * item["quantidade"])
            items_data.append(
                {
                    "produto_id": item["produto_id"],
                    "quantidade": item["quantidade"],
                    "preco": produto["preco"],
                }
            )

        pedido_id = self.order_repo.create_with_items(usuario_id, total, items_data)
        self.notifications.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}

    def listar_usuario(self, usuario_id, current_user, limit=None, offset=0):
        if current_user.get("tipo") != "admin" and int(usuario_id) != int(current_user["id"]):
            raise AppError("Acesso negado", 403)
        return self.order_repo.list_by_usuario(usuario_id, limit=limit, offset=offset)

    def listar_todos(self, current_user, limit=None, offset=0):
        if current_user.get("tipo") != "admin":
            return self.order_repo.list_by_usuario(
                current_user["id"], limit=limit, offset=offset
            )
        return self.order_repo.list_all(limit=limit, offset=offset)

    def atualizar_status(self, pedido_id, dados):
        if not dados:
            raise AppError("Dados inválidos")
        novo_status = dados.get("status", "")
        if novo_status not in STATUS_PEDIDO_VALIDOS:
            raise AppError("Status inválido")

        pedido = self.order_repo.get_by_id(pedido_id)
        if pedido is None:
            raise AppError("Pedido não encontrado", 404)

        anterior = pedido["status"]
        self.order_repo.update_status(pedido_id, novo_status)
        if novo_status == "cancelado" and anterior != "cancelado":
            self.order_repo.restore_stock_for_pedido(pedido_id)
        self.notifications.status_alterado(pedido_id, novo_status)
