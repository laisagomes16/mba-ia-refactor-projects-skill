import logging

logger = logging.getLogger("loja.notifications")


class NotificationService:
    def pedido_criado(self, pedido_id, usuario_id):
        logger.info("Pedido %s criado para usuario %s", pedido_id, usuario_id)

    def status_alterado(self, pedido_id, novo_status):
        if novo_status == "aprovado":
            logger.info("Pedido %s aprovado", pedido_id)
        elif novo_status == "cancelado":
            logger.info("Pedido %s cancelado", pedido_id)
