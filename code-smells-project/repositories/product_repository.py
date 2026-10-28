from database import get_db
from models.product import product_to_dict


class ProductRepository:
    def list_all(self, limit=None, offset=0):
        cursor = get_db().cursor()
        query = (
            "SELECT id, nome, descricao, preco, estoque, categoria, ativo, criado_em "
            "FROM produtos ORDER BY id"
        )
        params = []
        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        cursor.execute(query, params)
        return [product_to_dict(row) for row in cursor.fetchall()]

    def get_by_id(self, product_id):
        cursor = get_db().cursor()
        cursor.execute(
            "SELECT id, nome, descricao, preco, estoque, categoria, ativo, criado_em FROM produtos WHERE id = ?",
            (product_id,),
        )
        return product_to_dict(cursor.fetchone())

    def get_row_by_id(self, product_id):
        cursor = get_db().cursor()
        cursor.execute("SELECT * FROM produtos WHERE id = ?", (product_id,))
        return cursor.fetchone()

    def create(self, nome, descricao, preco, estoque, categoria):
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
        db.commit()
        return cursor.lastrowid

    def update(self, product_id, nome, descricao, preco, estoque, categoria):
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """
            UPDATE produtos
            SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ?
            WHERE id = ?
            """,
            (nome, descricao, preco, estoque, categoria, product_id),
        )
        db.commit()
        return True

    def delete(self, product_id):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM produtos WHERE id = ?", (product_id,))
        db.commit()
        return True

    def search(self, termo, categoria=None, preco_min=None, preco_max=None):
        cursor = get_db().cursor()
        query = "SELECT id, nome, descricao, preco, estoque, categoria, ativo, criado_em FROM produtos WHERE 1=1"
        params = []
        if termo:
            query += " AND (nome LIKE ? OR descricao LIKE ?)"
            like = "%" + termo + "%"
            params.extend([like, like])
        if categoria:
            query += " AND categoria = ?"
            params.append(categoria)
        if preco_min is not None:
            query += " AND preco >= ?"
            params.append(preco_min)
        if preco_max is not None:
            query += " AND preco <= ?"
            params.append(preco_max)
        cursor.execute(query, params)
        return [product_to_dict(row) for row in cursor.fetchall()]

    def list_by_ids(self, ids):
        if not ids:
            return []
        cursor = get_db().cursor()
        placeholders = ",".join("?" * len(ids))
        cursor.execute(
            "SELECT * FROM produtos WHERE id IN (" + placeholders + ")",
            tuple(ids),
        )
        return cursor.fetchall()
