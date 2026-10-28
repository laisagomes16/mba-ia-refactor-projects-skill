"""Model de User — hash seguro, verificação e migração transparente de MD5."""
import hashlib
import hmac
import re

from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from utils.helpers import EMAIL_PATTERN, ROLE_ADMIN, ROLE_USER, utcnow

_MD5_HEX = re.compile(r'^[a-f0-9]{32}$')


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=ROLE_USER)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def set_password(self, pwd):
        """PBKDF2 com salt (FINDING-004). Nunca mais MD5 sem salt."""
        self.password = generate_password_hash(pwd)

    def check_password(self, pwd):
        stored = self.password or ''
        if _MD5_HEX.match(stored):
            # Compatibilidade: contas legadas em MD5 ainda autenticam e são
            # atualizadas para o hash seguro no primeiro login bem-sucedido.
            legacy = hashlib.md5(pwd.encode()).hexdigest()
            if hmac.compare_digest(stored, legacy):
                self.set_password(pwd)
                return True
            return False
        return check_password_hash(stored, pwd)

    def is_admin(self):
        return self.role == ROLE_ADMIN

    def is_active_user(self):
        return bool(self.active)

    @staticmethod
    def is_valid_email(email):
        return isinstance(email, str) and re.match(EMAIL_PATTERN, email) is not None

