def order_to_dict(pedido_row, itens):
    return {
        "id": pedido_row["id"],
        "usuario_id": pedido_row["usuario_id"],
        "status": pedido_row["status"],
        "total": pedido_row["total"],
        "criado_em": pedido_row["criado_em"],
        "itens": itens,
    }
