from database import get_db
from models.order import order_to_dict


class OrderRepository:
    def create_with_items(self, usuario_id, total, items_data):
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
            (usuario_id, total),
        )
        pedido_id = cursor.lastrowid
        for item in items_data:
            cursor.execute(
                """
                INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario)
                VALUES (?, ?, ?, ?)
                """,
                (pedido_id, item["produto_id"], item["quantidade"], item["preco"]),
            )
            cursor.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                (item["quantidade"], item["produto_id"]),
            )
        db.commit()
        return pedido_id

    def get_by_id(self, pedido_id):
        cursor = get_db().cursor()
        cursor.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,))
        return cursor.fetchone()

    def list_by_usuario(self, usuario_id, limit=None, offset=0):
        sql = "SELECT * FROM pedidos WHERE usuario_id = ? ORDER BY id"
        params = [usuario_id]
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        return self._hydrate(sql, tuple(params))

    def list_all(self, limit=None, offset=0):
        sql = "SELECT * FROM pedidos ORDER BY id"
        params = []
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        return self._hydrate(sql, tuple(params))

    def update_status(self, pedido_id, novo_status):
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "UPDATE pedidos SET status = ? WHERE id = ?",
            (novo_status, pedido_id),
        )
        db.commit()
        return True

    def restore_stock_for_pedido(self, pedido_id):
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT produto_id, quantidade FROM itens_pedido WHERE pedido_id = ?",
            (pedido_id,),
        )
        itens = cursor.fetchall()
        for item in itens:
            cursor.execute(
                "UPDATE produtos SET estoque = estoque + ? WHERE id = ?",
                (item["quantidade"], item["produto_id"]),
            )
        db.commit()

    def sales_aggregates(self):
        cursor = get_db().cursor()
        cursor.execute("SELECT COUNT(*) FROM pedidos")
        total_pedidos = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(total) FROM pedidos")
        faturamento = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'")
        pendentes = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'aprovado'")
        aprovados = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'cancelado'")
        cancelados = cursor.fetchone()[0]
        return total_pedidos, faturamento, pendentes, aprovados, cancelados

    def _hydrate(self, pedidos_sql, params):
        db = get_db()
        cursor = db.cursor()
        cursor.execute(pedidos_sql, params)
        pedidos = cursor.fetchall()
        if not pedidos:
            return []

        ids = [row["id"] for row in pedidos]
        placeholders = ",".join("?" * len(ids))
        cursor.execute(
            """
            SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario, p.nome AS produto_nome
            FROM itens_pedido i
            LEFT JOIN produtos p ON p.id = i.produto_id
            WHERE i.pedido_id IN ("""
            + placeholders
            + """)
            """,
            tuple(ids),
        )
        itens_por_pedido = {}
        for item in cursor.fetchall():
            itens_por_pedido.setdefault(item["pedido_id"], []).append(
                {
                    "produto_id": item["produto_id"],
                    "produto_nome": item["produto_nome"] if item["produto_nome"] else "Desconhecido",
                    "quantidade": item["quantidade"],
                    "preco_unitario": item["preco_unitario"],
                }
            )

        result = []
        for row in pedidos:
            result.append(order_to_dict(row, itens_por_pedido.get(row["id"], [])))
        return result
