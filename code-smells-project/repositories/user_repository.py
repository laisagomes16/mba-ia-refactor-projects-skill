from auth import hash_password
from database import get_db
from errors import AppError
from models.user import user_public_dict


class UserRepository:
    def list_all(self, limit=None, offset=0):
        cursor = get_db().cursor()
        query = "SELECT id, nome, email, tipo, criado_em FROM usuarios ORDER BY id"
        params = []
        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        cursor.execute(query, params)
        return [user_public_dict(row) for row in cursor.fetchall()]

    def get_by_id(self, user_id):
        cursor = get_db().cursor()
        cursor.execute(
            "SELECT id, nome, email, tipo, criado_em FROM usuarios WHERE id = ?",
            (user_id,),
        )
        return user_public_dict(cursor.fetchone())

    def get_auth_row_by_email(self, email):
        cursor = get_db().cursor()
        cursor.execute(
            "SELECT id, nome, email, senha, tipo FROM usuarios WHERE email = ?",
            (email,),
        )
        return cursor.fetchone()

    def create(self, nome, email, senha, tipo="cliente"):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
        if cursor.fetchone() is not None:
            raise AppError("Email já cadastrado")
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, hash_password(senha), tipo),
        )
        db.commit()
        return cursor.lastrowid

    def update_password_hash(self, user_id, password_hash):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (password_hash, user_id))
        db.commit()
