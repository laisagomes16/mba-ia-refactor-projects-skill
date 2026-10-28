from flask import current_app

from auth import create_token, hash_password, verify_password
from errors import AppError
from models.user import user_login_dict
from repositories.user_repository import UserRepository


class UserService:
    def __init__(self, repository=None):
        self.repository = repository or UserRepository()

    def listar(self, limit=None, offset=0):
        return self.repository.list_all(limit=limit, offset=offset)

    def obter(self, user_id):
        usuario = self.repository.get_by_id(user_id)
        if not usuario:
            raise AppError("Usuário não encontrado", 404)
        return usuario

    def criar(self, dados):
        if not dados:
            raise AppError("Dados inválidos")
        nome = dados.get("nome", "")
        email = dados.get("email", "")
        senha = dados.get("senha", "")
        if not nome or not email or not senha:
            raise AppError("Nome, email e senha são obrigatórios")
        return self.repository.create(nome, email, senha)

    def login(self, dados):
        if not dados:
            raise AppError("Dados inválidos")
        email = dados.get("email", "")
        senha = dados.get("senha", "")
        if not email or not senha:
            raise AppError("Email e senha são obrigatórios")

        row = self.repository.get_auth_row_by_email(email)
        if row is None or not verify_password(row["senha"], senha):
            raise AppError("Email ou senha inválidos", 401)

        stored = row["senha"] or ""
        if not (stored.startswith("pbkdf2:") or stored.startswith("scrypt:")):
            self.repository.update_password_hash(row["id"], hash_password(senha))

        payload = user_login_dict(row)
        payload_token = dict(payload)
        payload_token["token"] = create_token(current_app._get_current_object(), row["id"])
        return payload_token
