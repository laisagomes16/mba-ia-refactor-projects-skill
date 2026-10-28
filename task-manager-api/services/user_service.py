"""Regras de negócio de User (cadastro, login, atualização)."""
from errors import AuthenticationError, ConflictError, ForbiddenError, NotFoundError, ValidationError
from models.user import User
from repositories.user_repository import UserRepository
from services.auth_service import AuthService
from services.task_service import TaskService
from utils.helpers import MIN_PASSWORD_LENGTH, ROLE_USER, VALID_ROLES

MSG_USER_NOT_FOUND = 'Usuário não encontrado'
MSG_INVALID_DATA = 'Dados inválidos'
MSG_INVALID_EMAIL = 'Email inválido'
MSG_PASSWORD_TOO_SHORT = 'Senha deve ter no mínimo {} caracteres'.format(MIN_PASSWORD_LENGTH)
MSG_EMAIL_IN_USE = 'Email já cadastrado'
MSG_INVALID_CREDENTIALS = 'Credenciais inválidas'
MSG_INVALID_ROLE = 'Role inválido'
MSG_INACTIVE_USER = 'Usuário inativo'


class UserService:
    @staticmethod
    def get(user_id):
        user = UserRepository.get_by_id(user_id)
        if not user:
            raise NotFoundError(MSG_USER_NOT_FOUND)
        return user

    @staticmethod
    def list_all():
        return UserRepository.list_all()

    # ----- validação -----

    @staticmethod
    def _validate_name(name):
        if not name or not str(name).strip():
            raise ValidationError(MSG_INVALID_DATA)
        return str(name).strip()

    @staticmethod
    def _validate_email(email):
        if not User.is_valid_email(email):
            raise ValidationError(MSG_INVALID_EMAIL)
        return email

    @staticmethod
    def _validate_password(password):
        if not password or len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError(MSG_PASSWORD_TOO_SHORT)
        return password

    @staticmethod
    def _validate_role(role):
        if role not in VALID_ROLES:
            raise ValidationError(MSG_INVALID_ROLE)
        return role

    # ----- escrita -----

    @classmethod
    def create(cls, payload):
        name = cls._validate_name(payload.get('name'))
        email = cls._validate_email(payload.get('email'))
        password = cls._validate_password(payload.get('password'))
        role = cls._validate_role(payload.get('role', ROLE_USER))

        if UserRepository.get_by_email(email):
            raise ConflictError(MSG_EMAIL_IN_USE)

        user = User(name=name, email=email, role=role)
        user.set_password(password)
        return UserRepository.save(user)

    @classmethod
    def update(cls, user_id, payload):
        user = cls.get(user_id)
        if not payload:
            raise ValidationError(MSG_INVALID_DATA)

        if 'name' in payload:
            user.name = cls._validate_name(payload['name'])
        if 'email' in payload:
            new_email = cls._validate_email(payload['email'])
            existing = UserRepository.get_by_email(new_email)
            if existing and existing.id != user.id:
                raise ConflictError(MSG_EMAIL_IN_USE)
            user.email = new_email
        if payload.get('password'):
            user.set_password(cls._validate_password(payload['password']))
        if 'role' in payload:
            user.role = cls._validate_role(payload['role'])
        if 'active' in payload:
            user.active = bool(payload['active'])

        return UserRepository.save(user)

    @classmethod
    def delete(cls, user_id):
        user = cls.get(user_id)
        TaskService.delete_by_user(user.id)
        UserRepository.delete(user)
        return user

    # ----- autenticação -----

    @classmethod
    def login(cls, email, password):
        if not email or not password:
            raise ValidationError(MSG_INVALID_DATA)
        user = UserRepository.get_by_email(email)
        if not user or not user.check_password(password):
            raise AuthenticationError(MSG_INVALID_CREDENTIALS)
        if not user.is_active_user():
            raise ForbiddenError(MSG_INACTIVE_USER)
        # Persiste upgrade de hash MD5 → PBKDF2 quando aplicável.
        UserRepository.save(user)
        return user, AuthService.issue_token(user)
