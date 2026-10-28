"""AuthService — emite e valida tokens HMAC assinados.

Substitui o token previsível `fake-jwt-token-{id}` (FINDING-008), mantendo o
mesmo formato de resposta (`{"token": ...}`) e o mesmo fluxo de login, sem
introduzir um provedor de identidade externo.
"""
import base64
import hashlib
import hmac
import json
import time

from flask import current_app

from errors import AuthenticationError

DEFAULT_TTL_SECONDS = 60 * 60 * 8
MSG_INVALID_TOKEN = 'Token inválido ou expirado'


def _b64encode(raw):
    return base64.urlsafe_b64encode(raw).decode('utf-8').rstrip('=')


def _b64decode(text):
    padding = '=' * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


class AuthService:
    @staticmethod
    def _secret():
        secret = current_app.config['SECRET_KEY']
        return secret.encode('utf-8') if isinstance(secret, str) else secret

    @staticmethod
    def _sign(payload_b64):
        return hmac.new(AuthService._secret(), payload_b64.encode('utf-8'),
                        hashlib.sha256).hexdigest()

    @staticmethod
    def issue_token(user, ttl_seconds=DEFAULT_TTL_SECONDS):
        payload = {'sub': user.id, 'role': user.role, 'exp': int(time.time()) + ttl_seconds}
        payload_b64 = _b64encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
        return '{}.{}'.format(payload_b64, AuthService._sign(payload_b64))

    @staticmethod
    def decode_token(token):
        if not token or '.' not in token:
            raise AuthenticationError(MSG_INVALID_TOKEN)
        payload_b64, signature = token.rsplit('.', 1)
        if not hmac.compare_digest(AuthService._sign(payload_b64), signature):
            raise AuthenticationError(MSG_INVALID_TOKEN)
        try:
            payload = json.loads(_b64decode(payload_b64))
        except (ValueError, TypeError):
            raise AuthenticationError(MSG_INVALID_TOKEN)
        if payload.get('exp', 0) < int(time.time()):
            raise AuthenticationError(MSG_INVALID_TOKEN)
        return payload
